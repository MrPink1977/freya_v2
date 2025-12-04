"""
Audio Service Package

Provides audio input/output management for Freya v2.0.
"""

from src.services.audio.audio_manager import AudioManager, AudioManagerError

__all__ = ["AudioManager", "AudioManagerError"]
