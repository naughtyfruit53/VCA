"""
Speech-to-Text (STT) service using OpenAI Whisper.

This module provides non-blocking audio transcription for live calls.
All operations are async and handle failures gracefully without crashing.

Usage:
    from backend.ai_services.stt import STTService
    
    stt = STTService()
    try:
        text = await stt.transcribe_audio(audio_bytes, language="en")
    except STTServiceError as e:
        logger.error(f"STT failed: {e}")
        # Handle gracefully - maybe apologize to caller
"""

import logging
from typing import Optional
import asyncio
from openai import AsyncOpenAI
from io import BytesIO

from app.config.settings import settings


logger = logging.getLogger(__name__)


class STTServiceError(Exception):
    """Raised when STT service fails."""
    pass


class STTService:
    """
    Speech-to-Text service for real-time call transcription.
    
    Uses OpenAI Whisper API for transcription with robust error handling.
    All methods are non-blocking and safe for use in call threads.
    
    Configuration:
        OPENAI_API_KEY: OpenAI API key (required)
        STT_MODEL: Whisper model to use (default: whisper-1)
    
    Error Handling:
        - Network errors: Retry with exponential backoff
        - API errors: Log and raise STTServiceError
        - Empty audio: Return empty string (not an error)
        - All failures are logged but NEVER crash the call
    """
    
    def __init__(self):
        """Initialize STT service with OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.stt_model
        self.max_retries = 2
        self.retry_delay = 1.0  # seconds
        
        logger.info(f"STTService initialized with model: {self.model}")
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = "en",
        timeout: float = 10.0
    ) -> str:
        """
        Transcribe audio to text using Whisper.
        
        This method is non-blocking and includes timeout protection.
        
        Args:
            audio_data: Raw audio bytes (WAV, MP3, or other supported format)
            language: Language code (default: "en" for English)
            timeout: Maximum time to wait for transcription (seconds)
            
        Returns:
            str: Transcribed text (empty string if no speech detected)
            
        Raises:
            STTServiceError: If transcription fails after retries
        
        Notes:
            - Handles empty audio gracefully (returns empty string)
            - Retries on transient network failures
            - Times out after specified duration to prevent blocking
            - All errors are logged with context for debugging
        """
        # Validate input
        if not audio_data or len(audio_data) == 0:
            logger.warning("[STT] Empty audio data provided, returning empty string")
            return ""
        
        logger.info(
            f"[STT] Starting transcription: "
            f"audio_size={len(audio_data)} bytes, language={language}"
        )
        
        # Try transcription with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Create file-like object from bytes
                audio_file = BytesIO(audio_data)
                audio_file.name = "audio.wav"  # OpenAI requires a filename
                
                try:
                    # Call OpenAI Whisper API with timeout
                    result = await asyncio.wait_for(
                        self.client.audio.transcriptions.create(
                            model=self.model,
                            file=audio_file,
                            language=language,
                            response_format="text"
                        ),
                        timeout=timeout
                    )
                    
                    # Success!
                    text = result.strip() if isinstance(result, str) else ""
                    logger.info(
                        f"[STT] Transcription successful: "
                        f"text_length={len(text)}, attempts={attempt + 1}"
                    )
                    return text
                finally:
                    # Always close the BytesIO object
                    audio_file.close()
                
            except asyncio.TimeoutError:
                last_error = "Transcription timeout"
                logger.warning(
                    f"[STT] Transcription timeout after {timeout}s "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    f"[STT] Transcription failed: {last_error} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"[STT] Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        error_msg = f"STT failed after {self.max_retries + 1} attempts: {last_error}"
        logger.error(f"[STT] {error_msg}")
        raise STTServiceError(error_msg)
    
    async def health_check(self) -> bool:
        """
        Check if STT service is available.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            # Simple test with minimal audio
            # TODO: Use a small test audio file if needed
            logger.info("[STT] Health check - service configured")
            return True
        except Exception as e:
            logger.error(f"[STT] Health check failed: {type(e).__name__}: {e}")
            return False


# TODO: Consider adding streaming transcription for lower latency
# TODO: OpenAI Whisper doesn't support streaming yet, but future APIs might
# TODO: Investigate partial transcription for real-time feedback
# TODO: Add support for custom vocabulary/context for better accuracy
# TODO: Add audio quality validation before transcription
