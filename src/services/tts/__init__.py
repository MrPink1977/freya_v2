"""
TTS Service Package

Provides text-to-speech capabilities for Freya v2.0.
"""

from src.services.tts.tts_service import TTSService, TTSServiceError

__all__ = ["TTSService", "TTSServiceError"]
