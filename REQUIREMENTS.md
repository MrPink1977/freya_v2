# Freya v2.0 - Requirements Document

**Date:** December 3, 2025  
**Author:** Manus AI  
**Status:** Clean Slate Design

## Executive Summary

Freya v2.0 is a location-aware, multi-room personal AI assistant with persistent memory, vision capabilities, and extensive tool integration. The system prioritizes local processing while strategically using cloud services for enhanced quality, with a focus on natural interaction and comprehensive monitoring.

## Core Requirements

### 1. Hardware Configuration

#### Compute
- **Primary Server**: Single PC with RTX 5060 Ti 16GB
- **GPU**: CUDA-enabled for local LLM inference
- **Storage**: SSD for fast model loading and database access

#### Audio/Video Endpoints
| Location | Microphone | Speaker | Camera |
|----------|-----------|---------|--------|
| **Bedroom** | ✓ | ✓ | ✗ |
| **Front Door** | ✓ | ✓ | ✓ |

**Future Expansion**: Architecture must support adding additional rooms easily

### 2. Processing Philosophy

#### Local-First Strategy
- **Core LLM**: Local model on RTX 5060 Ti
- **Wake Word Detection**: Local (Tiny Whisper)
- **STT (Speech-to-Text)**: Local primary (faster-whisper)
- **Memory/Database**: Local (ChromaDB or similar)
- **File Operations**: Local
- **Basic Tools**: Local

#### Strategic Cloud Services
- **TTS (Text-to-Speech)**: ElevenLabs (with local fallback)
- **Advanced Web Search**: Cloud APIs (Brave, etc.)
- **Optional Services**: Weather, news, etc.

**Rationale**: Quality and capability where it matters, privacy and reliability where it counts.

### 3. Location Awareness

#### Wake Word Behavior
1. **Trigger**: Any endpoint hears "Hey Freya" (or custom wake word)
2. **Response**: Active endpoint becomes conversation owner
3. **Isolation**: Other endpoints temporarily disabled
4. **Session**: Conversation continues at active endpoint until completion

#### Listening Window
- **Initial**: Wake word triggers active listening
- **Continuation**: Smart listening window (3-5 seconds of silence = end)
- **No Repeated Wake**: Natural conversation flow without constant "Hey Freya"

#### Location Context
- Each endpoint has location metadata (bedroom, front_door)
- Responses can be location-specific ("turning on bedroom lights")
- Memory can store location-tagged events

### 4. Memory System

#### Architecture: Adaptive Memory v3 (Integrated)
Based on the proven OpenWebUI plugin with 6,700+ downloads.

#### Memory Categories
1. **Identity**: Name, age, occupation, personal facts
2. **Preferences**: Likes, dislikes, habits
3. **Behavior**: Patterns, routines, interests
4. **Relationships**: Family, friends, contacts
5. **Goals**: Aspirations, projects, tasks
6. **Possessions**: Owned items, resources

#### Memory Organization
- **Memory Banks**: Personal, Work, General
- **Short-term**: Current conversation context (last 10-20 exchanges)
- **Long-term**: Persistent facts, preferences, history
- **Clustering**: Automatic grouping of related memories
- **Summarization**: Periodic compression of old memories

#### Memory Operations
- **Extraction**: LLM-powered from conversations
- **Deduplication**: Embedding-based semantic similarity
- **Retrieval**: Vector search + optional LLM relevance scoring
- **Pruning**: Configurable (FIFO or relevance-based)

### 5. Vision Capabilities

#### Phase 1 (MVP)
- **Motion Detection**: Alert when someone approaches front door
- **Basic Object Detection**: "A car is pulling in"

#### Phase 2 (Future)
- **Facial Recognition**: Identify known people
- **Advanced Alerts**: "John is at the front door"

#### Integration
- Camera feed processed locally
- Alerts trigger Freya responses
- Visual context available to LLM when relevant

### 6. Tool Ecosystem

#### Core Tools (MCP Servers)
All tools exposed via Model Context Protocol for modularity and extensibility.

##### File Operations
- List, read, write, delete files
- Directory navigation
- File search
- **Implementation**: Official MCP filesystem server

##### Web Capabilities
- **Web Search**: Brave Search MCP (or similar)
- **Web Scraping**: Playwright MCP for dynamic content
- **URL Fetching**: Simple HTTP requests

##### System Operations
- Execute shell commands (with safety guards)
- System information (CPU, memory, disk)
- Process management
- **Implementation**: Shell MCP server

##### Information Services
- **Weather**: Current conditions and forecast
- **Date/Time**: Current time, timezone info
- **Calendar**: Event management (future)
- **News**: Headlines and summaries

##### Media & Entertainment
- **Spotify**: Playback control, search, playlists (future)
- **Music**: Local media playback

##### Home Automation (Future)
- **Home Assistant Integration**: Device control
- **Scene Management**: Lighting, climate, etc.

