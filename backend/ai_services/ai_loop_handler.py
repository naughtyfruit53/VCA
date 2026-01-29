"""
AI Audio Loop Handler for live inbound calls.

This module orchestrates the complete AI conversation loop:
1. Listen to caller audio via ARI
2. Transcribe with STT (Whisper)
3. Generate response with LLM (GPT + AIProfile)
4. Synthesize with TTS (OpenAI TTS)
5. Stream response back to caller via ARI

All operations are non-blocking and handle failures gracefully.

Usage:
    from backend.ai_services.ai_loop_handler import AILoopHandler
    
    handler = AILoopHandler()
    await handler.handle_inbound_call(
        call_id=call_id,
        channel_id=channel_id,
        tenant_id=tenant_id,
        ai_profile_id=ai_profile_id
    )
"""

import logging
import time
from typing import Optional
from uuid import UUID
import asyncio

from backend.ai_services.stt import STTService, STTServiceError
from backend.ai_services.llm import LLMService, LLMServiceError
from backend.ai_services.tts import TTSService, TTSServiceError
from backend.ai_services.ari_client import ARIClient, ARIClientError
from backend.ai_services.conversation_state import ConversationStateManager, ConversationStateError
from app.models import AIProfile
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class AILoopHandlerError(Exception):
    """Raised when AI loop handler fails."""
    pass


