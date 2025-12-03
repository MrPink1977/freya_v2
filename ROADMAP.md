# Freya v2.0 - Implementation Roadmap (MCP-First Architecture)

**Date:** December 3, 2025  
**Author:** Manus AI  
**Version:** 2.0 - **REVISED FOR MCP-FIRST ARCHITECTURE**  
**Status:** 🔥 **Active - MCP-First Approach**

---

## 🎯 Architectural Decision

**Decision Date**: December 3, 2025  
**Decision**: **Full MCP-First Architecture**

Freya v2.0 is fundamentally built around the Model Context Protocol (MCP). The MCP Gateway is **core infrastructure**, not an enhancement. All external services and tools integrate through MCP from day 1.

**Rationale**:
- Freya is "rebuilt for MCP" - this should be reflected in the implementation order
- MCP Gateway enables tool usage, which makes Freya useful
- Building MCP early avoids technical debt and rework
- Aligns with architecture document's vision
- Prioritizes quality and correctness over speed

---

## 1. Guiding Principles

This roadmap is designed around a philosophy of incremental delivery and leveraging best-in-class open-source components. We will build the system in distinct, testable phases, ensuring a functional core at every step.

- **Build, Don't Reinvent**: We will write code for Freya's unique personality and the orchestration of services. We will *not* write our own memory system, tool servers, or low-level protocols.
- **MCP-First**: The MCP Gateway is foundational infrastructure, built early to enable tool usage from the start.
- **Service-Oriented**: Each component is an independent service, communicating via a central message bus. This allows for parallel development and easy upgrades.
- **Local First, Cloud Second**: Core processing remains local for privacy and reliability. Cloud services are used strategically for quality enhancement (e.g., TTS via ElevenLabs MCP).

---

## 2. Core Technology Stack

This stack is chosen for its robust community support, performance, and suitability for AI applications.

| Component | Technology | Justification | Local/Cloud |
| :--- | :--- | :--- | :--- |
| **Programming Language** | Python 3.11+ | The standard for AI/ML development with a rich ecosystem. | Local |
| **Core Framework** | `asyncio` | Essential for building high-performance, concurrent I/O-bound services. | Local |
| **Containerization** | Docker & Docker Compose | Simplifies setup, deployment, and management of all microservices. | Local |
| **Message Bus** | Redis (Pub/Sub) | A fast, reliable, and industry-standard message broker for decoupling services. | Local |
| **Web Server (GUI Backend)** | FastAPI | High-performance Python web framework with automatic data validation and docs. | Local |
| **Web GUI Frontend** | React or Svelte | Modern, component-based frameworks for building dynamic user interfaces. | Local |
| **LLM Engine** | Ollama | The easiest way to run and manage local LLMs on your GPU. | Local |
| **Speech-to-Text (STT)** | `faster-whisper` | State-of-the-art accuracy for local transcription with GPU support. | Local |
| **Text-to-Speech (TTS)** | ElevenLabs MCP Server | Highest quality voice output via MCP. | Cloud (via MCP) |
| **Wake Word Detection** | `pvporcupine` | Highly accurate and computationally efficient wake word engine. | Local |
| **Vector Database** | ChromaDB | Open-source, purpose-built vector database for AI memory and search. | Local |
| **Memory System** | Adaptive Memory v3 (logic) | A proven, feature-rich memory system from the OpenWebUI community. | Local |
| **Tool Protocol** | `mcp` Python SDK | The official, standard way to integrate tools and external services. | Local |
| **Tool Gateway** | MetaMCP or MCPX | Aggregates hundreds of MCP servers into a single, manageable endpoint. | Local |
| **Vision Processing** | OpenCV & `ultralytics` (YOLO) | Industry standards for real-time computer vision and object detection. | Local |

**Key Point**: Most MCP servers run **locally**! Only services like ElevenLabs TTS and web search APIs are cloud-based.

---

## 3. Phased Implementation Roadmap (REVISED)

This 12-week plan is designed to deliver a functional and increasingly capable system at the end of each phase.

### Phase 1: The Foundation (Weeks 1-2) ✅ COMPLETE

**Goal**: Establish the core infrastructure and basic LLM conversation capability.

- **Tasks**:
    1.  ✅ **Setup Docker Compose**: Create `docker-compose.yml` to manage containers for Redis, Ollama, and the main Python application.
    2.  ✅ **Implement Message Bus**: Create a `MessageBus` class that connects to Redis for pub/sub.
    3.  ✅ **Build LLM Engine**: Create initial version of the `LLMEngine` service.
    4.  ✅ **Establish Core Services**: Implement `BaseService` pattern and configuration management.
    5.  ✅ **Code Quality Standards**: Implement production-grade error handling, logging, type hints, and documentation.

- **Outcome**: Core infrastructure is in place. LLM Engine can process text and generate responses via message bus.

