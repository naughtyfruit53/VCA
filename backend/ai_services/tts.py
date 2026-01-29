"""
Text-to-Speech (TTS) service using OpenAI TTS.

This module provides non-blocking audio synthesis for AI responses.
All operations are async and handle failures gracefully without crashing.

Usage:
    from backend.ai_services.tts import TTSService
    
    tts = TTSService()
    try:
        audio_bytes = await tts.synthesize_speech(
            text="Hello, how can I help you?",
            voice="alloy"
        )
    except TTSServiceError as e:
        logger.error(f"TTS failed: {e}")
        # Handle gracefully - maybe end call or retry
"""

import logging
from typing import Optional
import asyncio
from openai import AsyncOpenAI

from app.config.settings import settings


logger = logging.getLogger(__name__)


class TTSServiceError(Exception):
    """Raised when TTS service fails."""
    pass


class TTSService:
    """
    Text-to-Speech service for AI voice responses.
    
    Uses OpenAI TTS API with neutral voice for professional calls.
    All methods are non-blocking and safe for use in call threads.
    
    Configuration:
        OPENAI_API_KEY: OpenAI API key (required)
        TTS_MODEL: TTS model to use (default: tts-1)
        TTS_VOICE: Voice to use (default: alloy - neutral)
    
    Available Voices:
        - alloy: Neutral, professional (default)
        - echo: Male, clear
        - fable: British accent
        - onyx: Deep male
        - nova: Female, warm
        - shimmer: Female, energetic
    
    Error Handling:
        - Network errors: Retry with exponential backoff
        - API errors: Log and raise TTSServiceError
        - Empty text: Return empty audio (not an error)
        - All failures are logged but NEVER crash the call
    """
    
    def __init__(self):
        """Initialize TTS service with OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.tts_model
        self.voice = settings.tts_voice
        self.max_retries = 2
        self.retry_delay = 1.0  # seconds
        self.speed = 1.0  # Normal speaking speed
        
        logger.info(
            f"TTSService initialized with model: {self.model}, voice: {self.voice}"
        )
    
    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        timeout: float = 15.0
    ) -> bytes:
        """
        Synthesize text to speech using OpenAI TTS.
        
        This method is non-blocking and includes timeout protection.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default: from settings)
            speed: Speaking speed 0.25-4.0 (default: 1.0)
            timeout: Maximum time to wait for synthesis (seconds)
            
        Returns:
            bytes: Audio data in MP3 format
            
        Raises:
            TTSServiceError: If synthesis fails after retries
        
        Notes:
            - Handles empty text gracefully (returns empty bytes)
            - Retries on transient network failures
            - Times out after specified duration to prevent blocking
            - All errors are logged with context for debugging
            - Returns MP3 format for efficient streaming
        """
        # Validate input
        if not text or not text.strip():
            logger.warning("[TTS] Empty text provided, returning empty audio")
            return b""
        
        # Truncate very long text to prevent timeout
        max_chars = 500
        if len(text) > max_chars:
            logger.warning(
                f"[TTS] Text too long ({len(text)} chars), "
                f"truncating to {max_chars} chars"
            )
            text = text[:max_chars] + "..."
        
        logger.info(
            f"[TTS] Starting synthesis: "
            f"text_length={len(text)}, voice={voice or self.voice}"
        )
        
        # Try synthesis with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Call OpenAI TTS API with timeout
                response = await asyncio.wait_for(
                    self.client.audio.speech.create(
                        model=self.model,
                        voice=voice or self.voice,
                        input=text,
                        response_format="mp3",
                        speed=speed or self.speed
                    ),
                    timeout=timeout
                )
                
                # Read audio data
                audio_data = b""
                async for chunk in response.iter_bytes():
                    audio_data += chunk
                
                if not audio_data:
                    raise TTSServiceError("Empty audio data returned")
                
                # Success!
                logger.info(
                    f"[TTS] Synthesis successful: "
                    f"audio_size={len(audio_data)} bytes, attempts={attempt + 1}"
                )
                return audio_data
                
            except asyncio.TimeoutError:
                last_error = "Synthesis timeout"
                logger.warning(
                    f"[TTS] Synthesis timeout after {timeout}s "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    f"[TTS] Synthesis failed: {last_error} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"[TTS] Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        error_msg = f"TTS failed after {self.max_retries + 1} attempts: {last_error}"
        logger.error(f"[TTS] {error_msg}")
        raise TTSServiceError(error_msg)
    
    async def health_check(self) -> bool:
        """
        Check if TTS service is available.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            # Simple test with minimal text
            audio = await self.synthesize_speech(
                text="Test",
                timeout=5.0
            )
            return len(audio) > 0
        except Exception as e:
            logger.error(f"[TTS] Health check failed: {type(e).__name__}: {e}")
            return False


# TODO: Add support for SSML for better control (pauses, emphasis, etc.)
# TODO: Add audio format conversion if needed (MP3 -> WAV, etc.)
# TODO: Consider caching common phrases to reduce API calls
# TODO: Add support for voice cloning for branded experiences
# TODO: Investigate streaming TTS for lower time-to-first-audio
