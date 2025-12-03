""
# Freya v2.0 - System Architecture

**Date:** December 3, 2025  
**Author:** Manus AI  
**Version:** 1.0

## 1. Introduction

This document provides a comprehensive overview of the system architecture for Freya v2.0, a location-aware, multi-room personal AI assistant. The design prioritizes modularity, scalability, and a local-first processing approach, while strategically leveraging cloud services for enhanced capabilities. The architecture is built around a central message bus, enabling decoupled services that can be developed, deployed, and scaled independently.

## 2. High-Level Architecture

The architecture is composed of several distinct layers: Endpoints, Core Services, Communication, Data, and External Services. A central Message Bus orchestrates the flow of information between these components, ensuring a clean separation of concerns.

![Freya v2.0 System Architecture](/home/ubuntu/freya_v2/architecture.png)

*Figure 1: A high-level diagram illustrating the components and data flows within the Freya v2.0 ecosystem.*

## 3. Component Breakdown

### 3.1. Endpoints

Endpoints are the physical interfaces for user interaction. Each endpoint is a "dumb" client responsible only for capturing and rendering audio/video streams. All processing happens on the central server.

- **Bedroom Endpoint**: A simple microphone and speaker setup.
- **Front Door Endpoint**: A more complex setup including a microphone, speaker, and camera.

### 3.2. Core Services

These are the brains of the operation, running as independent services on the main server.

- **Audio Manager**: Manages all audio streams. It receives raw audio from endpoints, routes it for STT, and directs TTS output to the correct location-aware endpoint. It is responsible for activating and deactivating endpoints to ensure only one is active during a conversation.

- **Vision Service**: Processes video streams from camera-enabled endpoints. It performs motion and object detection (e.g., "a person is at the door," "a car is pulling in") and will be the foundation for future facial recognition capabilities. Alerts are published to the Message Bus.

- **STT (Speech-to-Text) Service**: Transcribes raw audio into text. It will use a local, GPU-accelerated model like `faster-whisper` for high accuracy and privacy.

- **TTS (Text-to-Speech) Service**: Converts text responses into natural-sounding speech. It will primarily use the high-quality **ElevenLabs** cloud service, with a local model (like Piper) as a fallback to ensure availability.

- **LLM Engine**: The core reasoning component. It runs a powerful local model (e.g., Llama 3.2) on the RTX 5060 Ti via a framework like Ollama or vLLM. It receives text, queries other services for context (memory, tools), and generates responses.

- **Memory Manager**: Implements the long-term and short-term memory capabilities. This will be built by integrating the proven **Adaptive Memory v3** logic, which provides sophisticated, LLM-powered memory extraction, clustering, and summarization, all stored in a local ChromaDB instance.

- **Personality Manager**: Injects Freya's unique personality into the final response. It receives the LLM's raw, factual response and adjusts the tone and phrasing to be witty, sarcastic, or serious, depending on the context of the conversation.

- **MCP Gateway**: Acts as the universal translator for all tools. It uses an aggregator like **MetaMCP** or **MCPX** to manage connections to a vast ecosystem of pre-built MCP servers. This component makes the system incredibly extensible, as adding new tools is a matter of configuration, not code.

### 3.3. Communication Layer

- **Message Bus (Redis Pub/Sub)**: The central nervous system of the architecture. All services communicate by publishing and subscribing to events on the bus. This decouples the services, allowing them to be developed and managed independently.

- **Web Server (FastAPI)**: Provides the API backend for the Web Dashboard GUI. It communicates with the Message Bus via WebSockets to provide real-time updates and receive user commands.

### 3.4. Data Layer

- **Vector DB (ChromaDB)**: The persistent storage for the Memory Manager. It stores embeddings of conversations and memories, enabling efficient semantic search.

- **Config & Logs DB**: A simple database (e.g., SQLite or file-based) to store system configuration, endpoint settings, and detailed logs from all services for debugging and monitoring via the GUI.

### 3.5. External Services (via MCP)

This layer represents the vast ecosystem of tools Freya can use. Instead of building these from scratch, we will integrate existing, production-ready MCP servers.

- **File System MCP**: For local file browsing and manipulation.
- **Web Search MCP**: For internet queries (e.g., Brave Search).
- **Spotify MCP**: For music control.
- **Home Assistant MCP**: For future smart home integration.
- **And 400+ more...**: The `awesome-mcp-servers` repository provides a massive library of tools to choose from.

### 3.6. User Interface

- **Web Dashboard GUI**: A comprehensive control panel built as a web application (React/Vue). It will provide real-time status monitoring, conversation logs, a "thoughts" window to see Freya's internal reasoning, and full configuration management for all system components.

## 4. Data Flow: Lifecycle of a Request

1.  **Wake Word**: The **Bedroom Endpoint** microphone detects the wake word. It starts streaming audio to the **Audio Manager**.
2.  **Activation**: The **Audio Manager** identifies the "Bedroom" as the active location and publishes an `endpoint.activated` event to the **Message Bus**. Other endpoints are temporarily ignored.
3.  **Transcription**: The **STT Service**, subscribed to audio streams, transcribes the user's speech ("What's the weather like?") and publishes the text to the bus.
4.  **Reasoning**: The **LLM Engine** receives the text. It determines the user's intent is to get the weather.
5.  **Tool Call**: The LLM Engine publishes a `tool.query` event for a weather tool. The **MCP Gateway** receives this, calls the appropriate external **Weather MCP server**, and receives the result (e.g., "22°C and sunny").
6.  **Memory Retrieval**: Simultaneously, the LLM Engine queries the **Memory Manager** for relevant context (e.g., user prefers Celsius). The Memory Manager retrieves this from **ChromaDB**.
7.  **Response Generation**: The LLM Engine combines the tool result and memory context to generate a factual response: "The weather is 22 degrees Celsius and sunny."
8.  **Personality Injection**: The response is sent to the **Personality Manager**, which, knowing the user is in a casual context, reframes it: "Looks like it's a nice and sunny 22 degrees Celsius out there. Don't forget your sunglasses, unless you're going for that squinty-eyed look."
9.  **Speech Synthesis**: The final text is sent to the **TTS Service** (ElevenLabs), which generates the audio file.
10. **Playback**: The audio is sent to the **Audio Manager**, which routes it specifically to the **Bedroom Endpoint** speaker for playback.
11. **GUI Update**: Throughout this process, all services publish status, log, and data events to the **Message Bus**, which are streamed to the **Web Dashboard GUI** for real-time monitoring.

## 5. Conclusion

This service-oriented, message-driven architecture provides a robust and scalable foundation for Freya v2.0. By leveraging best-in-class open-source components (Adaptive Memory, MCP servers) and focusing custom development on unique aspects like personality and agent coordination, we can build a highly capable and maintainable system efficiently.
""