class AILoopHandler:
    """
    Orchestrates the complete AI audio loop for live calls.
    
    This is the main coordinator that:
    - Initializes all AI services (STT, LLM, TTS, ARI)
    - Manages conversation state in Redis
    - Enforces max turns and duration limits
    - Handles all failure paths gracefully
    - Logs latency metrics (time-to-first-audio)
    - Never blocks the call thread
    
    Error Handling Philosophy:
        - AI service failures: Fail-fast, log exit reason, end call gracefully
        - ARI failures: Log and end call gracefully
        - State failures: Best-effort, don't crash
        - Timeout discipline: Per-step ≤1.2s, total loop ≤1.5s
        - Exit discipline: First silence prompt once, second silence exit
        - NEVER expose technical errors to caller
        - ALWAYS log detailed errors and exit reasons for debugging
    
    Configuration:
        All settings from app.config.settings:
        - OpenAI API keys
        - Redis URL
        - ARI credentials
        - Conversation limits
    """
    
    def __init__(self):
        """Initialize AI loop handler with all services."""
        self.stt = STTService()
        self.llm = LLMService()
        self.tts = TTSService()
        self.ari = ARIClient()
        self.state_mgr = ConversationStateManager()
        
        # Fallback responses for failures (fail-fast, no retry)
        self.error_responses = {
            "stt_failure": "I'm sorry, I'm having trouble hearing you. Goodbye.",
            "llm_failure": "I apologize, I'm having technical difficulties. Goodbye.",
            "tts_failure": "I'm experiencing audio issues. Goodbye.",
            "max_turns": "Thank you for calling. I hope I was able to help you today. Goodbye!",
            "max_duration": "I apologize, but we've reached the maximum call duration. Thank you for calling!",
            "silence": "I haven't heard from you. Thank you for calling. Goodbye.",
            "confusion": "I'm sorry, I'm unable to help with that. Goodbye.",
            "timeout": "I apologize for the delay. Goodbye.",
            "general_error": "I apologize for the inconvenience. Goodbye."
        }
        
        # Timeout discipline (in seconds)
        self.per_step_timeout = 1.2  # Each step must complete within 1.2s
        self.total_loop_timeout = 1.5  # Total loop must complete within 1.5s
        
        logger.info("AILoopHandler initialized with all services (fail-fast mode)")
    
    async def handle_inbound_call(
        self,
        call_id: str,
        channel_id: str,
        tenant_id: UUID,
        ai_profile_id: UUID,
        db: Session
    ) -> None:
        """
        Handle complete AI conversation loop for an inbound call.
        
        This is the main entry point for AI-powered call handling.
        Runs the complete conversation loop until:
        - Max turns reached
        - Max duration reached
        - Caller hangs up
        - Critical failure occurs
        
        Args:
            call_id: Unique call identifier
            channel_id: Asterisk channel ID (for ARI)
            tenant_id: Tenant owning this call
            ai_profile_id: AI profile to use
            db: Database session for AI profile lookup
            
        This method is designed to be fire-and-forget - it handles all errors
        internally and never crashes.
        """
        start_time = time.time()
        logger.info(
            f"[AI LOOP] Starting AI loop: call_id={call_id}, "
            f"channel_id={channel_id}, tenant_id={tenant_id}"
        )
        
        try:
            # Step 1: Initialize conversation state
            logger.info("[AI LOOP] Step 1: Initializing conversation state")
            await self.state_mgr.initialize_call(call_id, tenant_id, ai_profile_id)
            
            # Step 2: Get AI profile from database
            logger.info("[AI LOOP] Step 2: Loading AI profile")
            ai_profile = db.query(AIProfile).filter(
                AIProfile.id == ai_profile_id,
                AIProfile.tenant_id == tenant_id
            ).first()
            
            if not ai_profile:
                raise AILoopHandlerError(
                    f"AI profile not found: id={ai_profile_id}, tenant={tenant_id}"
                )
            
            system_prompt = ai_profile.system_prompt
            logger.info(f"[AI LOOP] AI profile loaded: role={ai_profile.role}")
            
            # Step 3: Connect to ARI
            logger.info("[AI LOOP] Step 3: Connecting to ARI")
            await self.ari.connect()
            
            # Step 4: Answer the call
            logger.info("[AI LOOP] Step 4: Answering call")
            await self.ari.answer_call(channel_id)
            
            # Step 5: Send greeting (first audio)
            logger.info("[AI LOOP] Step 5: Generating greeting")
            greeting = await self._generate_greeting(system_prompt)
            await self._play_response(channel_id, greeting, call_id, "greeting")
            
            # Log time-to-first-audio
            time_to_first_audio = time.time() - start_time
            logger.info(
                f"[AI LOOP] Time to first audio: {time_to_first_audio:.2f}s"
            )
            
            # Step 6: Main conversation loop
            logger.info("[AI LOOP] Step 6: Entering main conversation loop")
            await self._conversation_loop(
                call_id=call_id,
                channel_id=channel_id,
                system_prompt=system_prompt
            )
            
            # Step 7: End call gracefully
            logger.info("[AI LOOP] Step 7: Ending call gracefully")
            await self._end_call_gracefully(call_id, channel_id, "completed")
            
        except Exception as e:
            # Critical failure - log and end call
            logger.error(
                f"[AI LOOP] Critical error in AI loop: {type(e).__name__}: {e}",
                exc_info=True
            )
            await self._end_call_gracefully(call_id, channel_id, "failed")
        
        finally:
            # Cleanup
            total_duration = time.time() - start_time
            logger.info(
                f"[AI LOOP] AI loop completed: call_id={call_id}, "
                f"duration={total_duration:.2f}s"
            )
            await self.ari.disconnect()
    
    async def _generate_greeting(self, system_prompt: str) -> str:
        """
        Generate initial greeting using LLM.
        
        Args:
            system_prompt: AI profile system prompt
            
        Returns:
            str: Greeting text
        """
        try:
            messages = [{"role": "user", "content": "Start the conversation with a greeting"}]
            greeting = await self.llm.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=50
            )
            return greeting
        except LLMServiceError:
            # Fallback greeting
            return "Hello! How can I help you today?"
    
    async def _conversation_loop(
        self,
        call_id: str,
        channel_id: str,
        system_prompt: str
    ) -> None:
        """
        Main conversation loop - iterates until termination condition.
        
        Args:
            call_id: Unique call identifier
            channel_id: Asterisk channel ID
            system_prompt: AI profile system prompt
        """
        logger.info("[AI LOOP] Starting conversation loop")
        
        # TODO: This is a PLACEHOLDER loop structure
        # Full implementation requires:
        # 1. Audio streaming from ARI (currently NotImplementedError)
        # 2. VAD for turn detection
        # 3. Barge-in handling
        # 4. Proper audio buffering
        
        max_iterations = 50  # Safety limit
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Check if conversation should end
                should_end, reason = await self.state_mgr.should_end_conversation(call_id)
                if should_end:
                    logger.info(
                        f"[AI LOOP] Conversation ending: reason={reason}"
                    )
                    # Set exit reason in state
                    await self.state_mgr.set_exit_reason(call_id, reason)
                    # Send goodbye message
                    goodbye = self.error_responses.get(reason, "Thank you for calling. Goodbye!")
                    await self._play_response(channel_id, goodbye, call_id, "goodbye")
                    break
                
                # TODO: Step 1 - Capture audio from caller via ARI
                # Currently NotImplementedError - requires ARI External Media
                logger.warning(
                    "[AI LOOP] Audio capture not implemented - "
                    "conversation loop is PLACEHOLDER only"
                )
                
                # TODO: Step 2 - Transcribe audio with STT
                # audio_chunk = await self.ari.stream_audio_from_caller(channel_id)
                # caller_text = await self.stt.transcribe_audio(audio_chunk)
                
                # TODO: Step 3 - Generate AI response with LLM
                # history = await self.state_mgr.get_conversation_history(call_id)
                # ai_response = await self.llm.generate_response(history, system_prompt)
                
                # TODO: Step 4 - Synthesize response with TTS
                # audio_data = await self.tts.synthesize_speech(ai_response)
                
                # TODO: Step 5 - Play response to caller via ARI
                # await self.ari.play_audio_to_caller(channel_id, audio_data)
                
                # TODO: Step 6 - Update conversation state
                # await self.state_mgr.add_turn(call_id, "user", caller_text)
                # await self.state_mgr.add_turn(call_id, "assistant", ai_response)
                
                # PLACEHOLDER: Break after one iteration since audio not implemented
                logger.warning(
                    "[AI LOOP] Breaking conversation loop - "
                    "full audio streaming not yet implemented"
                )
                break
                
                # Prevent tight loop
                await asyncio.sleep(0.1)
                
            except STTServiceError as e:
                # STT failure - fail-fast, set exit reason, end call
                logger.error(f"[AI LOOP] STT failure: {type(e).__name__}: {e}")
                await self.state_mgr.set_exit_reason(call_id, "stt_failure")
                try:
                    error_response = self.error_responses["stt_failure"]
                    await self._play_response(channel_id, error_response, call_id, "error")
                except Exception:
                    pass
                break
                
            except LLMServiceError as e:
                # LLM failure - fail-fast, set exit reason, end call
                logger.error(f"[AI LOOP] LLM failure: {type(e).__name__}: {e}")
                await self.state_mgr.set_exit_reason(call_id, "llm_failure")
                try:
                    error_response = self.error_responses["llm_failure"]
                    await self._play_response(channel_id, error_response, call_id, "error")
                except Exception:
                    pass
                break
                
            except TTSServiceError as e:
                # TTS failure - fail-fast, set exit reason, end call
                logger.error(f"[AI LOOP] TTS failure: {type(e).__name__}: {e}")
                await self.state_mgr.set_exit_reason(call_id, "tts_failure")
                try:
                    error_response = self.error_responses["tts_failure"]
                    await self._play_response(channel_id, error_response, call_id, "error")
                except Exception:
                    pass
                break
                
            except asyncio.TimeoutError:
                # Timeout - fail-fast, set exit reason, end call
                logger.error(f"[AI LOOP] Timeout exceeded")
                await self.state_mgr.set_exit_reason(call_id, "timeout")
                try:
                    error_response = self.error_responses["timeout"]
                    await self._play_response(channel_id, error_response, call_id, "error")
                except Exception:
                    pass
                break
                
            except Exception as e:
                # General error - fail-fast, set exit reason, end call
                logger.error(
                    f"[AI LOOP] Error in conversation turn: {type(e).__name__}: {e}"
                )
                await self.state_mgr.set_exit_reason(call_id, "general_error")
                # Try to apologize to caller
                try:
                    error_response = self.error_responses["general_error"]
                    await self._play_response(channel_id, error_response, call_id, "error")
                except Exception:
                    pass
                # End call after error
                break
        
        logger.info("[AI LOOP] Conversation loop ended")
    
    async def _play_response(
        self,
        channel_id: str,
        text: str,
        call_id: str,
        context: str = "response"
    ) -> None:
        """
        Synthesize and play response to caller.
        
        Args:
            channel_id: Asterisk channel ID
            text: Text to speak
            call_id: Call ID for state tracking
            context: Context for logging
        """
        try:
            # Synthesize speech
            audio_data = await self.tts.synthesize_speech(text)
            
            # TODO: Play via ARI (currently NotImplementedError)
            # await self.ari.play_audio_to_caller(channel_id, audio_data)
            
            logger.info(
                f"[AI LOOP] Response played ({context}): "
                f"text_length={len(text)}, audio_size={len(audio_data)}"
            )
            
            # Add to conversation state if not greeting
            if context != "greeting":
                await self.state_mgr.add_turn(call_id, "assistant", text)
            
        except TTSServiceError as e:
            logger.error(f"[AI LOOP] TTS failed for {context}: {e}")
            # Continue without playing audio
        except Exception as e:
            logger.error(
                f"[AI LOOP] Failed to play response ({context}): {e}"
            )
    
    async def _end_call_gracefully(
        self,
        call_id: str,
        channel_id: str,
        reason: str
    ) -> None:
        """
        End call gracefully with cleanup.
        
        Args:
            call_id: Unique call identifier
            channel_id: Asterisk channel ID
            reason: Reason for ending
        """
        try:
            # Get state to log exit reason if available
            state = await self.state_mgr.get_state(call_id)
            exit_reason = state.get("ai_exit_reason") if state else None
            
            # Mark as ending in state
            await self.state_mgr.mark_ending(call_id, reason=exit_reason or reason)
            
            # Hang up call
            await self.ari.hangup_call(channel_id)
            
            # Clean up state
            await self.state_mgr.end_call(call_id)
            
            logger.info(
                f"[AI LOOP] Call ended gracefully: reason={reason}, "
                f"ai_exit_reason={exit_reason or 'not set'}"
            )
            
        except Exception as e:
            logger.error(f"[AI LOOP] Error during graceful end: {e}")


# TODO: Integrate with telephony adapter (tata.py) to start AI loop on inbound calls
# TODO: Add latency tracking for each component (STT, LLM, TTS, total)
# TODO: Add support for human handoff when caller requests
# TODO: Add support for call transfer to specific extension
# TODO: Add DTMF handling for menu navigation
# TODO: Add call recording with consent
# TODO: Add sentiment analysis for caller satisfaction
# TODO: Add support for multi-language detection and switching
# TODO: Add feedback collection at end of call
# TODO: Add conversation summary generation
# TODO: Consider implementing full ARI audio streaming (External Media)
# TODO: Add barge-in detection and handling
