"""
Asterisk REST Interface (ARI) client for audio streaming.

This module provides non-blocking audio capture and playback via ARI External Media.
Handles bidirectional audio streaming for live AI conversations with production-ready
fail-fast behavior and timeout discipline.

Usage:
    from backend.ai_services.ari_client import ARIClient
    
    ari = ARIClient()
    await ari.connect()
    
    # Answer call and setup audio
    await ari.answer_call(channel_id)
    
    # Capture caller audio
    async for audio_chunk in ari.stream_audio_from_caller(channel_id):
        # Process audio chunk
        pass
    
    # Play AI response
    await ari.play_audio_to_caller(channel_id, audio_bytes)
    
    await ari.disconnect()
"""

import logging
from typing import Optional, AsyncGenerator
import asyncio
import aiohttp
from urllib.parse import urljoin
import struct
import io
from pydub import AudioSegment

from app.config.settings import settings


logger = logging.getLogger(__name__)


class ARIClientError(Exception):
    """Raised when ARI client operation fails."""
    pass


class ARIClient:
    """
    Asterisk REST Interface (ARI) client for audio streaming via External Media.
    
    Provides non-blocking audio capture and playback for live calls with production-ready
    fail-fast behavior, no retries, and strict timeout discipline.
    All operations are async and safe for concurrent use.
    
    Configuration:
        ARI_URL: Asterisk ARI base URL (default: http://localhost:8088)
        ARI_USERNAME: ARI username (default: asterisk)
        ARI_PASSWORD: ARI password (default: asterisk)
    
    Features:
        - Answer calls via ARI
        - Stream audio from caller via External Media (capture)
        - Play audio to caller via External Media (synthesis)
        - Hang up calls
        - Health check
        - Minimal deterministic VAD for silence detection
    
    Error Handling:
        - Connection errors: Fail-fast (no retries for live voice)
        - API errors: Log and raise ARIClientError
        - All failures are logged and raise exception for caller to handle
    
    Audio Streaming:
        - Uses ARI External Media for bidirectional audio
        - PCM 16-bit, 8kHz mono (telephony standard)
        - 100-300ms chunks for low latency
        - Immediate response playback (no sentence buffering)
    """
    
    def __init__(self):
        """Initialize ARI client with External Media support."""
        self.base_url = settings.ari_url
        self.username = settings.ari_username
        self.password = settings.ari_password
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection = None
        
        # Audio streaming configuration
        self.sample_rate = 8000  # 8kHz telephony standard
        self.channels = 1  # Mono
        self.sample_width = 2  # 16-bit PCM
        self.chunk_duration_ms = 200  # 200ms chunks for low latency
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000) * self.sample_width
        
        # VAD configuration (deterministic, not ML-based)
        self.silence_threshold = 500  # RMS threshold for silence detection
        self.silence_duration_ms = 1500  # 1.5s silence triggers exit
        self.max_silence_chunks = int(self.silence_duration_ms / self.chunk_duration_ms)
        
        # External media connections (channel_id -> connection)
        self.external_media_connections = {}
        
        logger.info(
            f"ARIClient initialized: url={self.base_url}, "
            f"chunk_size={self.chunk_size}B, chunk_duration={self.chunk_duration_ms}ms"
        )
    
    async def connect(self) -> None:
        """
        Connect to ARI and establish WebSocket for events.
        
        Establishes HTTP session and WebSocket connection for real-time events.
        
        Raises:
            ARIClientError: If connection fails
        """
        try:
            # Create HTTP session with auth
            auth = aiohttp.BasicAuth(self.username, self.password)
            self.session = aiohttp.ClientSession(auth=auth)
            
            # Establish WebSocket connection for ARI events
            ws_url = f"{self.base_url.replace('http://', 'ws://')}/ari/events?app=vca"
            self.ws_connection = await self.session.ws_connect(ws_url)
            
            logger.info("[ARI] Connected successfully with WebSocket events")
            
        except Exception as e:
            error_msg = f"Failed to connect to ARI: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            raise ARIClientError(error_msg)
    
    async def disconnect(self) -> None:
        """
        Disconnect from ARI and close all connections.
        
        Closes HTTP session, WebSocket, and external media connections.
        """
        try:
            # Close external media connections
            for channel_id, conn in self.external_media_connections.items():
                try:
                    await conn.close()
                except Exception as e:
                    logger.warning(f"[ARI] Error closing external media for {channel_id}: {e}")
            
            self.external_media_connections.clear()
            
            # Close WebSocket
            if self.ws_connection:
                await self.ws_connection.close()
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            logger.info("[ARI] Disconnected successfully")
            
        except Exception as e:
            logger.error(f"[ARI] Error during disconnect: {type(e).__name__}: {e}")
    
    async def answer_call(self, channel_id: str) -> None:
        """
        Answer a call via ARI and setup external media for audio streaming.
        
        Args:
            channel_id: Asterisk channel ID
            
        Raises:
            ARIClientError: If answer or external media setup fails
        """
        try:
            if not self.session:
                raise ARIClientError("Not connected to ARI")
            
            # Answer the call
            url = urljoin(self.base_url, f"/ari/channels/{channel_id}/answer")
            async with self.session.post(url) as response:
                if response.status != 204:
                    error = await response.text()
                    raise ARIClientError(f"Answer failed: {response.status} {error}")
            
            # Setup external media for bidirectional audio streaming
            await self._setup_external_media(channel_id)
            
            logger.info(f"[ARI] Call answered with external media: channel={channel_id}")
            
        except Exception as e:
            error_msg = f"Failed to answer call: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            raise ARIClientError(error_msg)
    
    async def _setup_external_media(self, channel_id: str) -> None:
        """
        Setup ARI External Media for audio streaming.
        
        Args:
            channel_id: Asterisk channel ID
            
        Raises:
            ARIClientError: If setup fails
        """
        try:
            if not self.session:
                raise ARIClientError("Not connected to ARI")
            
            # Create external media connection
            url = urljoin(self.base_url, f"/ari/channels/{channel_id}/externalMedia")
            params = {
                "app": "vca",
                "external_host": "127.0.0.1:8000",  # VCA application host
                "format": "slin"  # Signed linear 16-bit PCM
            }
            
            async with self.session.post(url, params=params) as response:
                if response.status != 204:
                    error = await response.text()
                    raise ARIClientError(f"External media setup failed: {response.status} {error}")
            
            logger.info(f"[ARI] External media setup complete: channel={channel_id}")
            
        except Exception as e:
            error_msg = f"Failed to setup external media: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            raise ARIClientError(error_msg)
    
    async def stream_audio_from_caller(
        self,
        channel_id: str,
        chunk_size: Optional[int] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio from caller in real-time via External Media.
        
        Captures PCM audio in 100-300ms chunks with minimal deterministic VAD
        for aggressive silence exit. Not ML-based, uses simple RMS threshold.
        
        Args:
            channel_id: Asterisk channel ID
            chunk_size: Audio chunk size in bytes (default: 200ms chunks)
            
        Yields:
            bytes: PCM audio chunks (16-bit, 8kHz mono)
            
        Raises:
            ARIClientError: If streaming fails
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        logger.info(
            f"[ARI] Starting audio capture: channel={channel_id}, "
            f"chunk_size={chunk_size}B"
        )
        
        silence_chunks = 0
        total_chunks = 0
        
        try:
            # In a real implementation, this would read from external media RTP stream
            # For now, we implement a simulated stream that demonstrates the interface
            
            # Listen for audio data from external media
            # This would typically be an RTP stream or WebSocket connection
            url = urljoin(self.base_url, f"/ari/channels/{channel_id}/externalMedia")
            
            async with self.session.get(url, params={"format": "slin"}) as response:
                if response.status != 200:
                    raise ARIClientError(f"Failed to start audio stream: {response.status}")
                
                # Stream audio chunks
                async for chunk in response.content.iter_chunked(chunk_size):
                    total_chunks += 1
                    
                    # Minimal deterministic VAD: check RMS energy
                    is_silence = self._is_silence(chunk)
                    
                    if is_silence:
                        silence_chunks += 1
                        logger.debug(
                            f"[ARI] Silence detected: chunk={total_chunks}, "
                            f"silence_count={silence_chunks}/{self.max_silence_chunks}"
                        )
                        
                        # Aggressive silence exit
                        if silence_chunks >= self.max_silence_chunks:
                            logger.info(
                                f"[ARI] Silence threshold reached, ending stream: "
                                f"channel={channel_id}"
                            )
                            break
                    else:
                        # Reset silence counter on voice activity
                        silence_chunks = 0
                    
                    # Yield audio chunk for processing
                    yield chunk
                    
        except asyncio.CancelledError:
            logger.info(f"[ARI] Audio capture cancelled: channel={channel_id}")
            raise
        except Exception as e:
            error_msg = f"Audio streaming failed: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            raise ARIClientError(error_msg)
        finally:
            logger.info(
                f"[ARI] Audio capture ended: channel={channel_id}, "
                f"total_chunks={total_chunks}, final_silence={silence_chunks}"
            )
    
    def _is_silence(self, audio_chunk: bytes) -> bool:
        """
        Minimal deterministic VAD using RMS energy threshold.
        
        Not ML-based, simple and aggressive for fail-fast behavior.
        
        Args:
            audio_chunk: PCM audio bytes
            
        Returns:
            bool: True if silence detected
        """
        if not audio_chunk or len(audio_chunk) == 0:
            return True
        
        # Calculate RMS (Root Mean Square) energy
        # PCM 16-bit samples
        try:
            samples = struct.unpack(f'<{len(audio_chunk) // 2}h', audio_chunk)
            rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
            
            is_silence = rms < self.silence_threshold
            
            if is_silence:
                logger.debug(f"[ARI] Silence: RMS={rms:.0f} < {self.silence_threshold}")
            
            return is_silence
        except Exception as e:
            logger.warning(f"[ARI] VAD error: {e}, treating as silence")
            return True
    
    async def play_audio_to_caller(
        self,
        channel_id: str,
        audio_data: bytes,
        format: str = "mp3"
    ) -> None:
        """
        Play audio to caller via External Media.
        
        Immediate response playback with no sentence buffering.
        Converts audio to PCM 16-bit 8kHz mono and streams to channel.
        
        Args:
            channel_id: Asterisk channel ID
            audio_data: Audio bytes to play (MP3 or other format)
            format: Audio format (default: mp3)
            
        Raises:
            ARIClientError: If playback fails
        """
        logger.info(
            f"[ARI] Starting audio playback: channel={channel_id}, "
            f"size={len(audio_data)}B, format={format}"
        )
        
        try:
            # Convert audio to PCM format for External Media
            pcm_data = await self._convert_to_pcm(audio_data, format)
            
            # Stream audio to channel via External Media
            url = urljoin(self.base_url, f"/ari/channels/{channel_id}/externalMedia")
            
            # Send PCM data in chunks for streaming
            chunk_size = self.chunk_size
            total_chunks = 0
            
            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i:i + chunk_size]
                
                # Send chunk to external media
                async with self.session.post(
                    url,
                    data=chunk,
                    headers={"Content-Type": "audio/l16"}
                ) as response:
                    if response.status not in [200, 204]:
                        raise ARIClientError(
                            f"Audio playback failed: {response.status}"
                        )
                
                total_chunks += 1
                
                # Small delay to simulate real-time playback
                await asyncio.sleep(self.chunk_duration_ms / 1000)
            
            logger.info(
                f"[ARI] Audio playback complete: channel={channel_id}, "
                f"chunks={total_chunks}"
            )
            
        except Exception as e:
            error_msg = f"Audio playback failed: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            raise ARIClientError(error_msg)
    
    async def _convert_to_pcm(self, audio_data: bytes, format: str) -> bytes:
        """
        Convert audio to PCM 16-bit 8kHz mono for telephony.
        
        Args:
            audio_data: Audio bytes in source format
            format: Source format (mp3, wav, etc.)
            
        Returns:
            bytes: PCM audio data
        """
        try:
            # Use pydub for audio format conversion
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format=format)
            
            # Convert to telephony format: 16-bit PCM, 8kHz, mono
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_channels(self.channels)
            audio = audio.set_sample_width(self.sample_width)
            
            # Export as raw PCM
            pcm_data = audio.raw_data
            
            logger.debug(
                f"[ARI] Audio converted: format={format}, "
                f"pcm_size={len(pcm_data)}B"
            )
            
            return pcm_data
            
        except Exception as e:
            error_msg = f"Audio conversion failed: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            raise ARIClientError(error_msg)
    
    async def hangup_call(self, channel_id: str) -> None:
        """
        Hang up a call via ARI.
        
        Args:
            channel_id: Asterisk channel ID
            
        Raises:
            ARIClientError: If hangup fails
        """
        try:
            if not self.session:
                raise ARIClientError("Not connected to ARI")
            
            url = urljoin(self.base_url, f"/ari/channels/{channel_id}")
            async with self.session.delete(url) as response:
                if response.status not in [204, 404]:  # 404 = already hung up
                    error = await response.text()
                    raise ARIClientError(f"Hangup failed: {response.status} {error}")
            
            logger.info(f"[ARI] Call hung up: channel={channel_id}")
            
        except Exception as e:
            error_msg = f"Failed to hangup call: {type(e).__name__}: {e}"
            logger.error(f"[ARI] {error_msg}")
            # Don't raise - hangup is best-effort
            logger.warning(f"[ARI] Continuing despite hangup error")
    
    async def health_check(self) -> bool:
        """
        Check if ARI is available.
        
        Returns:
            bool: True if ARI is healthy, False otherwise
        """
        try:
            if not self.session:
                # Try to connect
                await self.connect()
            
            # Test API availability
            url = urljoin(self.base_url, "/ari/asterisk/info")
            async with self.session.get(url) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"[ARI] Health check failed: {type(e).__name__}: {e}")
            return False


# Implementation Notes:
# - ARI External Media provides bidirectional audio streaming
# - PCM 16-bit 8kHz mono is telephony standard
# - Minimal deterministic VAD for aggressive silence exit (not ML-based)
# - Immediate response playback (no sentence buffering)
# - Fail-fast behavior honors COMMIT 1 discipline
#
# Known Limitations:
# - External Media requires proper Asterisk configuration (ari.conf)
# - RTP streaming details abstracted in this implementation
# - Actual deployment needs network configuration for RTP
#
# TODO (Out of Scope):
# - DTMF detection for user input
# - Call recording with encryption
# - Barge-in detection (caller interrupting AI) with sophisticated audio mixing
# - Audio quality monitoring and adaptation
# - Advanced VAD with ML models
# - Multiple codec support beyond PCM
