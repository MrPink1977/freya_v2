"""
STT Service - Speech-to-Text transcription for Freya v2.0

Manages speech-to-text transcription using faster-whisper for local,
GPU-accelerated audio transcription with high accuracy.

Author: MrPink1977
Version: 0.1.0
Date: 2025-12-03
"""

from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime
import asyncio
import numpy as np
import io
import wave
import time

try:
    from faster_whisper import WhisperModel
except ImportError:
    logger.warning("faster-whisper not installed. STT service will not be available.")
    WhisperModel = None

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config


class STTServiceError(ServiceError):
    """Exception raised for STT Service specific errors."""
    pass


class STTService(BaseService):
    """
    Speech-to-Text service for transcribing audio to text.

    This service uses faster-whisper to transcribe audio streams with GPU
    acceleration. It subscribes to audio streams on the message bus and
    publishes transcriptions for the LLM Engine to process.

    Subscribes to:
        - audio.stream: Raw audio data from Audio Manager or test scripts

    Publishes to:
        - stt.transcription: Transcribed text with metadata
        - service.stt.status: Service status updates
        - service.stt.metrics: Performance metrics

    Attributes:
        model: faster-whisper WhisperModel instance
        device: Device for inference (cuda, cpu, or auto)
        compute_type: Compute type for model (int8, float16, etc.)
        transcription_count: Total number of transcriptions performed
        total_duration: Total transcription time in seconds

    Example:
        >>> stt = STTService(message_bus)
        >>> await stt.initialize()
        >>> await stt.start()
    """

    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the STT Service.

        Args:
            message_bus: Shared MessageBus instance

        Raises:
            STTServiceError: If faster-whisper is not available
        """
        super().__init__("stt_service", message_bus)

        if WhisperModel is None:
            raise STTServiceError(
                "faster-whisper package not installed. "
                "Install with: pip install faster-whisper"
            )

        self.model: Optional[WhisperModel] = None
        self.device = self._determine_device()
        self.compute_type = config.stt_compute_type
        self.transcription_count = 0
        self.total_duration = 0.0
        self._model_loaded = False

        logger.debug(
            f"[{self.name}] Initialized - model={config.stt_model}, "
            f"device={self.device}, compute_type={self.compute_type}"
        )

    def _determine_device(self) -> str:
        """
        Determine the appropriate device for inference.

        Returns:
            Device string ("cuda" or "cpu")
        """
        if config.stt_device == "auto":
            # Try to detect CUDA availability
            try:
                import torch
                if torch.cuda.is_available():
                    logger.info(f"[{self.name}] CUDA detected, using GPU acceleration")
                    return "cuda"
                else:
                    logger.warning(f"[{self.name}] CUDA not available, using CPU")
                    return "cpu"
            except ImportError:
                logger.warning(f"[{self.name}] PyTorch not available, using CPU")
                return "cpu"
        else:
            return config.stt_device

    async def initialize(self) -> None:
        """
        Initialize the STT service and load the Whisper model.

        This loads the faster-whisper model with configured settings.
        First run will download the model files.

        Raises:
            STTServiceError: If model loading fails
        """
        try:
            logger.info(
                f"[{self.name}] Loading Whisper model '{config.stt_model}' "
                f"on {self.device}..."
            )

            start_time = time.time()

            # Load the model
            # Note: This runs in a thread pool to avoid blocking
            self.model = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: WhisperModel(
                    config.stt_model,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=None,  # Use default cache directory
                )
            )

            load_time = time.time() - start_time
            self._model_loaded = True
            self._healthy = True

            logger.success(
                f"[{self.name}] ✓ Model loaded successfully in {load_time:.2f}s"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to load model: {e}")
            self._healthy = False
            self.increment_error_count()
            raise STTServiceError(f"Model loading failed: {e}") from e

    async def start(self) -> None:
        """
        Start the STT service.

        Subscribes to audio.stream channel and begins processing audio.

        Raises:
            STTServiceError: If service fails to start
        """
        try:
            if not self._model_loaded:
                raise STTServiceError("Model not loaded. Call initialize() first.")

            logger.info(f"[{self.name}] Starting STT service...")

            # Subscribe to audio streams
            await self.message_bus.subscribe("audio.stream", self._handle_audio)

            self._mark_started()
            await self.publish_status("started")

            logger.success(f"[{self.name}] ✓ STT service started successfully")

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to start: {e}")
            self.increment_error_count()
            raise STTServiceError(f"Service start failed: {e}") from e

    async def stop(self) -> None:
        """
        Stop the STT service gracefully.

        Unsubscribes from channels and cleans up resources.

        Raises:
            STTServiceError: If service fails to stop cleanly
        """
        try:
            logger.info(f"[{self.name}] Stopping STT service...")

            # Unsubscribe from audio streams
            await self.message_bus.unsubscribe("audio.stream")

            self._mark_stopped()
            await self.publish_status("stopped")

            # Publish final metrics
            await self._publish_metrics()

            logger.success(
                f"[{self.name}] ✓ STT service stopped. "
                f"Total transcriptions: {self.transcription_count}"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error during shutdown: {e}")
            self.increment_error_count()
            raise STTServiceError(f"Service stop failed: {e}") from e

    async def health_check(self) -> bool:
        """
        Check if the STT service is healthy.

        Returns:
            True if service is operational, False otherwise
        """
        if not await super().health_check():
            return False

        # Check if model is loaded
        if not self._model_loaded or self.model is None:
            logger.warning(f"[{self.name}] ⚠️  Health check failed: Model not loaded")
            return False

        return True

    async def _handle_audio(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming audio data for transcription.

        Args:
            data: Audio data dictionary with format:
                {
                    "audio_data": bytes,  # Raw audio bytes
                    "format": str,  # Audio format (e.g., "wav", "raw")
                    "sample_rate": int,  # Sample rate in Hz
                    "timestamp": str,  # ISO timestamp
                    "location": str (optional)  # Source location
                }
        """
        try:
            logger.debug(f"[{self.name}] 📥 Received audio for transcription")

            # Validate input data
            if not isinstance(data, dict):
                raise STTServiceError(f"Invalid data type: {type(data)}")

            if "audio_data" not in data:
                raise STTServiceError("Missing 'audio_data' in message")

            audio_data = data.get("audio_data")
            audio_format = data.get("format", "wav")
            sample_rate = data.get("sample_rate", config.audio_sample_rate)
            location = data.get("location", "unknown")

            # Convert audio data to numpy array
            audio_array = await self._process_audio_data(
                audio_data, audio_format, sample_rate
            )

            # Perform transcription
            transcription = await self._transcribe(audio_array, sample_rate)

            # Add metadata and publish
            transcription["location"] = location
            transcription["source_timestamp"] = data.get("timestamp")

            await self.message_bus.publish("stt.transcription", transcription)

            logger.info(
                f"[{self.name}] 📤 Transcription: \"{transcription['text']}\" "
                f"(confidence: {transcription['confidence']:.2f}, "
                f"duration: {transcription['duration']:.2f}s)"
            )

            # Update metrics
            self.transcription_count += 1
            if self.transcription_count % 10 == 0:  # Publish metrics every 10 transcriptions
                await self._publish_metrics()

        except STTServiceError as e:
            logger.error(f"[{self.name}] ❌ STT error: {e}")
            self.increment_error_count()

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Unexpected error: {e}")
            self.increment_error_count()

    async def _process_audio_data(
        self,
        audio_data: bytes,
        audio_format: str,
        sample_rate: int
    ) -> np.ndarray:
        """
        Process raw audio data into numpy array for transcription.

        Args:
            audio_data: Raw audio bytes
            audio_format: Format of audio (wav, raw, etc.)
            sample_rate: Sample rate in Hz

        Returns:
            Numpy array of audio samples (float32, mono, normalized to [-1, 1])

        Raises:
            STTServiceError: If audio processing fails
        """
        try:
            if audio_format == "wav":
                # Parse WAV file
                with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                    # Get audio parameters
                    n_channels = wav_file.getnchannels()
                    sampwidth = wav_file.getsampwidth()
                    framerate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()

                    # Read raw audio
                    raw_audio = wav_file.readframes(n_frames)

                    # Convert to numpy array
                    if sampwidth == 2:  # 16-bit
                        audio_array = np.frombuffer(raw_audio, dtype=np.int16)
                    elif sampwidth == 4:  # 32-bit
                        audio_array = np.frombuffer(raw_audio, dtype=np.int32)
                    else:
                        raise STTServiceError(f"Unsupported sample width: {sampwidth}")

                    # Convert to float32 and normalize to [-1, 1]
                    audio_array = audio_array.astype(np.float32)
                    audio_array /= np.iinfo(audio_array.dtype).max if sampwidth == 2 else 2147483648.0

                    # Convert stereo to mono if needed
                    if n_channels == 2:
                        audio_array = audio_array.reshape((-1, 2)).mean(axis=1)

                    logger.debug(
                        f"[{self.name}] Processed WAV: {len(audio_array)} samples, "
                        f"{framerate}Hz, {n_channels}ch"
                    )

                    return audio_array

            elif audio_format == "raw":
                # Assume raw 16-bit PCM
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                audio_array = audio_array.astype(np.float32) / 32768.0
                return audio_array

            else:
                raise STTServiceError(f"Unsupported audio format: {audio_format}")

        except Exception as e:
            raise STTServiceError(f"Audio processing failed: {e}") from e

    async def _transcribe(
        self,
        audio_array: np.ndarray,
        sample_rate: int
    ) -> Dict[str, Any]:
        """
        Transcribe audio using faster-whisper.

        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary with transcription results:
            {
                "text": str,
                "language": str,
                "confidence": float,
                "duration": float,
                "timestamp": str
            }

        Raises:
            STTServiceError: If transcription fails
        """
        try:
            start_time = time.time()

            # Run transcription in thread pool to avoid blocking
            segments, info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_array,
                    language=config.stt_language if config.stt_language != "auto" else None,
                    beam_size=config.stt_beam_size,
                    vad_filter=config.stt_vad_filter,
                    condition_on_previous_text=config.stt_condition_on_previous_text,
                )
            )

            # Collect all segments
            text_segments = []
            confidences = []

            for segment in segments:
                text_segments.append(segment.text.strip())
                confidences.append(segment.avg_logprob)

            # Combine segments
            full_text = " ".join(text_segments)
            avg_confidence = np.mean(confidences) if confidences else 0.0

            # Convert log probability to approximate confidence (0-1)
            # avg_logprob ranges from -inf to 0, we'll map to 0-1
            confidence = np.exp(avg_confidence) if avg_confidence > -10 else 0.0

            duration = time.time() - start_time
            self.total_duration += duration

            logger.debug(
                f"[{self.name}] Transcription completed in {duration:.2f}s - "
                f"language={info.language}, confidence={confidence:.2f}"
            )

            return {
                "text": full_text,
                "language": info.language,
                "confidence": confidence,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            raise STTServiceError(f"Transcription failed: {e}") from e

    async def _publish_metrics(self) -> None:
        """Publish service metrics to the message bus."""
        try:
            avg_duration = (
                self.total_duration / self.transcription_count
                if self.transcription_count > 0
                else 0.0
            )

            metrics = {
                "service": self.name,
                "transcription_count": self.transcription_count,
                "total_duration": self.total_duration,
                "avg_duration": avg_duration,
                "error_count": self._error_count,
                "uptime": self.get_uptime(),
                "timestamp": datetime.now().isoformat()
            }

            await self.message_bus.publish("service.stt.metrics", metrics)

            logger.debug(
                f"[{self.name}] 📊 Metrics: {self.transcription_count} transcriptions, "
                f"avg {avg_duration:.2f}s/transcription"
            )

        except Exception as e:
            logger.error(f"[{self.name}] Failed to publish metrics: {e}")
