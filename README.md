# Freya v2.0

> A location-aware, multi-room personal AI assistant with persistent memory and MCP integration

[![GitHub](https://img.shields.io/badge/GitHub-MrPink1977%2Ffreya__v2-blue?logo=github)](https://github.com/MrPink1977/freya_v2)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)

---

## 🎯 What is Freya?

Freya is a next-generation personal AI assistant designed for the modern home. She's witty, intelligent, and genuinely helpful—capable of holding natural conversations across multiple rooms, remembering your preferences, and taking action on your behalf.

Unlike cloud-dependent assistants that compromise your privacy, Freya runs primarily on your own hardware, giving you complete control over your data while delivering a superior, personalized experience.

## ✨ Key Features

- **🏠 Multi-Room Audio**: Bedroom and front door endpoints, with easy expansion
- **📍 Location Awareness**: Knows where you are and responds accordingly
- **🧠 Intelligent Memory**: Persistent memory system that learns your preferences over time
- **🔧 400+ Tools**: Extensible tool ecosystem via Model Context Protocol (MCP)
- **👁️ Vision Capabilities**: Motion and object detection at the front door
- **🎭 Adaptive Personality**: Witty, sarcastic, and context-aware
- **🖥️ Real-Time Dashboard**: Comprehensive web GUI for monitoring and control
- **🔒 Privacy-First**: Core processing runs locally on your hardware

## 🏗️ Architecture

Freya is built on a service-oriented architecture with a Redis message bus connecting independent microservices:

![Architecture Diagram](architecture.png)

### Core Components

- **Audio Manager**: Multi-endpoint audio routing with location awareness
- **LLM Engine**: Local model inference (Llama 3.2) on RTX 5060 Ti
- **Memory Manager**: Adaptive Memory v3 with ChromaDB vector storage
- **MCP Gateway**: Universal tool integration via MetaMCP/MCPX
- **Vision Service**: OpenCV + YOLO for real-time object detection
- **Web Dashboard**: React/Svelte frontend with FastAPI backend

## 📚 Documentation

This repository contains the complete design specifications for Freya v2.0:

- **[Executive Summary](EXECUTIVE_SUMMARY.md)** - High-level vision and key differentiators
- **[Requirements](REQUIREMENTS.md)** - Detailed functional and technical requirements
- **[Architecture](ARCHITECTURE.md)** - System design and component breakdown
- **[Roadmap](ROADMAP.md)** - 12-week implementation plan and technology stack

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- NVIDIA GPU (RTX 5060 Ti or similar)
- CUDA 12.0+

### Installation

```bash
# Clone the repository
git clone https://github.com/MrPink1977/freya_v2.git
cd freya_v2

# Set up the environment (coming in Phase 1)
# docker-compose up -d
```

## 🗓️ Development Roadmap

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| **Phase 1** | Weeks 1-2 | Foundation - single-room conversation loop |
| **Phase 2** | Weeks 3-4 | Multi-room with location awareness |
| **Phase 3** | Weeks 5-6 | Tool ecosystem integration |
| **Phase 4** | Weeks 7-8 | Intelligent, persistent memory |
| **Phase 5** | Weeks 9-10 | Vision capabilities |
| **Phase 6** | Weeks 11-12 | Polish, personality, and full dashboard |

See the [full roadmap](ROADMAP.md) for detailed task breakdowns.

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **LLM** | Ollama (Llama 3.2) |
| **STT** | faster-whisper |
| **TTS** | ElevenLabs |
| **Wake Word** | Porcupine |
| **Memory** | Adaptive Memory v3 + ChromaDB |
| **Tools** | MCP Python SDK + MetaMCP |
| **Vision** | OpenCV + YOLO |
| **Message Bus** | Redis Pub/Sub |
| **Web Framework** | FastAPI + React/Svelte |
| **Containerization** | Docker Compose |

## 🤝 Contributing

This is a personal project, but contributions, suggestions, and feedback are welcome! Please open an issue to discuss major changes.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Adaptive Memory v3** - Memory system from the OpenWebUI community
- **Model Context Protocol** - Tool integration standard by Anthropic
- **awesome-mcp-servers** - 400+ pre-built MCP servers

## 📞 Contact

- GitHub: [@MrPink1977](https://github.com/MrPink1977)
- Project: [freya_v2](https://github.com/MrPink1977/freya_v2)

---

**Status**: 🚧 Phase 2 In Progress - STT Service Implemented!
