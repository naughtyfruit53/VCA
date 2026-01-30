"""
Language Detection Service for Agent Brain v1 APIs.

IMPORTANT: This is a SIMULATED service. No real language detection is performed.
All responses are mock data for testing purposes.

The service simulates language detection with confidence scores and implements
session-based detection logic with fallback to primary_language.
"""

from typing import Dict, Optional
import random

# Confidence threshold for language detection
LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD = 0.65


class LanguageDetectionService:
    """
    Simulated language detection service.
    
    This service DOES NOT perform real language detection. It generates
    mock detection results for testing and development purposes.
    
    Session-based logic:
    - Detects language once per session_id
    - Falls back to primary_language if confidence < LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD
    - Caches detection result per session
    """
    
    def __init__(self):
        """Initialize the simulated language detection service."""
        self._session_cache: Dict[str, Dict[str, any]] = {}
    
    def detect_language(
        self,
        text: str,
        session_id: str,
        primary_language: str = "en"
    ) -> Dict[str, any]:
        """
        Detect language from text (SIMULATED).
        
        This method SIMULATES language detection and returns mock results.
        Detection is performed once per session_id and cached.
        
        Args:
            text: Input text to detect language from
            session_id: Session identifier for caching detection
            primary_language: Fallback language if confidence is low
            
        Returns:
            Dict with keys:
                - detected_language: Language code (en/hi/mr/gu)
                - confidence: Confidence score (0.0-1.0)
                - used_fallback: Whether primary_language was used as fallback
                
        Note:
            This is a MOCK implementation. No actual language detection is performed.
        """
        # Check if we already detected for this session
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        
        # SIMULATED detection logic
        # In a real implementation, this would use an NLP model
        detected_language, confidence = self._simulate_detection(text)
        
        # Apply confidence threshold and fallback logic
        used_fallback = False
        if confidence < LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD:
            detected_language = primary_language
            confidence = 1.0  # We're certain about the fallback
            used_fallback = True
        
        result = {
            "detected_language": detected_language,
            "confidence": confidence,
            "used_fallback": used_fallback
        }
        
        # Cache for this session
        self._session_cache[session_id] = result
        
        return result
    
    def _simulate_detection(self, text: str) -> tuple[str, float]:
        """
        Simulate language detection (MOCK implementation).
        
        This is a placeholder that returns mock results based on simple heuristics.
        In production, this would call a real language detection service.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        # Simple heuristic: check for language-specific keywords (MOCK)
        text_lower = text.lower()
        
        # Hindi detection (mock)
        hindi_keywords = ["namaste", "kaise", "aap", "hai", "मैं", "हूं"]
        if any(keyword in text_lower for keyword in hindi_keywords):
            return "hi", random.uniform(0.7, 0.95)
        
        # Marathi detection (mock)
        marathi_keywords = ["kasa", "tumhi", "aahe", "मी", "आहे"]
        if any(keyword in text_lower for keyword in marathi_keywords):
            return "mr", random.uniform(0.7, 0.95)
        
        # Gujarati detection (mock)
        gujarati_keywords = ["kem", "tamne", "chhe", "હું", "છું"]
        if any(keyword in text_lower for keyword in gujarati_keywords):
            return "gu", random.uniform(0.7, 0.95)
        
        # Default to English with variable confidence
        # Sometimes return low confidence to test fallback logic
        if random.random() < 0.3:  # 30% chance of low confidence
            return "en", random.uniform(0.4, 0.64)
        else:
            return "en", random.uniform(0.75, 0.95)
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear cached detection for a session.
        
        Args:
            session_id: Session identifier to clear
        """
        if session_id in self._session_cache:
            del self._session_cache[session_id]
    
    def get_session_language(self, session_id: str) -> Optional[str]:
        """
        Get detected language for a session if cached.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Language code if cached, None otherwise
        """
        if session_id in self._session_cache:
            return self._session_cache[session_id]["detected_language"]
        return None
