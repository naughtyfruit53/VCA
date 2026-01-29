"""
Conversation state management using Redis.

This module manages ephemeral per-call conversation state including:
- Conversation history (messages)
- Turn count (for max turns enforcement)
- Start time (for max duration enforcement)
- Current state (active, ending, ended)

Usage:
    from backend.ai_services.conversation_state import ConversationStateManager
    
    state_mgr = ConversationStateManager()
    await state_mgr.initialize_call(call_id, tenant_id, ai_profile_id)
    
    # During conversation
    await state_mgr.add_turn(call_id, "user", "Hello")
    history = await state_mgr.get_conversation_history(call_id)
    
    # Check limits
    should_end = await state_mgr.should_end_conversation(call_id)
    
    # Cleanup
    await state_mgr.end_call(call_id)
"""

import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from uuid import UUID
import time

from app.config.redis import get_redis_client
from app.config.settings import settings


logger = logging.getLogger(__name__)


class ConversationStateError(Exception):
    """Raised when conversation state operation fails."""
    pass


class ConversationStateManager:
    """
    Manages conversation state in Redis for live calls.
    
    Each call has its own state keyed by call_id, containing:
    - Conversation history (list of messages)
    - Turn count
    - Start timestamp
    - State (active/ending/ended)
    - Tenant and AI profile associations
    
    Configuration:
        REDIS_URL: Redis connection string (required)
        MAX_CONVERSATION_TURNS: Maximum turns before ending (default: 20)
        MAX_CONVERSATION_DURATION_SECONDS: Maximum call duration (default: 300)
    
    Key Management:
        All keys expire after 1 hour to prevent memory leaks.
        Keys are automatically cleaned up on call end.
    
    Error Handling:
        - Redis errors: Log and raise ConversationStateError
        - Missing state: Initialize new state (idempotent)
        - All operations are atomic where possible
    """
    
    def __init__(self):
        """Initialize conversation state manager."""
        self.max_turns = settings.max_conversation_turns
        self.max_duration = settings.max_conversation_duration_seconds
        self.state_ttl = 3600  # 1 hour TTL for all keys
        
        logger.info(
            f"ConversationStateManager initialized: "
            f"max_turns={self.max_turns}, max_duration={self.max_duration}s"
        )
    
    def _call_key(self, call_id: str) -> str:
        """Get Redis key for call state."""
        return f"call:{call_id}:state"
    
    async def initialize_call(
        self,
        call_id: str,
        tenant_id: UUID,
        ai_profile_id: UUID
    ) -> None:
        """
        Initialize conversation state for a new call.
        
        Args:
            call_id: Unique call identifier
            tenant_id: Tenant owning this call
            ai_profile_id: AI profile to use for this call
            
        Raises:
            ConversationStateError: If initialization fails
        """
        try:
            redis = await get_redis_client()
            
            # Create initial state
            state = {
                "call_id": call_id,
                "tenant_id": str(tenant_id),
                "ai_profile_id": str(ai_profile_id),
                "started_at": time.time(),
                "turn_count": 0,
                "conversation_history": [],
                "state": "active",
                "silence_count": 0,  # Track consecutive silences
                "ai_exit_reason": None,  # Track exit reason: silence, confusion, max_turns, max_duration, stt_failure, llm_failure, tts_failure, timeout
                "metadata": {}
            }
            
            # Store in Redis with TTL
            key = self._call_key(call_id)
            await redis.setex(
                key,
                self.state_ttl,
                json.dumps(state)
            )
            
            logger.info(
                f"[STATE] Call initialized: call_id={call_id}, "
                f"tenant_id={tenant_id}, ai_profile_id={ai_profile_id}"
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize call state: {type(e).__name__}: {e}"
            logger.error(f"[STATE] {error_msg}")
            raise ConversationStateError(error_msg)
    
    async def get_state(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current conversation state for a call.
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            dict: Call state or None if not found
            
        Raises:
            ConversationStateError: If retrieval fails
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            state_json = await redis.get(key)
            if not state_json:
                logger.warning(f"[STATE] No state found for call_id={call_id}")
                return None
            
            state = json.loads(state_json)
            return state
            
        except Exception as e:
            error_msg = f"Failed to get call state: {type(e).__name__}: {e}"
            logger.error(f"[STATE] {error_msg}")
            raise ConversationStateError(error_msg)
    
    async def add_turn(
        self,
        call_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add a turn to the conversation history.
        
        Args:
            call_id: Unique call identifier
            role: Message role ("user" or "assistant")
            content: Message content (transcribed text or AI response)
            
        Raises:
            ConversationStateError: If update fails
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            # Get current state
            state = await self.get_state(call_id)
            if not state:
                raise ConversationStateError(f"No state found for call_id={call_id}")
            
            # Add message to history
            message = {
                "role": role,
                "content": content,
                "timestamp": time.time()
            }
            state["conversation_history"].append(message)
            
            # Increment turn count (only for user messages)
            if role == "user":
                state["turn_count"] += 1
            
            # Update Redis with extended TTL
            await redis.setex(
                key,
                self.state_ttl,
                json.dumps(state)
            )
            
            logger.info(
                f"[STATE] Turn added: call_id={call_id}, role={role}, "
                f"turn_count={state['turn_count']}"
            )
            
        except Exception as e:
            error_msg = f"Failed to add turn: {type(e).__name__}: {e}"
            logger.error(f"[STATE] {error_msg}")
            raise ConversationStateError(error_msg)
    
    async def get_conversation_history(self, call_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for LLM context.
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            list: Conversation history in LLM format [{"role": "...", "content": "..."}]
            
        Raises:
            ConversationStateError: If retrieval fails
        """
        state = await self.get_state(call_id)
        if not state:
            return []
        
        # Convert to LLM format (exclude timestamps)
        history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in state.get("conversation_history", [])
        ]
        
        return history
    
    async def should_end_conversation(self, call_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if conversation should end based on limits.
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            tuple: (should_end: bool, reason: Optional[str])
            
        Raises:
            ConversationStateError: If check fails
        """
        state = await self.get_state(call_id)
        if not state:
            return (True, "no_state")
        
        # Check if already ending/ended
        if state.get("state") in ["ending", "ended"]:
            return (True, "already_ending")
        
        # Check turn limit
        turn_count = state.get("turn_count", 0)
        if turn_count >= self.max_turns:
            logger.info(
                f"[STATE] Max turns reached: call_id={call_id}, "
                f"turns={turn_count}/{self.max_turns}"
            )
            return (True, "max_turns")
        
        # Check duration limit
        started_at = state.get("started_at", 0)
        elapsed = time.time() - started_at
        if elapsed >= self.max_duration:
            logger.info(
                f"[STATE] Max duration reached: call_id={call_id}, "
                f"duration={elapsed:.0f}s/{self.max_duration}s"
            )
            return (True, "max_duration")
        
        return (False, None)
    
    async def increment_silence_count(self, call_id: str) -> int:
        """
        Increment silence count for exit discipline.
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            int: New silence count
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            state = await self.get_state(call_id)
            if state:
                state["silence_count"] = state.get("silence_count", 0) + 1
                await redis.setex(key, self.state_ttl, json.dumps(state))
                logger.info(
                    f"[STATE] Silence count incremented: call_id={call_id}, "
                    f"count={state['silence_count']}"
                )
                return state["silence_count"]
            return 0
        except Exception as e:
            logger.error(f"[STATE] Failed to increment silence: {type(e).__name__}: {e}")
            return 0
    
    async def reset_silence_count(self, call_id: str) -> None:
        """
        Reset silence count when user speaks.
        
        Args:
            call_id: Unique call identifier
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            state = await self.get_state(call_id)
            if state:
                state["silence_count"] = 0
                await redis.setex(key, self.state_ttl, json.dumps(state))
        except Exception as e:
            logger.error(f"[STATE] Failed to reset silence: {type(e).__name__}: {e}")
    
    async def set_exit_reason(self, call_id: str, reason: str) -> None:
        """
        Set the ai_exit_reason for this call.
        
        Args:
            call_id: Unique call identifier
            reason: Exit reason (silence, confusion, max_turns, max_duration, 
                   stt_failure, llm_failure, tts_failure, timeout)
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            state = await self.get_state(call_id)
            if state:
                state["ai_exit_reason"] = reason
                await redis.setex(key, self.state_ttl, json.dumps(state))
                logger.info(
                    f"[STATE] Exit reason set: call_id={call_id}, reason={reason}"
                )
        except Exception as e:
            logger.error(f"[STATE] Failed to set exit reason: {type(e).__name__}: {e}")
    
    async def mark_ending(self, call_id: str, reason: Optional[str] = None) -> None:
        """
        Mark conversation as ending (graceful shutdown).
        
        Args:
            call_id: Unique call identifier
            reason: Optional exit reason to set
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            state = await self.get_state(call_id)
            if state:
                state["state"] = "ending"
                if reason:
                    state["ai_exit_reason"] = reason
                await redis.setex(key, self.state_ttl, json.dumps(state))
                logger.info(
                    f"[STATE] Call marked as ending: call_id={call_id}, "
                    f"reason={reason or 'not specified'}"
                )
        except Exception as e:
            logger.error(f"[STATE] Failed to mark ending: {type(e).__name__}: {e}")
    
    async def end_call(self, call_id: str) -> None:
        """
        End call and clean up state.
        
        Args:
            call_id: Unique call identifier
        """
        try:
            redis = await get_redis_client()
            key = self._call_key(call_id)
            
            # Delete state (cleanup)
            await redis.delete(key)
            logger.info(f"[STATE] Call state deleted: call_id={call_id}")
            
        except Exception as e:
            logger.error(f"[STATE] Failed to end call: {type(e).__name__}: {e}")


# TODO: Add support for metadata updates (e.g., caller intent, sentiment)
# TODO: Add conversation context trimming for long calls (keep recent messages)
# TODO: Add support for call transfer state (when human handoff is needed)
# TODO: Add metrics tracking (latencies, error rates per call)
# TODO: Consider persisting final conversation to database for analytics