**Status**: ✅ **COMPLETE** (December 3, 2025)

---

### Phase 1.5: MCP Gateway & Tool Ecosystem (Weeks 3-4) 🔥 NEXT

**Goal**: Build the MCP Gateway to enable tool usage. This makes Freya actually useful, not just a chatbot.

- **Tasks**:
    1.  **Deploy MCP Gateway Service**: Create `MCPGateway` service using the official `mcp` Python SDK.
    2.  **Integrate with LLM Engine**: Add tool calling capability to `LLMEngine` (function calling, tool discovery).
    3.  **Connect Essential MCP Servers**: Configure and test 5-7 core MCP servers:
        - **Filesystem MCP** (local file access) - LOCAL
        - **Brave Search MCP** (web search) - CLOUD API
        - **Weather MCP** (weather data) - CLOUD API
        - **Shell MCP** (system commands) - LOCAL
        - **Time/Date MCP** (current time) - LOCAL
        - **Calculator MCP** (math operations) - LOCAL
        - **ElevenLabs MCP** (for future TTS) - CLOUD API
    4.  **Implement Tool Discovery**: Auto-discover available tools from connected MCP servers.
    5.  **Add Tool Execution**: Route tool calls from LLM to appropriate MCP server and return results.
    6.  **Update System Prompt**: Make LLM aware of available tools and how to use them.
    7.  **Testing**: Verify LLM can successfully call tools (e.g., "What's the weather?", "Search the web for...").

- **Outcome**: Freya can now perform useful tasks like searching the web, accessing files, checking weather, and executing system commands. The tool ecosystem is in place and extensible.

**Estimated Time**: 1-2 weeks (8-12 hours of focused work)

**Status**: 📋 **PLANNED** - Ready for implementation

---

### Phase 2: Audio Pipeline (Weeks 5-6)

**Goal**: Enable voice interaction. Freya can listen, speak, and converse using voice in a single room.

- **Tasks**:
    1.  **Build STT Service**: Create `STTService` using `faster-whisper` for local, GPU-accelerated transcription.
    2.  **Build TTS Service**: Create `TTSService` that uses **ElevenLabs MCP server** (not direct SDK).
    3.  **Build Audio Manager**: Create single-room `AudioManager` to route audio streams.
    4.  **Establish Voice Loop**: Wire services together: Audio → STT → LLM → TTS → Audio.
    5.  **Testing**: Verify voice conversation works end-to-end.

- **Outcome**: Freya can listen and respond via voice in one room. Full voice conversation loop is functional with tool access.

**Estimated Time**: 1-2 weeks

---

### Phase 3: Multi-Room & Location Awareness (Weeks 7-8)

**Goal**: Enable Freya to listen and respond in multiple rooms, aware of which location is active.

- **Tasks**:
    1.  **Refactor AudioManager**: Update the service to handle audio streams from multiple, named endpoints (e.g., `bedroom`, `front_door`).
    2.  **Integrate Wake Word**: Add `pvporcupine` to each endpoint's client-side script to detect the wake word locally before streaming audio.
    3.  **Implement Session Logic**: Create the "active endpoint" logic. When a wake word is detected, that endpoint becomes the session owner, and others are temporarily ignored.
    4.  **Add Conversation Window**: Implement the "continued conversation" logic to avoid repeated wake words.
    5.  **Update GUI**: The dashboard now shows the status of all endpoints and highlights the currently active one.

- **Outcome**: Freya is now a location-aware assistant. You can start a conversation in the bedroom or at the front door, and she responds in the correct location.

**Estimated Time**: 1-2 weeks

---

### Phase 4: Intelligent Memory (Weeks 9-10)

**Goal**: Upgrade Freya's memory from simple context to a persistent, intelligent system.

- **Tasks**:
    1.  **Deploy ChromaDB**: Add a ChromaDB container to the Docker Compose setup.
    2.  **Build MemoryManager**: Create the `MemoryManager` service and integrate the core logic from the **Adaptive Memory v3** component.
    3.  **Connect to LLM**: Modify the `LLMEngine` to query the `MemoryManager` for relevant context before generating a response and to send conversation history for memory extraction.
    4.  **Develop Memory GUI**: Add a "Memory" tab to the dashboard, allowing you to view, search, and manage Freya's long-term memories.

- **Outcome**: Freya now remembers past conversations, user preferences, and key facts, leading to highly personalized and context-aware interactions.

**Estimated Time**: 1-2 weeks

---

### Phase 5: Vision (Weeks 11-12)

**Goal**: Enable proactive capabilities based on visual input from the front door camera.

