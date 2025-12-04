"""
Mock Audio Data Generators

Provides mock audio data and utilities for testing audio services.
"""

import numpy as np
import wave
import io
from typing import Optional


def generate_tone(
    frequency: float = 440.0,
    duration: float = 1.0,
    sample_rate: int = 16000,
    amplitude: float = 0.5
) -> bytes:
    """
    Generate a simple sine wave tone as PCM audio data.
    
    Args:
        frequency: Tone frequency in Hz (default: 440Hz = A4 note)
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0.0 to 1.0)
    
    Returns:
        16-bit PCM audio data as bytes
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = amplitude * np.sin(2 * np.pi * frequency * t)
    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()


def generate_silence(
    duration: float = 1.0,
    sample_rate: int = 16000
) -> bytes:
    """
    Generate silence as PCM audio data.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    
    Returns:
        16-bit PCM audio data as bytes (all zeros)
    """
    num_samples = int(sample_rate * duration)
    return np.zeros(num_samples, dtype=np.int16).tobytes()


def generate_white_noise(
    duration: float = 1.0,
    sample_rate: int = 16000,
    amplitude: float = 0.1
) -> bytes:
    """
    Generate white noise as PCM audio data.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0.0 to 1.0)
    
    Returns:
        16-bit PCM audio data as bytes
    """
    num_samples = int(sample_rate * duration)
    noise = amplitude * np.random.uniform(-1, 1, num_samples)
    noise_int16 = (noise * 32767).astype(np.int16)
    return noise_int16.tobytes()


def create_wav_file(
    audio_data: bytes,
    sample_rate: int = 16000,
    channels: int = 1
) -> bytes:
    """
    Create a WAV file from PCM audio data.
    
    Args:
        audio_data: 16-bit PCM audio data
        sample_rate: Sample rate in Hz
        channels: Number of channels
    
    Returns:
        WAV file as bytes
    """
    wav_buffer = io.BytesIO()
    
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    
    return wav_buffer.getvalue()


def get_audio_info(audio_data: bytes) -> dict:
    """
    Get information about PCM audio data.
    
    Args:
        audio_data: 16-bit PCM audio data
    
    Returns:
        Dictionary with audio information
    """
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    return {
        "num_samples": len(audio_array),
        "duration_seconds": len(audio_array) / 16000,  # Assuming 16kHz
        "size_bytes": len(audio_data),
        "max_amplitude": np.max(np.abs(audio_array)),
        "rms": np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
    }