#### Tool Management
- **MCP Aggregator**: MetaMCP or MCPX for unified tool access
- **Dynamic Discovery**: Tools can be added without code changes
- **Permission System**: User approval for sensitive operations

### 7. Personality System

#### Core Traits
- **Name**: Freya
- **Tone**: Witty, funny, playfully sarcastic
- **Capability**: Excellent at her job
- **Adaptability**: Knows when to be serious vs. playful
- **Consistency**: Same personality across all locations

#### Context Awareness
- **Important Tasks**: Professional, focused, accurate
- **Casual Conversation**: Playful, engaging, humorous
- **Emergencies**: Direct, clear, helpful

#### Implementation
- Personality defined in system prompt
- Context-aware tone adjustment
- Memory of interaction style preferences

### 8. User Interface (GUI)

#### Dashboard Requirements

##### System Status Panel
- **Green Lights**: All systems operational
- **Component Status**: LLM, STT, TTS, Memory, MCP Servers
- **Endpoint Status**: Each mic/speaker/camera with health indicators
- **Resource Monitoring**: CPU, GPU, RAM, VRAM usage

##### Conversation Windows
- **Text Chat**: Full conversation history with timestamps
- **Freya's Thoughts**: Internal reasoning, tool calls, decision process
- **Active Location**: Which endpoint is currently active

##### Logging Panel
- **System Logs**: Errors, warnings, info
- **Tool Execution**: What tools are being called
- **Memory Operations**: What's being stored/retrieved
- **Performance Metrics**: Response times, model inference speed

##### Settings & Control
- **Endpoint Configuration**: Enable/disable locations
- **Model Selection**: Choose LLM, STT, TTS models
- **Memory Management**: View, edit, delete memories
- **Tool Configuration**: Enable/disable tools, set permissions
- **Personality Tuning**: Adjust system prompts

#### Technology Stack
- **Framework**: Web-based (React + FastAPI backend)
- **Real-time Updates**: WebSocket for live status
- **Visualization**: Charts for performance metrics
- **Responsive**: Works on desktop and tablet

### 9. Technical Architecture

#### Core Components

##### 1. Audio Manager
- Multi-endpoint audio routing
- Wake word detection per endpoint
- Location-aware session management

##### 2. LLM Engine
- Local model inference (Ollama or vLLM)
- Model: Llama 3.2 or similar (quality over speed)
- GPU acceleration via CUDA

##### 3. Memory Manager
- Adaptive Memory v3 integration
- Vector database (ChromaDB)
- Automatic extraction and retrieval

##### 4. MCP Client
- Official Python SDK
- Connection to multiple MCP servers
- Tool discovery and execution

##### 5. Vision Pipeline
- Camera feed processing
- Object/motion detection
- Future: Facial recognition

##### 6. Web Dashboard
- Real-time monitoring
- Configuration interface
- Conversation interface

#### Communication Architecture
- **Message Bus**: Central event system (Redis or in-memory)
- **WebSocket**: GUI ↔ Backend communication
- **MCP Protocol**: Tool communication
- **Audio Streaming**: Endpoint ↔ Server

### 10. Development Priorities

#### Phase 1: Foundation (Weeks 1-2)
- Core LLM integration (local Ollama)
- Single endpoint audio (bedroom)
- Basic STT/TTS pipeline
- Simple memory system
- Basic GUI (status + chat)

#### Phase 2: Multi-Room (Weeks 3-4)
- Second endpoint (front door)
- Location awareness
- Wake word detection
- Endpoint isolation

#### Phase 3: Tools (Weeks 5-6)
- MCP SDK integration
- 5-10 core tools
- Tool execution in GUI

#### Phase 4: Memory (Weeks 7-8)
- Adaptive Memory v3 integration
- Memory visualization in GUI
- Long-term persistence

#### Phase 5: Vision (Weeks 9-10)
- Camera integration
- Motion/object detection
- Visual alerts

#### Phase 6: Polish (Weeks 11-12)
- Personality refinement
- GUI enhancements
- Performance optimization
- Documentation

## Success Criteria

### Functional
- ✓ Responds to wake word at any endpoint
- ✓ Location-aware conversations
- ✓ Persistent memory across sessions
- ✓ Executes 10+ useful tools
- ✓ Natural conversation flow (no repeated wake words)
- ✓ Visual alerts from camera

### Performance
- ✓ Wake word detection < 500ms
- ✓ STT processing < 2 seconds
- ✓ LLM response < 5 seconds (quality over speed)
- ✓ TTS generation < 2 seconds
- ✓ End-to-end latency < 10 seconds

### Quality
- ✓ Accurate speech recognition (>95%)
- ✓ Natural-sounding TTS (ElevenLabs quality)
- ✓ Contextually appropriate responses
- ✓ Reliable memory recall
- ✓ Stable 24/7 operation

### User Experience
- ✓ Feels like talking to a real assistant
- ✓ Witty and engaging personality
- ✓ Helpful and accurate
- ✓ Easy to monitor and configure
- ✓ Minimal false wake word triggers
