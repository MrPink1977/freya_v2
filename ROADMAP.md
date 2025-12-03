# Freya v2.0 - Implementation Roadmap & Technology Stack

**Date:** December 3, 2025  
**Author:** Manus AI  
**Version:** 1.0

## 1. Guiding Principles

This roadmap is designed around a philosophy of incremental delivery and leveraging best-in-class open-source components. We will build the system in distinct, testable phases, ensuring a functional core at every step.

- **Build, Don't Reinvent**: We will write code for Freya's unique personality and the orchestration of services. We will *not* write our own memory system, tool servers, or low-level protocols.
- **Service-Oriented**: Each component is an independent service, communicating via a central message bus. This allows for parallel development and easy upgrades.
- **Local First, Cloud Second**: Core processing remains local for privacy and reliability. Cloud services are used strategically for quality enhancement (e.g., TTS).

## 2. Core Technology Stack

This stack is chosen for its robust community support, performance, and suitability for AI applications.

| Component | Technology | Justification |
| :--- | :--- | :--- |
| **Programming Language** | Python 3.11+ | The standard for AI/ML development with a rich ecosystem. |
| **Core Framework** | `asyncio` | Essential for building high-performance, concurrent I/O-bound services. |
| **Containerization** | Docker & Docker Compose | Simplifies setup, deployment, and management of all microservices. |
| **Message Bus** | Redis (Pub/Sub) | A fast, reliable, and industry-standard message broker for decoupling services. |
| **Web Server (GUI Backend)** | FastAPI | High-performance Python web framework with automatic data validation and docs. |
| **Web GUI Frontend** | React or Svelte | Modern, component-based frameworks for building dynamic user interfaces. |
| **LLM Engine** | Ollama | The easiest way to run and manage local LLMs on your GPU. |
| **Speech-to-Text (STT)** | `faster-whisper` | State-of-the-art accuracy for local transcription with GPU support. |
| **Text-to-Speech (TTS)** | `elevenlabs` Python SDK | Provides the highest quality and most natural-sounding voice output. |
| **Wake Word Detection** | `pvporcupine` | Highly accurate and computationally efficient wake word engine. |
| **Vector Database** | ChromaDB | Open-source, purpose-built vector database for AI memory and search. |
| **Memory System** | Adaptive Memory v3 (logic) | A proven, feature-rich memory system from the OpenWebUI community. |
| **Tool Protocol** | `mcp` Python SDK | The official, standard way to integrate tools and external services. |
| **Tool Gateway** | MetaMCP or MCPX | Aggregates hundreds of MCP servers into a single, manageable endpoint. |
| **Vision Processing** | OpenCV & `ultralytics` (YOLO) | Industry standards for real-time computer vision and object detection. |

## 3. Phased Implementation Roadmap

This 12-week plan is designed to deliver a functional and increasingly capable system at the end of each phase.

### Phase 1: The Foundation (Weeks 1-2)

**Goal**: Establish a working, single-room conversation loop. A user can speak, and Freya responds. No memory, no advanced tools, no location awareness yet.

- **Tasks**:
    1.  **Setup Docker Compose**: Create `docker-compose.yml` to manage containers for Redis, Ollama, and the main Python application.
    2.  **Implement Message Bus**: Create a `MessageBus` class that connects to Redis for pub/sub.
    3.  **Build Core Services**: Create initial versions of the `LLMEngine`, `STTService`, `TTSService`, and a single-endpoint `AudioManager`.
    4.  **Establish Basic Loop**: Wire the services together via the message bus: Audio -> STT -> LLM -> TTS -> Audio.
    5.  **Develop Minimal GUI**: Create a simple FastAPI backend and a React/Svelte frontend that displays the conversation and basic status lights.

- **Outcome**: A user can talk to Freya in one room. The GUI shows the conversation. The core infrastructure is in place.

### Phase 2: Multi-Room & Location Awareness (Weeks 3-4)

**Goal**: Enable Freya to listen and respond in multiple rooms, aware of which location is active.

