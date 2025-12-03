"""
Manual Test Script for STT Service

This script allows you to test the STT service by publishing
audio data to the message bus and listening for transcriptions.

Usage:
    python tests/test_stt_manual.py [audio_file.wav]

If no audio file is provided, it will generate a simple test tone.
"""

import asyncio
import sys
import wave
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.message_bus import MessageBus
from src.core.config import config


async def generate_test_audio() -> bytes:
    """
    Generate a simple test audio file (WAV format).

    Creates a 3-second audio file with a simple tone.

    Returns:
        WAV file as bytes
    """
    logger.info("Generating test audio (3 second tone)...")

    sample_rate = 16000
    duration = 3  # seconds
    frequency = 440  # A4 note

    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)

    # Create WAV file in memory
    import io
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    wav_bytes = wav_buffer.getvalue()
    logger.success(f"✓ Generated {len(wav_bytes)} bytes of test audio")

    return wav_bytes


async def load_audio_file(file_path: str) -> bytes:
    """
    Load an audio file from disk.

    Args:
        file_path: Path to WAV file

    Returns:
        WAV file as bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a valid WAV
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    if not path.suffix.lower() == '.wav':
        raise ValueError(f"Only WAV files supported, got: {path.suffix}")

    logger.info(f"Loading audio file: {file_path}")

    with open(path, 'rb') as f:
        audio_bytes = f.read()

    logger.success(f"✓ Loaded {len(audio_bytes)} bytes from {file_path}")

    return audio_bytes


async def transcription_listener(data: dict) -> None:
    """
    Callback for transcription messages.

    Args:
        data: Transcription data from message bus
    """
    logger.info("=" * 70)
    logger.success("📝 TRANSCRIPTION RECEIVED:")
    logger.info("=" * 70)
    logger.info(f"Text: \"{data.get('text', '')}\"")
    logger.info(f"Language: {data.get('language', 'unknown')}")
    logger.info(f"Confidence: {data.get('confidence', 0):.2%}")
    logger.info(f"Duration: {data.get('duration', 0):.2f}s")
    logger.info(f"Timestamp: {data.get('timestamp', '')}")
    logger.info("=" * 70)


async def main() -> None:
    """Main test function."""
    logger.info("=" * 70)
    logger.info("STT Service Manual Test")
    logger.info("=" * 70)

    # Get audio file from command line or generate test audio
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        try:
            audio_bytes = await load_audio_file(audio_file)
        except Exception as e:
            logger.error(f"Failed to load audio file: {e}")
            return
    else:
        logger.warning("No audio file provided, generating test tone")
        logger.warning("For real testing, provide a WAV file: python tests/test_stt_manual.py file.wav")
        audio_bytes = await generate_test_audio()

    # Connect to message bus
    logger.info("Connecting to message bus...")
    message_bus = MessageBus(
        redis_host=config.redis_host,
        redis_port=config.redis_port
    )

    try:
        await message_bus.connect()
        logger.success("✓ Connected to message bus")

        # Subscribe to transcription channel
        logger.info("Subscribing to transcription channel...")
        await message_bus.subscribe("stt.transcription", transcription_listener)
        logger.success("✓ Subscribed to stt.transcription")

        # Start message bus listener
        bus_task = asyncio.create_task(message_bus.start())

        # Wait a moment for subscription to be ready
        await asyncio.sleep(1)

        # Publish audio to audio.stream channel
        logger.info("=" * 70)
        logger.info("📤 Publishing audio to message bus...")
        logger.info("=" * 70)

        audio_message = {
            "audio_data": audio_bytes,
            "format": "wav",
            "sample_rate": 16000,
            "timestamp": datetime.now().isoformat(),
            "location": "test_location"
        }

        await message_bus.publish("audio.stream", audio_message)
        logger.success("✓ Audio published to audio.stream")

        # Wait for transcription (with timeout)
        logger.info("Waiting for transcription (timeout: 30s)...")

        try:
            await asyncio.wait_for(asyncio.sleep(30), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("⚠️  Timeout waiting for transcription")

        # Cleanup
        logger.info("Cleaning up...")
        bus_task.cancel()
        try:
            await bus_task
        except asyncio.CancelledError:
            pass

        await message_bus.unsubscribe("stt.transcription")
        await message_bus.stop()
        await message_bus.disconnect()

        logger.info("=" * 70)
        logger.success("✓ Test completed")
        logger.info("=" * 70)

    except Exception as e:
        logger.exception(f"Test failed: {e}")

    finally:
        if message_bus.is_connected():
            await message_bus.disconnect()


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
