"""
Main Entry Point - Freya v2.0

Initializes and orchestrates all services.
"""

import asyncio
import signal
from loguru import logger

from src.core.message_bus import MessageBus
from src.core.config import config
from src.services.llm.llm_engine import LLMEngine


class FreyaOrchestrator:
    """Main orchestrator for all Freya services."""
    
    def __init__(self):
        self.message_bus = MessageBus(
            redis_host=config.redis_host,
            redis_port=config.redis_port
        )
        self.services = []
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Initialize all services."""
        logger.info("Initializing Freya v2.0...")
        
        # Connect message bus
        await self.message_bus.connect()
        
        # Initialize services (Phase 1: just LLM for now)
        llm_engine = LLMEngine(self.message_bus)
        await llm_engine.initialize()
        self.services.append(llm_engine)
        
        # TODO: Add other services as they're implemented
        # audio_manager = AudioManager(self.message_bus)
        # stt_service = STTService(self.message_bus)
        # tts_service = TTSService(self.message_bus)
        
        logger.info("All services initialized")
        
    async def start(self) -> None:
        """Start all services."""
        logger.info("Starting Freya v2.0...")
        
        # Start all services
        for service in self.services:
            await service.start()
            
        # Start message bus listener
        bus_task = asyncio.create_task(self.message_bus.start())
        
        logger.info("✨ Freya v2.0 is now running!")
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
        
        # Cancel message bus task
        bus_task.cancel()
        
    async def stop(self) -> None:
        """Stop all services gracefully."""
        logger.info("Shutting down Freya v2.0...")
        
        # Stop all services
        for service in reversed(self.services):
            await service.stop()
            
        # Disconnect message bus
        await self.message_bus.disconnect()
        
        logger.info("Freya v2.0 shut down successfully")
        
    def handle_shutdown(self, sig: signal.Signals) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig.name}, initiating shutdown...")
        self._shutdown_event.set()


async def main() -> None:
    """Main entry point."""
    # Configure logging
    logger.add(
        "logs/freya_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=config.log_level
    )
    
    orchestrator = FreyaOrchestrator()
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: orchestrator.handle_shutdown(s)
        )
    
    try:
        await orchestrator.initialize()
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