- **Tasks**:
    1.  **Refactor AudioManager**: Update the service to handle audio streams from multiple, named endpoints (e.g., `bedroom`, `front_door`).
    2.  **Integrate Wake Word**: Add `pvporcupine` to each endpoint's client-side script to detect the wake word locally before streaming audio.
    3.  **Implement Session Logic**: Create the "active endpoint" logic. When a wake word is detected, that endpoint becomes the session owner, and others are temporarily ignored.
    4.  **Add Conversation Window**: Implement the "continued conversation" logic to avoid repeated wake words.
    5.  **Update GUI**: The dashboard now shows the status of all endpoints and highlights the currently active one.

- **Outcome**: Freya is now a location-aware assistant. You can start a conversation in the bedroom or at the front door, and she responds in the correct location.

### Phase 3: The Tool Ecosystem (Weeks 5-6)

**Goal**: Give Freya the ability to interact with the outside world through a robust and scalable tool system.

- **Tasks**:
    1.  **Deploy MCP Gateway**: Set up the `MCPGateway` service using MetaMCP or a similar aggregator.
    2.  **Integrate MCP SDK**: Add the official `mcp` Python SDK to the `LLMEngine`.
    3.  **Connect Core Tools**: Configure the gateway to connect to 3-5 essential, pre-built MCP servers (e.g., Filesystem, Web Search, Shell).
    4.  **Update LLM Prompt**: Modify the system prompt to make the LLM aware of the available tools and how to use them.
    5.  **Enhance GUI**: Add a "Tool Calls" panel to the logging window to show which tools are being executed.

- **Outcome**: Freya can now perform useful tasks like searching the web, reading local files, and providing weather updates.

### Phase 4: Intelligent Memory (Weeks 7-8)

**Goal**: Upgrade Freya's memory from simple context to a persistent, intelligent system.

- **Tasks**:
    1.  **Deploy ChromaDB**: Add a ChromaDB container to the Docker Compose setup.
    2.  **Build MemoryManager**: Create the `MemoryManager` service and integrate the core logic from the **Adaptive Memory v3** component.
    3.  **Connect to LLM**: Modify the `LLMEngine` to query the `MemoryManager` for relevant context before generating a response and to send conversation history for memory extraction.
    4.  **Develop Memory GUI**: Add a "Memory" tab to the dashboard, allowing you to view, search, and manage Freya's long-term memories.

- **Outcome**: Freya now remembers past conversations, user preferences, and key facts, leading to highly personalized and context-aware interactions.

### Phase 5: Vision (Weeks 9-10)

**Goal**: Enable proactive capabilities based on visual input from the front door camera.

- **Tasks**:
    1.  **Create VisionService**: Build the service to process the video stream from the front door endpoint.
    2.  **Integrate Object Detection**: Use OpenCV and a pre-trained YOLO model to detect common objects like "person" and "car".
    3.  **Implement Visual Alerts**: When a relevant object is detected, the `VisionService` publishes an alert to the Message Bus (e.g., `vision.alert: {location: 'front_door', object: 'person_detected'}`).
    4.  **Connect to LLM**: The `LLMEngine` subscribes to these alerts and can initiate a proactive response (e.g., "By the way, there is someone at the front door.").

- **Outcome**: Freya is no longer just reactive; she can now perceive her environment and provide unsolicited, helpful information.

### Phase 6: Polish & Personality (Weeks 11-12)

**Goal**: Refine all systems, enhance the user experience, and solidify Freya's unique character.

- **Tasks**:
    1.  **Implement PersonalityManager**: Create the service that intercepts the LLM's factual response and applies the witty/sarcastic/serious tone based on context.
    2.  **Tune All Models**: Fine-tune thresholds for wake word, STT confidence, and object detection to minimize errors.
    3.  **Enhance GUI**: Build out the full dashboard with all planned features, including the "Freya's Thoughts" window and comprehensive settings panels.
    4.  **Performance Optimization**: Profile the system to identify and eliminate bottlenecks.
    5.  **Write Documentation**: Create a user manual and developer documentation for the completed system.

- **Outcome**: A polished, stable, and highly capable personal AI assistant that is a joy to interact with and easy to manage.