- **Tasks**:
    1.  **Create VisionService**: Build the service to process the video stream from the front door endpoint.
    2.  **Integrate Object Detection**: Use OpenCV and a pre-trained YOLO model to detect common objects like "person" and "car".
    3.  **Implement Visual Alerts**: When a relevant object is detected, the `VisionService` publishes an alert to the Message Bus (e.g., `vision.alert: {location: 'front_door', object: 'person_detected'}`).
    4.  **Connect to LLM**: The `LLMEngine` subscribes to these alerts and can initiate a proactive response (e.g., "By the way, there is someone at the front door.").
    5.  **Add Facial Recognition (Optional)**: Integrate a facial recognition model to identify known individuals.

- **Outcome**: Freya can now see and react to events at the front door, providing proactive alerts and context-aware responses.

**Estimated Time**: 1-2 weeks

---

### Phase 6: Personality & Polish (Week 12+)

**Goal**: Add Freya's unique personality and polish the user experience.

- **Tasks**:
    1.  **Build PersonalityManager**: Create service to inject personality into LLM responses.
    2.  **Develop Personality Profiles**: Create witty, sarcastic, professional personality modes.
    3.  **Context-Aware Personality**: Adjust tone based on conversation context.
    4.  **Enhance GUI**: Add "thoughts" window, tool call visualization, comprehensive logging.
    5.  **Performance Optimization**: Tune services for latency and resource usage.
    6.  **Documentation**: Complete user manual and deployment guide.

- **Outcome**: Freya has her unique personality, the GUI is polished, and the system is production-ready.

**Estimated Time**: 1+ weeks

---

## 4. Key Differences from Original Roadmap

### What Changed:

| Original | Revised (MCP-First) | Reason |
|----------|---------------------|--------|
| Phase 2: Multi-room audio | Phase 1.5: MCP Gateway | MCP is foundational, not optional |
| Phase 3: MCP Gateway | Phase 2: Audio Pipeline | Audio depends on having tools available |
| TTS: Direct SDK | TTS: ElevenLabs MCP | Consistent MCP architecture |
| Tools in Week 5-6 | Tools in Week 3-4 | Earlier access to useful functionality |

### Why This is Better:

1. **Freya is useful earlier** - Week 3-4 instead of Week 5-6
2. **No rework needed** - TTS uses MCP from day 1
3. **True to vision** - "Rebuilt for MCP" is reflected in implementation
4. **Better architecture** - MCP is infrastructure, not an add-on
5. **Extensible from start** - Adding new tools is just configuration

---

## 5. Local vs. Cloud MCP Servers

### 🏠 Local MCP Servers (Most of them!)

These run on your machine, no internet required:

- **Filesystem MCP** - Browse and manipulate local files
- **Shell MCP** - Execute system commands
- **Time/Date MCP** - Current time and date
- **Calculator MCP** - Math operations
- **SQLite MCP** - Local database access
- **Git MCP** - Git repository operations
- **Docker MCP** - Container management
- **Spotify MCP** (local control) - Control Spotify client
- **Home Assistant MCP** (future) - Smart home control via local HA instance
- **And 300+ more local servers...**

### ☁️ Cloud MCP Servers (Only when needed)

These require internet and API keys:

- **ElevenLabs MCP** - High-quality text-to-speech
- **Brave Search MCP** - Web search
- **Weather MCP** - Weather data APIs
- **Google Calendar MCP** - Calendar integration
- **Email MCP** - Email access
- **And ~100 cloud-based servers...**

### 🔒 Privacy-First Approach

- **Default**: Use local MCP servers whenever possible
- **Cloud services**: Only for capabilities that require it (TTS quality, web search)
- **Configurable**: Can disable cloud services and use local fallbacks
- **API keys**: Stored locally, never shared

**Bottom line**: ~75% of MCP servers are fully local! Only specific services like TTS and web search need cloud access.

---

## 6. Next Steps

### Immediate (Phase 1.5):
1. ✅ Update roadmap to reflect MCP-first architecture
2. 📋 Create PHASE_1.5_PLAN_MCP.md (detailed implementation plan)
3. 🔨 Implement MCP Gateway service
4. 🔌 Connect 5-7 essential MCP servers
5. ✅ Test tool calling from LLM

### After Phase 1.5:
1. Implement STT Service (local, faster-whisper)
2. Implement TTS Service (via ElevenLabs MCP)
3. Build Audio Manager
4. Continue with remaining phases

---

## 7. Success Metrics

### Phase 1.5 Success Criteria:
- [ ] MCP Gateway service running and healthy
- [ ] LLM Engine can discover available tools
- [ ] LLM can successfully call tools via MCP
- [ ] At least 5 MCP servers connected and functional
- [ ] User can ask "What's the weather?" and get a real answer
- [ ] User can ask "Search the web for..." and get results
- [ ] Tool calls are logged and visible in GUI (future)

---

**Status**: Phase 1 complete, Phase 1.5 (MCP Gateway) is next! 🚀

**Last Updated**: December 3, 2025
