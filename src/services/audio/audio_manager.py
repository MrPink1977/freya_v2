"""
Audio Manager - Audio I/O Management for Freya v2.0

Manages audio input/output using PyAudio, handling microphone capture
and speaker playback with proper device management and error handling.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-04
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import threading
from queue import Queue, Empty
import wave
import io
from loguru import logger

try:
    import pyaudio
    import numpy as np
except ImportError:
    logger.warning("PyAudio or numpy not installed. Audio Manager will not be available.")
    pyaudio = None
    np = None

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config


class AudioManagerError(ServiceError):
    """Exception raised for Audio Manager specific errors."""
    pass


class AudioManager(BaseService):
    """
    Audio Manager for handling microphone input and speaker output.
    
    Manages two separate threads:
    - Input thread: Captures audio from microphone and publishes to message bus
    - Output thread: Receives audio from message bus and plays on speaker
    
    Subscribes to:
        - audio.output.stream: Audio data to play on speakers
        - audio.control.start_recording: Start audio capture
        - audio.control.stop_recording: Stop audio capture
    
    Publishes to:
        - audio.input.stream: Captured audio data from microphone
        - audio.device.list: Available audio devices
        - service.audio_manager.status: Service status updates
        - service.audio_manager.metrics: Performance metrics
    
    Attributes:
        pyaudio_instance: PyAudio instance for audio I/O
        input_stream: Audio input stream (microphone)
        output_stream: Audio output stream (speaker)
        input_thread: Thread for audio capture
        output_thread: Thread for audio playback
        input_queue: Queue for buffering input audio
        output_queue: Queue for buffering output audio
        is_recording: Flag indicating if recording is active
        is_playing: Flag indicating if playback is active
    """
    
    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the Audio Manager.
        
        Args:
            message_bus: Shared MessageBus instance
        
        Raises:
            AudioManagerError: If PyAudio is not available
        """
        super().__init__("audio_manager", message_bus)
        
        if pyaudio is None:
            raise AudioManagerError(
                "PyAudio not installed. Install with: pip install pyaudio"
            )
        
        if np is None:
            raise AudioManagerError(
                "NumPy not installed. Install with: pip install numpy"
            )
        
        # PyAudio instance
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        
        # Audio streams
        self.input_stream: Optional[pyaudio.Stream] = None
        self.output_stream: Optional[pyaudio.Stream] = None
        
        # Threading
        self.input_thread: Optional[threading.Thread] = None
        self.output_thread: Optional[threading.Thread] = None
        self.input_queue: Queue = Queue(maxsize=100)
        self.output_queue: Queue = Queue(maxsize=100)
        
        # Control flags
        self.is_recording = False
        self.is_playing = False
        self._stop_input_thread = threading.Event()
        self._stop_output_thread = threading.Event()
        
        # Audio configuration
        self.sample_rate = config.audio_sample_rate
        self.channels = config.audio_channels
        self.chunk_size = config.audio_chunk_size
        self.input_device_index = getattr(config, 'audio_input_device_index', None)
        self.output_device_index = getattr(config, 'audio_output_device_index', None)
        
        # Metrics
        self.input_buffer_count = 0
        self.output_buffer_count = 0
        
        logger.debug(
            f"[{self.name}] Initialized with sample_rate={self.sample_rate}, "
            f"channels={self.channels}, chunk_size={self.chunk_size}"
        )
    
    async def initialize(self) -> None:
        """
        Initialize the Audio Manager.
        
        Raises:
            AudioManagerError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing Audio Manager...")
            
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Enumerate and log available devices
            device_count = self.pyaudio_instance.get_device_count()
            logger.info(f"[{self.name}] Found {device_count} audio devices")
            
            devices = []
            for i in range(device_count):
                info = self.pyaudio_instance.get_device_info_by_index(i)
                devices.append({
                    "index": i,
                    "name": info.get("name"),
                    "max_input_channels": info.get("maxInputChannels"),
                    "max_output_channels": info.get("maxOutputChannels"),
                    "default_sample_rate": info.get("defaultSampleRate")
                })
                logger.debug(
                    f"[{self.name}] Device {i}: {info.get('name')} "
                    f"(in:{info.get('maxInputChannels')}, "
                    f"out:{info.get('maxOutputChannels')})"
                )
            
            # Publish device list
            await self.message_bus.publish("audio.device.list", {
                "devices": devices,
                "timestamp": datetime.now().isoformat()
            })
            
            self._healthy = True
            logger.success(f"[{self.name}] ✓ Audio Manager initialized")
            
        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Initialization failed: {e}")
            self._healthy = False
            self.increment_error_count()
            raise AudioManagerError(f"Initialization failed: {e}") from e
    
    async def start(self) -> None:
        """
        Start the Audio Manager service.
        
        Starts input and output threads and subscribes to message bus channels.
        
        Raises:
            AudioManagerError: If service fails to start
        """
        try:
            logger.info(f"[{self.name}] Starting Audio Manager...")
            
            # Subscribe to message bus channels
            await self.message_bus.subscribe(
                "audio.output.stream",
                self._handle_output_audio
            )
            await self.message_bus.subscribe(
                "audio.control.start_recording",
                self._handle_start_recording
            )
            await self.message_bus.subscribe(
                "audio.control.stop_recording",
                self._handle_stop_recording
            )
            
            # Start output thread (always active)
            self._start_output_thread()
            
            # Start input thread if auto-recording is enabled
            # For now, start by default
            await self._start_input_stream()
            
            self._mark_started()
            await self.publish_status("started", {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_size": self.chunk_size
            })
            
            logger.success(f"[{self.name}] ✓ Audio Manager started")
            
        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to start: {e}")
            self.increment_error_count()
            raise AudioManagerError(f"Service start failed: {e}") from e
    
    async def stop(self) -> None:
        """
        Stop the Audio Manager gracefully.
        """
        try:
            logger.info(f"[{self.name}] Stopping Audio Manager...")
            
            # Stop input stream
            await self._stop_input_stream()
            
            # Stop output thread
            self._stop_output_thread_func()
            
            # Unsubscribe from message bus
            await self.message_bus.unsubscribe("audio.output.stream")
            await self.message_bus.unsubscribe("audio.control.start_recording")
            await self.message_bus.unsubscribe("audio.control.stop_recording")
            
            # Close streams
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
                self.output_stream = None
            
            # Terminate PyAudio
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
            
            self._mark_stopped()
            await self.publish_status("stopped")
            
            logger.success(f"[{self.name}] ✓ Audio Manager stopped")
            
        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error during shutdown: {e}")
            self.increment_error_count()
            raise AudioManagerError(f"Service stop failed: {e}") from e
    
    # Input Stream Management
    
    async def _start_input_stream(self) -> None:
        """Start audio input stream and capture thread."""
        try:
            if self.is_recording:
                logger.warning(f"[{self.name}] Input stream already running")
                return
            
            logger.info(f"[{self.name}] Starting audio input stream...")
            
            # Open input stream
            self.input_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=None  # We'll use blocking mode
            )
            
            # Start input thread
            self._stop_input_thread.clear()
            self.input_thread = threading.Thread(
                target=self._input_loop,
                daemon=True
            )
            self.input_thread.start()
            
            self.is_recording = True
            
            logger.success(f"[{self.name}] ✓ Audio input stream started")
            
        except Exception as e:
            logger.error(f"[{self.name}] Failed to start input stream: {e}")
            self.increment_error_count()
            raise
    
    async def _stop_input_stream(self) -> None:
        """Stop audio input stream and capture thread."""
        try:
            if not self.is_recording:
                return
            
            logger.info(f"[{self.name}] Stopping audio input stream...")
            
            # Signal thread to stop
            self._stop_input_thread.set()
            
            # Wait for thread to finish
            if self.input_thread and self.input_thread.is_alive():
                self.input_thread.join(timeout=2.0)
            
            # Close stream
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            self.is_recording = False
            
            logger.success(f"[{self.name}] ✓ Audio input stream stopped")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error stopping input stream: {e}")
            self.increment_error_count()
    
    def _input_loop(self) -> None:
        """Input thread loop for capturing audio from microphone."""
        logger.info(f"[{self.name}] Input thread started")
        
        try:
            while not self._stop_input_thread.is_set():
                try:
                    # Read audio chunk from microphone
                    audio_chunk = self.input_stream.read(
                        self.chunk_size,
                        exception_on_overflow=False
                    )
                    
                    # Add to queue
                    try:
                        self.input_queue.put_nowait(audio_chunk)
                        self.input_buffer_count += 1
                        
                        # Process queue asynchronously (publish to message bus)
                        asyncio.run_coroutine_threadsafe(
                            self._process_input_queue(),
                            asyncio.get_event_loop()
                        )
                        
                    except:
                        # Queue full, drop oldest
                        try:
                            self.input_queue.get_nowait()
                            self.input_queue.put_nowait(audio_chunk)
                        except:
                            pass
                    
                except Exception as e:
                    if not self._stop_input_thread.is_set():
                        logger.error(f"[{self.name}] Input loop error: {e}")
                        self.increment_error_count()
                
        finally:
            logger.info(f"[{self.name}] Input thread stopped")
    
    async def _process_input_queue(self) -> None:
        """Process input queue and publish audio to message bus."""
        try:
            # Get all available chunks
            chunks = []
            while not self.input_queue.empty():
                try:
                    chunk = self.input_queue.get_nowait()
                    chunks.append(chunk)
                except Empty:
                    break
            
            if not chunks:
                return
            
            # Combine chunks
            audio_data = b''.join(chunks)
            
            # Publish to message bus
            await self.message_bus.publish("audio.input.stream", {
                "audio_data": audio_data,
                "format": "pcm_s16le",
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"[{self.name}] Error processing input queue: {e}")
    
    # Output Stream Management
    
    def _start_output_thread(self) -> None:
        """Start audio output thread for playing audio."""
        try:
            if self.is_playing:
                logger.warning(f"[{self.name}] Output thread already running")
                return
            
            logger.info(f"[{self.name}] Starting audio output thread...")
            
            # Open output stream
            self.output_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Start output thread
            self._stop_output_thread.clear()
            self.output_thread = threading.Thread(
                target=self._output_loop,
                daemon=True
            )
            self.output_thread.start()
            
            self.is_playing = True
            
            logger.success(f"[{self.name}] ✓ Audio output thread started")
            
        except Exception as e:
            logger.error(f"[{self.name}] Failed to start output thread: {e}")
            self.increment_error_count()
    
    def _stop_output_thread_func(self) -> None:
        """Stop audio output thread."""
        try:
            if not self.is_playing:
                return
            
            logger.info(f"[{self.name}] Stopping audio output thread...")
            
            # Signal thread to stop
            self._stop_output_thread.set()
            
            # Wait for thread to finish
            if self.output_thread and self.output_thread.is_alive():
                self.output_thread.join(timeout=2.0)
            
            self.is_playing = False
            
            logger.success(f"[{self.name}] ✓ Audio output thread stopped")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error stopping output thread: {e}")
    
    def _output_loop(self) -> None:
        """Output thread loop for playing audio on speakers."""
        logger.info(f"[{self.name}] Output thread started")
        
        try:
            while not self._stop_output_thread.is_set():
                try:
                    # Get audio chunk from queue (with timeout)
                    try:
                        audio_chunk = self.output_queue.get(timeout=0.1)
                        
                        # Play audio chunk
                        self.output_stream.write(audio_chunk)
                        self.output_buffer_count += 1
                        
                    except Empty:
                        # No audio to play, continue
                        continue
                    
                except Exception as e:
                    if not self._stop_output_thread.is_set():
                        logger.error(f"[{self.name}] Output loop error: {e}")
                        self.increment_error_count()
                
        finally:
            logger.info(f"[{self.name}] Output thread stopped")
    
    # Message Bus Handlers
    
    async def _handle_output_audio(self, data: Dict[str, Any]) -> None:
        """
        Handle audio output data from message bus.
        
        Args:
            data: Audio data to play
        """
        try:
            audio_data = data.get("audio_data")
            if not audio_data:
                logger.warning(f"[{self.name}] Received output audio with no data")
                return
            
            audio_format = data.get("format", "pcm_s16le")
            
            # Convert audio format if needed
            if audio_format == "mp3":
                # Would need to decode MP3 to PCM here
                # For now, assume it's already PCM or will be handled elsewhere
                logger.warning(f"[{self.name}] MP3 format not yet supported, skipping")
                return
            
            # Add to output queue
            try:
                self.output_queue.put_nowait(audio_data)
                logger.debug(
                    f"[{self.name}] Added audio to output queue "
                    f"({len(audio_data)} bytes)"
                )
            except:
                # Queue full, drop oldest
                try:
                    self.output_queue.get_nowait()
                    self.output_queue.put_nowait(audio_data)
                except:
                    logger.warning(f"[{self.name}] Output queue full, dropping audio")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error handling output audio: {e}")
            self.increment_error_count()
    
    async def _handle_start_recording(self, data: Dict[str, Any]) -> None:
        """Handle request to start audio recording."""
        try:
            await self._start_input_stream()
            logger.info(f"[{self.name}] Recording started")
        except Exception as e:
            logger.error(f"[{self.name}] Error starting recording: {e}")
    
    async def _handle_stop_recording(self, data: Dict[str, Any]) -> None:
        """Handle request to stop audio recording."""
        try:
            await self._stop_input_stream()
            logger.info(f"[{self.name}] Recording stopped")
        except Exception as e:
            logger.error(f"[{self.name}] Error stopping recording: {e}")
