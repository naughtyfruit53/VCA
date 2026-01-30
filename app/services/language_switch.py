"""
Language Switch Detector for Agent Brain v1 APIs.

IMPORTANT: This is a SIMULATED service. No real language switching detection is performed.
All responses are mock data for testing purposes.

The service simulates detection of explicit language change requests and manages
session-specific speaking_language (locked after change).
"""

from typing import Dict, Optional, Any


class LanguageSwitchDetector:
    """
    Simulated language switch detection service.
    
    This service DOES NOT perform real language switching detection. It generates
    mock detection results for testing and development purposes.
    
    Session-based logic:
    - Detects explicit language change requests
    - Updates session-specific speaking_language
    - Locks speaking_language after explicit change (cannot auto-switch)
    """
    
    def __init__(self):
        """Initialize the simulated language switch detector."""
        self._session_speaking_language: Dict[str, str] = {}
        self._session_locked: Dict[str, bool] = {}
    
    def detect_language_switch_request(
        self,
        text: str,
        session_id: str,
        current_language: str
    ) -> Dict[str, Any]:
        """
        Detect explicit language change request (SIMULATED).
        
        This method SIMULATES language switch detection and returns mock results.
        
        Args:
            text: Input text to check for language switch request
            session_id: Session identifier
            current_language: Current speaking language for the session
            
        Returns:
            Dict with keys:
                - switch_requested: Whether language switch was requested
                - target_language: Requested language (if switch_requested=True)
                - speaking_language: Updated speaking language for session
                - is_locked: Whether speaking_language is now locked
                
        Note:
            This is a MOCK implementation. No actual language detection is performed.
        """
        text_lower = text.lower()
        
        # Initialize session state if needed
        if session_id not in self._session_speaking_language:
            self._session_speaking_language[session_id] = current_language
            self._session_locked[session_id] = False
        
        # SIMULATED switch detection logic
        # In a real implementation, this would use NLP to understand intent
        switch_patterns = {
            "en": ["speak english", "switch to english", "in english", "english please"],
            "hi": ["hindi mein bolo", "speak hindi", "in hindi", "hindi please"],
            "mr": ["marathi mein bolo", "speak marathi", "in marathi", "marathi please"],
            "gu": ["gujarati mein bolo", "speak gujarati", "in gujarati", "gujarati please"],
        }
        
        switch_requested = False
        target_language = None
        
        # Check for explicit language switch patterns
        for lang, patterns in switch_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                switch_requested = True
                target_language = lang
                break
        
        # Update session state if switch was requested
        if switch_requested:
            self._session_speaking_language[session_id] = target_language
            self._session_locked[session_id] = True  # Lock after explicit change
        
        return {
            "switch_requested": switch_requested,
            "target_language": target_language,
            "speaking_language": self._session_speaking_language[session_id],
            "is_locked": self._session_locked[session_id]
        }
    
    def get_speaking_language(self, session_id: str, default: str = "en") -> str:
        """
        Get current speaking language for a session.
        
        Args:
            session_id: Session identifier
            default: Default language if session not found
            
        Returns:
            Current speaking language for the session
        """
        return self._session_speaking_language.get(session_id, default)
    
    def is_language_locked(self, session_id: str) -> bool:
        """
        Check if speaking language is locked for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if language is locked, False otherwise
        """
        return self._session_locked.get(session_id, False)
    
    def set_speaking_language(self, session_id: str, language: str, lock: bool = False) -> None:
        """
        Manually set speaking language for a session.
        
        Args:
            session_id: Session identifier
            language: Language code to set
            lock: Whether to lock the language
        """
        self._session_speaking_language[session_id] = language
        if lock:
            self._session_locked[session_id] = True
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear session state for language switching.
        
        Args:
            session_id: Session identifier to clear
        """
        if session_id in self._session_speaking_language:
            del self._session_speaking_language[session_id]
        if session_id in self._session_locked:
            del self._session_locked[session_id]
