"""
Main Entry Point - Freya v2.0

Initializes and orchestrates all services with proper lifecycle management,
error handling, and graceful shutdown.

Author: MrPink1977
Version: 0.1.0
Date: 2025-12-03
"""

import asyncio
import signal
import sys
from typing import List, Optional
from loguru import logger
from pathlib import Path

from src.core.message_bus import MessageBus, MessageBusError
from src.core.base_service import BaseService, ServiceError
from src.core.config import config
from src.services.llm.llm_engine import LLMEngine
from src.services.mcp_gateway import MCPGateway


class FreyaOrchestrator:
    """
    Main orchestrator for all Freya services.
    
    Manages the lifecycle of all services, handles initialization,
    startup, and graceful shutdown.
    
    Attributes:
        message_bus: Central MessageBus instance
        services: List of all registered services
        _shutdown_event: Async event for coordinating shutdown
        _initialized: Whether orchestrator has been initialized
        
    Example:
        >>> orchestrator = FreyaOrchestrator()
        >>> await orchestrator.initialize()
        >>> await orchestrator.start()
    """
    
    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.message_bus = MessageBus(
            redis_host=config.redis_host,
            redis_port=config.redis_port,
            max_retries=config.redis_max_retries,
            retry_delay=config.redis_retry_delay
        )
        self.services: List[BaseService] = []
        self._shutdown_event = asyncio.Event()
        self._initialized = False
        self._bus_task: Optional[asyncio.Task] = None
        
        logger.info("=" * 70)
        logger.info("Freya v2.0 - Personal AI Assistant")
        logger.info("=" * 70)
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Debug Mode: {config.debug_mode}")
        logger.info(f"Log Level: {config.log_level}")
        logger.info("=" * 70)
        
    async def initialize(self) -> None:
        """
        Initialize all services.
        
        Raises:
            MessageBusError: If message bus fails to connect
            ServiceError: If any service fails to initialize
        """
        try:
            logger.info("🚀 Initializing Freya v2.0...")
            
            # Connect message bus
            logger.info("Connecting to message bus...")
            await self.message_bus.connect()
            logger.success("✓ Message bus connected")
            
            # Initialize services
            logger.info("Initializing services...")

            # Phase 1.5: MCP Gateway (must initialize before LLM Engine)
            if config.mcp_enabled:
                logger.info("  - Initializing MCP Gateway...")
                mcp_gateway = MCPGateway(self.message_bus)
                await mcp_gateway.initialize()
                self.services.append(mcp_gateway)
                logger.success("  ✓ MCP Gateway initialized")
            else:
                logger.warning("  ⚠️  MCP Gateway disabled in configuration")

            # Phase 1: LLM Engine
            logger.info("  - Initializing LLM Engine...")
            llm_engine = LLMEngine(self.message_bus)
            await llm_engine.initialize()
            self.services.append(llm_engine)
            logger.success("  ✓ LLM Engine initialized")

            # TODO Phase 2: Add Audio, STT, TTS services
            # logger.info("  - Initializing Audio Manager...")
            # audio_manager = AudioManager(self.message_bus)
            # await audio_manager.initialize()
            # self.services.append(audio_manager)
            
            # logger.info("  - Initializing STT Service...")
            # stt_service = STTService(self.message_bus)
            # await stt_service.initialize()
            # self.services.append(stt_service)
            
            # logger.info("  - Initializing TTS Service...")
            # tts_service = TTSService(self.message_bus)
            # await tts_service.initialize()
            # self.services.append(tts_service)
            
            # TODO Phase 4: Add Memory Manager
            # logger.info("  - Initializing Memory Manager...")
            # memory_manager = MemoryManager(self.message_bus)
            # await memory_manager.initialize()
            # self.services.append(memory_manager)
            
            # TODO Phase 3: Add MCP Gateway
            # logger.info("  - Initializing MCP Gateway...")
            # mcp_gateway = MCPGateway(self.message_bus)
            # await mcp_gateway.initialize()
            # self.services.append(mcp_gateway)
            
            # TODO Phase 5: Add Vision Service
            # logger.info("  - Initializing Vision Service...")
            # vision_service = VisionService(self.message_bus)
            # await vision_service.initialize()
            # self.services.append(vision_service)
            
            # TODO Phase 6: Add Personality Manager
            # logger.info("  - Initializing Personality Manager...")
            # personality_manager = PersonalityManager(self.message_bus)
            # await personality_manager.initialize()
            # self.services.append(personality_manager)
            
            self._initialized = True
            logger.success(f"✓ All services initialized ({len(self.services)} services)")
            
        except MessageBusError as e:
            logger.error(f"❌ Failed to connect to message bus: {e}")
            logger.error("Please ensure Redis is running and accessible")
            raise
            
        except ServiceError as e:
            logger.error(f"❌ Service initialization failed: {e}")
            raise
            
        except Exception as e:
            logger.exception(f"❌ Unexpected error during initialization: {e}")
            raise
        
    async def start(self) -> None:
        """
        Start all services.
        
        Raises:
            RuntimeError: If orchestrator not initialized
            ServiceError: If any service fails to start
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
            
        try:
            logger.info("🚀 Starting Freya v2.0...")
            
            # Start all services
            for service in self.services:
                logger.info(f"  - Starting {service.name}...")
                await service.start()
                logger.success(f"  ✓ {service.name} started")
                
            # Start message bus listener
            logger.info("Starting message bus listener...")
            self._bus_task = asyncio.create_task(self.message_bus.start())
            logger.success("✓ Message bus listener started")
            
            logger.info("=" * 70)
            logger.success("✨ Freya v2.0 is now running!")
            logger.info("=" * 70)
            logger.info(f"Active services: {len(self.services)}")
            logger.info(f"Redis: {config.redis_host}:{config.redis_port}")
            logger.info(f"Ollama: {config.ollama_host}")
            logger.info(f"Model: {config.ollama_model}")
            logger.info("=" * 70)
            logger.info("Press Ctrl+C to stop")
            logger.info("=" * 70)
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except ServiceError as e:
            logger.error(f"❌ Service startup failed: {e}")
            raise
            
        except Exception as e:
            logger.exception(f"❌ Unexpected error during startup: {e}")
            raise
            
        finally:
            # Cancel message bus task if running
            if self._bus_task and not self._bus_task.done():
                logger.debug("Cancelling message bus task...")
                self._bus_task.cancel()
                try:
                    await self._bus_task
                except asyncio.CancelledError:
                    logger.debug("Message bus task cancelled")
        
    async def stop(self) -> None:
        """
        Stop all services gracefully.
        
        Services are stopped in reverse order of initialization
        to ensure proper cleanup of dependencies.
        """
        logger.info("=" * 70)
        logger.info("🛑 Shutting down Freya v2.0...")
        logger.info("=" * 70)
        
        # Stop message bus listener
        if self.message_bus.is_running():
            logger.info("Stopping message bus listener...")
            await self.message_bus.stop()
            logger.success("✓ Message bus listener stopped")
        
        # Stop all services in reverse order
        for service in reversed(self.services):
            try:
                logger.info(f"  - Stopping {service.name}...")
                await service.stop()
                logger.success(f"  ✓ {service.name} stopped")
            except Exception as e:
                logger.error(f"  ❌ Error stopping {service.name}: {e}")
                # Continue stopping other services
                
        # Disconnect message bus
        if self.message_bus.is_connected():
            logger.info("Disconnecting from message bus...")
            await self.message_bus.disconnect()
            logger.success("✓ Message bus disconnected")
        
        logger.info("=" * 70)
        logger.success("✓ Freya v2.0 shut down successfully")
        logger.info("=" * 70)
        
    def handle_shutdown(self, sig: signal.Signals) -> None:
        """
        Handle shutdown signals (SIGTERM, SIGINT).
        
        Args:
            sig: The signal that triggered shutdown
        """
        logger.info("=" * 70)
        logger.warning(f"⚠️  Received signal {sig.name} ({sig.value})")
        logger.info("Initiating graceful shutdown...")
        logger.info("=" * 70)
        self._shutdown_event.set()
        
    async def health_check_loop(self) -> None:
        """
        Periodically check health of all services.
        
        This runs in the background and logs warnings if services
        become unhealthy.
        """
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                unhealthy_services = []
                for service in self.services:
                    if not await service.health_check():
                        unhealthy_services.append(service.name)
                        
                if unhealthy_services:
                    logger.warning(
                        f"⚠️  Unhealthy services detected: {', '.join(unhealthy_services)}"
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")


def configure_logging() -> None:
    """
    Configure Loguru logging with proper formatting and rotation.
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stderr,
        format=config.log_format,
        level=config.log_level,
        colorize=True
    )
    
    # Add file handler with rotation
    log_file = config.log_dir / "freya_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        format=config.log_format,
        level=config.log_level,
        rotation=config.log_rotation,
        retention=config.log_retention,
        compression="zip",
        enqueue=True  # Thread-safe
    )
    
    logger.info(f"Logging configured: level={config.log_level}, dir={config.log_dir}")


async def main() -> None:
    """
    Main entry point for Freya v2.0.
    
    Handles initialization, startup, and graceful shutdown.
    """
    # Configure logging first
    configure_logging()
    
    orchestrator = FreyaOrchestrator()
    
    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: orchestrator.handle_shutdown(s)
        )
    
    # Start health check loop
    health_task = asyncio.create_task(orchestrator.health_check_loop())
    
    try:
        await orchestrator.initialize()
        await orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        
    except MessageBusError as e:
        logger.error(f"Message bus error: {e}")
        logger.error("Please check your Redis configuration and ensure Redis is running")
        sys.exit(1)
        
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
        
    finally:
        # Cancel health check
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass
            
        # Graceful shutdown
        await orchestrator.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)
