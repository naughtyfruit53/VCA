"""
Large Language Model (LLM) service using OpenAI GPT.

This module provides non-blocking AI conversation for live calls.
Uses tenant-specific AIProfile for system prompts and behavior.

Usage:
    from backend.ai_services.llm import LLMService
    
    llm = LLMService()
    try:
        response = await llm.generate_response(
            messages=conversation_history,
            system_prompt=ai_profile.system_prompt
        )
    except LLMServiceError as e:
        logger.error(f"LLM failed: {e}")
        # Handle gracefully - maybe apologize to caller
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
from openai import AsyncOpenAI

from app.config.settings import settings


logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when LLM service fails."""
    pass


class LLMService:
    """
    Large Language Model service for AI conversation.
    
    Uses OpenAI GPT API with tenant-specific system prompts from AIProfile.
    All methods are non-blocking and safe for use in call threads.
    
    Configuration:
        OPENAI_API_KEY: OpenAI API key (required)
        LLM_MODEL: GPT model to use (default: gpt-4)
    
    Error Handling:
        - Network errors: Fail-fast (no retries for live voice)
        - API errors: Log and raise LLMServiceError
        - Empty input: Return fallback response
        - All failures are logged and raise exception for caller to handle
    """
    
    def __init__(self):
        """Initialize LLM service with OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        # LIVE VOICE: No retries - single-attempt fail-fast for production voice calls
        self.max_retries = 0
        self.retry_delay = 0  # No delays
        self.max_tokens = 150  # Keep responses concise for phone calls
        self.temperature = 0.7  # Balanced creativity
        
        logger.info(f"LLMService initialized with model: {self.model} (fail-fast mode)")
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        timeout: float = 15.0,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate AI response using GPT.
        
        This method is non-blocking and includes timeout protection.
        
        Args:
            messages: Conversation history [{"role": "user/assistant", "content": "..."}]
            system_prompt: System prompt from AIProfile (defines AI behavior)
            timeout: Maximum time to wait for response (seconds)
            max_tokens: Override default max tokens for response
            
        Returns:
            str: AI-generated response text
            
        Raises:
            LLMServiceError: If generation fails after retries
        
        Notes:
            - System prompt is tenant-specific from AIProfile
            - Keeps responses concise for phone conversations
            - Single-attempt fail-fast (no retries for live voice calls)
            - Times out after specified duration to prevent blocking
            - All errors are logged with context for debugging
        """
        # Validate input
        if not system_prompt or not system_prompt.strip():
            raise LLMServiceError("System prompt is required")
        
        if not messages:
            logger.warning("[LLM] Empty conversation history, using default greeting")
            messages = []
        
        logger.info(
            f"[LLM] Generating response: "
            f"messages={len(messages)}, system_prompt_len={len(system_prompt)}"
        )
        
        # Build full message list with system prompt
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        # Try generation with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Call OpenAI GPT API with timeout
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=full_messages,
                        max_tokens=max_tokens or self.max_tokens,
                        temperature=self.temperature,
                        n=1,
                        stop=None
                    ),
                    timeout=timeout
                )
                
                # Extract response text
                if not response.choices or len(response.choices) == 0:
                    raise LLMServiceError("No response choices returned")
                
                text = response.choices[0].message.content.strip()
                
                if not text:
                    raise LLMServiceError("Empty response content")
                
                # Success!
                logger.info(
                    f"[LLM] Response generated: "
                    f"text_length={len(text)}, attempts={attempt + 1}"
                )
                return text
                
            except asyncio.TimeoutError:
                last_error = "Response generation timeout"
                logger.warning(
                    f"[LLM] Generation timeout after {timeout}s "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    f"[LLM] Generation failed: {last_error} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"[LLM] Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        error_msg = f"LLM failed after {self.max_retries + 1} attempts: {last_error}"
        logger.error(f"[LLM] {error_msg}")
        raise LLMServiceError(error_msg)
    
    def create_fallback_response(self, context: str = "general") -> str:
        """
        Create a fallback response when LLM fails.
        
        Args:
            context: Context for the fallback (e.g., "greeting", "error", "goodbye")
            
        Returns:
            str: Polite fallback message
        """
        fallbacks = {
            "greeting": "Hello! How can I help you today?",
            "error": "I'm sorry, I'm having trouble understanding. Could you please repeat that?",
            "goodbye": "Thank you for calling. Have a great day!",
            "general": "I apologize, I'm having a slight technical difficulty. Could you please hold for a moment?"
        }
        
        return fallbacks.get(context, fallbacks["general"])
    
    async def health_check(self) -> bool:
        """
        Check if LLM service is available.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            # Simple test with minimal prompt
            test_messages = [{"role": "user", "content": "Hi"}]
            response = await self.generate_response(
                messages=test_messages,
                system_prompt="You are a helpful assistant. Respond briefly.",
                timeout=5.0,
                max_tokens=10
            )
            return bool(response)
        except Exception as e:
            logger.error(f"[LLM] Health check failed: {type(e).__name__}: {e}")
            return False


# TODO: Add conversation history management (trim old messages to save tokens)
# TODO: Add support for function calling for structured actions (transfer, schedule, etc.)
# TODO: Add conversation context compression for long calls
# TODO: Add sentiment analysis for caller satisfaction
# TODO: Consider streaming responses for lower latency
