"""
Services for Agent Brain v1 APIs.

These services provide simulated AI functionality without real LLM calls:
- Language detection (simulated)
- Language switching detection (simulated)
- Runtime context building (prompt assembly, no LLM)

All responses are clearly marked as simulated/mock.
"""

from app.services.language_detection import LanguageDetectionService
from app.services.language_switch import LanguageSwitchDetector
from app.services.runtime_context import RuntimeContextBuilder

__all__ = [
    "LanguageDetectionService",
    "LanguageSwitchDetector",
    "RuntimeContextBuilder",
]
