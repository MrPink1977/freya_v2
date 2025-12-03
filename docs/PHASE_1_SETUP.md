# Phase 1 Setup Guide - Freya v2.0

This guide will walk you through setting up the Phase 1 foundation of Freya v2.0.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Docker & Docker Compose**
   - Docker Engine 20.10+
   - Docker Compose 2.0+
   - NVIDIA Container Toolkit (for GPU support)

2. **Git**
   - For cloning and managing the repository

3. **Hardware**
   - NVIDIA GPU (RTX 5060 Ti or similar)
   - At least 16GB RAM
   - 50GB free disk space

## Step 1: Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/MrPink1977/freya_v2.git
cd freya_v2
```

## Step 2: Configure Environment Variables

Copy the example environment file and edit it with your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys:

```bash
# Required for Phase 1
ELEVENLABS_API_KEY=your_actual_elevenlabs_key_here
PORCUPINE_ACCESS_KEY=your_actual_porcupine_key_here

# Optional: Adjust these if needed
OLLAMA_MODEL=llama3.2:latest
LOG_LEVEL=INFO
```

### Getting API Keys

- **ElevenLabs**: Sign up at [elevenlabs.io](https://elevenlabs.io) and get your API key from the dashboard
- **Porcupine**: Sign up at [picovoice.ai](https://picovoice.ai) and get your access key

## Step 3: Verify NVIDIA Docker Support

Ensure your system can use the GPU with Docker:

```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

You should see your GPU information. If this fails, install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

## Step 4: Build and Start Services

Build the Docker images and start all services:

```bash
docker-compose up -d
```

This will:
- Start Redis (message bus)
- Start Ollama (LLM server)
- Start ChromaDB (vector database)
- Build and start the Freya core application

## Step 5: Pull the LLM Model

The first time you run Freya, Ollama needs to download the LLM model. This happens automatically, but you can also do it manually:

```bash
docker exec -it freya-ollama ollama pull llama3.2:latest
```

This may take 10-20 minutes depending on your internet connection.

## Step 6: Check Service Status

View the logs to ensure everything is running:

```bash
# View all logs
docker-compose logs -f

# View just Freya core logs
docker-compose logs -f freya-core

# Check Redis
docker-compose logs redis

# Check Ollama
docker-compose logs ollama
```

You should see messages indicating:
- ✅ Connected to Redis
- ✅ LLM Engine initialized
- ✅ Freya v2.0 is now running!

## Step 7: Test the Message Bus

You can test the message bus with Redis CLI:

```bash
# Connect to Redis
docker exec -it freya-redis redis-cli

# Subscribe to all channels (in Redis CLI)
PSUBSCRIBE *

# In another terminal, publish a test message
docker exec -it freya-redis redis-cli PUBLISH test.channel '{"message": "hello"}'
```

## Phase 1 Status

At this point, you have:

✅ **Infrastructure Running**
- Redis message bus
- Ollama LLM server
- ChromaDB vector database
- Freya core application

✅ **Services Initialized**
- LLM Engine (basic conversation capability)
- Message bus integration
- Configuration management

⏳ **Not Yet Implemented** (coming in later phases)
- Audio input/output
- Speech-to-Text (STT)
- Text-to-Speech (TTS)
- Multi-room endpoints
- Memory system
- Tool integration
- Vision capabilities
- Web GUI

## Next Steps

Phase 1 establishes the foundation. The next phases will add:

- **Phase 2**: Multi-room audio and location awareness
- **Phase 3**: Tool ecosystem (web search, files, etc.)
- **Phase 4**: Intelligent memory
- **Phase 5**: Vision capabilities
- **Phase 6**: Polish and full GUI

## Troubleshooting

### Docker Compose Fails to Start

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs
```

### GPU Not Detected

```bash
# Verify NVIDIA drivers
nvidia-smi

# Verify Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Redis Connection Errors

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec -it freya-redis redis-cli ping
```

### Ollama Model Download Fails

```bash
# Check Ollama logs
docker-compose logs ollama

# Manually pull model
docker exec -it freya-ollama ollama pull llama3.2:latest
```

## Stopping Freya

To stop all services:

```bash
docker-compose down
```

To stop and remove all data (fresh start):

```bash
docker-compose down -v
```

## Development Mode

For development, you can run services individually:

```bash
# Start just infrastructure
docker-compose up -d redis ollama chromadb

# Run Freya core locally (outside Docker)
python -m src.main
```

This allows you to edit code and restart quickly without rebuilding Docker images.

---

**Need Help?** Open an issue on GitHub: https://github.com/MrPink1977/freya_v2/issues
