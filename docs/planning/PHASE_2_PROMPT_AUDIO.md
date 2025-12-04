# AI Coding Assistant Prompt - Freya v2.0 - Phase 2: Audio Pipeline

**Purpose**: This document provides the complete context and instructions for an AI coding assistant (Claude) to implement the **Phase 2: Audio Pipeline** for Freya v2.0.

**Version**: 1.0  
**Date**: December 3, 2025

---

## Initial Prompt for Claude

*Please copy and paste the following instructions as your initial prompt.*

```
You are an expert Python developer specializing in real-time audio processing and AI service integration. You are tasked with building the end-to-end audio pipeline for Freya v2.0, a sophisticated personal AI assistant. You will be implementing **Phase 2** of the project.

**REPOSITORY**: https://github.com/MrPink1977/freya_v2

**YOUR TASK**:
1.  **Assess the current state** of the repository. Note that Phase 1.75 (GUI Dashboard) is complete and merged to `master`.
2.  **Review the plan for Phase 2** outlined below. The new GUI is a critical tool for testing and visualization.
3.  **Refine and confirm the implementation plan** before you begin coding. Use the detailed plan in this document as your starting point.
4.  **Implement the Audio Pipeline**, including the STT Service, TTS Service, and Audio Manager, following all project standards.

**CRITICAL INSTRUCTIONS**:
- **READ THESE FILES FIRST**: `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `DEVELOPMENT_LOG.md`, `AI_CODING_PROMPT.md`, and `docs/GUI_SETUP.md`.
- **LEVERAGE THE GUI**: The GUI is your primary tool for testing. You will need to run it to see your audio features working in real-time.
- **CONFIRM THE PLAN**: Present your refined plan for review before writing any code.
- **FOLLOW STANDARDS**: Adhere strictly to the code quality, documentation, and commit message standards defined in `AI_CODING_PROMPT.md`.

---

## Current Project State (as of Dec 3, 2025)

- **Version**: 0.3.0
- **Phases Complete**: 
    - ✅ Phase 1: Foundation
    - ✅ Phase 1.5: MCP Gateway & Tool Calling
    - ✅ Phase 1.75: GUI Dashboard
- **Current Status**: Freya is a functional, text-based AI assistant with a real-time web dashboard for monitoring and interaction. The core infrastructure is stable and production-quality.
- **Repository Status**: The `master` branch is up-to-date. All documentation is organized. The GUI is fully functional.
- **Next Step**: **Phase 2: Audio Pipeline** as defined in `ROADMAP.md`.

---

## Detailed Plan: Phase 2 - Audio Pipeline

*This is your working plan. Review, refine, and present it for confirmation.*

### A. OBJECTIVE

Implement an end-to-end, real-time audio pipeline that allows a user to speak to Freya and hear her spoken response. This involves three new services: an STT Service, a TTS Service, and an Audio Manager to coordinate them.

**Success Criteria**:
1.  **STT Service**: Transcribes raw audio from a microphone into text using `faster-whisper` with GPU acceleration.
2.  **TTS Service**: Converts Freya's text responses into audible speech using the ElevenLabs MCP server.
3.  **Audio Manager**: Captures microphone input and plays back output audio streams.
4.  **End-to-End Flow**: A user can speak, the transcribed text appears in the GUI, the LLM responds, and the user hears Freya's spoken response.
5.  **GUI Integration**: The GUI is updated to visualize the audio pipeline's status and activity.

### B. ARCHITECTURE

```
 Mic Input
     │
     ▼
┌──────────────────┐   audio.input.stream   ┌──────────────────┐
│  Audio Manager   ├────────────────────────►│    STT Service   │
│ (PyAudio Capture)│                        │ (faster-whisper) │
└─────────┬────────┘   stt.transcription    └─────────┬────────┘
          │          ◄────────────────────────┘         │
          │                                             ▼
          │                                     ┌──────────────────┐
          │                                     │    LLM Engine    │
          │                                     └─────────┬────────┘
          │                                               │ llm.final_response
          │                                               ▼
┌─────────┴────────┐   audio.output.stream  ┌──────────────────┐
│  Audio Manager   ◄────────────────────────┤    TTS Service   │
│  (PyAudio Play)  │                        │ (ElevenLabs MCP) │
└──────────────────┘                        └──────────────────┘
     │
     ▼
 Speaker Output
```

### C. IMPLEMENTATION STEPS

**Part 1: STT Service (`faster-whisper`)** (Est: 2-3 hours)

1.  **Create `SttService`**: In `src/services/`, create a new `stt_service` directory and `stt_service.py` file.
2.  **Integrate `faster-whisper`**: Add `faster-whisper` to the project dependencies. The service should load the specified model upon initialization.
3.  **GPU/CPU Detection**: Automatically detect if a GPU is available and select the appropriate compute type (`float16` for GPU, `int8` for CPU).
4.  **Message Bus**: 
    - **Subscribe**: to `audio.input.stream` to receive raw audio chunks.
    - **Publish**: transcribed text to the `stt.transcription` channel.
5.  **Configuration**: Add `stt_model_size` (e.g., "base", "small", "medium") and `stt_device` ("auto", "cuda", "cpu") to `config.py`.

**Part 2: TTS Service (ElevenLabs MCP)** (Est: 1.5-2 hours)

1.  **Create `TtsService`**: In `src/services/`, create a new `tts_service` directory and `tts_service.py` file.
2.  **MCP Integration**: This service will **not** call the MCP server directly. Instead, it will listen for LLM responses and then use the `mcp_gateway` to invoke the `elevenlabs_tts` tool.
3.  **Message Bus**:
    - **Subscribe**: to `llm.final_response` to get the text to be synthesized.
    - **Publish**: the resulting audio bytes to the `audio.output.stream` channel.
4.  **Configuration**: Add `tts_voice_id` to `config.py` to specify which ElevenLabs voice to use.

**Part 3: Audio Manager** (Est: 2-3 hours)

1.  **Create `AudioManager`**: In `src/services/`, create `audio_manager` directory and `audio_manager.py`.
2.  **PyAudio Integration**: Add `PyAudio` to dependencies. This service will manage audio I/O.
3.  **Microphone Capture**: In a separate thread, continuously capture audio from the default microphone.
    - **Publish**: the raw audio chunks to the `audio.input.stream` channel.
4.  **Audio Playback**: 
    - **Subscribe**: to `audio.output.stream`.
    - When audio is received, play it back through the default speaker.
5.  **Configuration**: Add `audio_chunk_size` and `audio_sample_rate` to `config.py`.

**Part 4: GUI & Core Integration** (Est: 1-1.5 hours)

1.  **Modify `GuiService`**:
    - Subscribe to `stt.transcription` and display the text in the chat window (distinguished from user-typed messages).
    - Add status indicators for the three new audio services to the dashboard.
    - Add a "Mute/Unmute" button to the GUI that publishes to a new `audio.mute.toggle` channel, which the `AudioManager` will listen to.
2.  **Modify `LLMEngine`**: 
    - Subscribe to `stt.transcription` and treat it as user input to the LLM.
3.  **Modify `main.py`**: Add `SttService`, `TtsService`, and `AudioManager` to the service orchestrator.
4.  **Modify `docker-compose.yml`**: Ensure the container has access to audio devices (`/dev/snd`).

### D. FILES TO CREATE/MODIFY

- **Create**:
    - `src/services/stt_service/stt_service.py`
    - `src/services/tts_service/tts_service.py`
    - `src/services/audio_manager/audio_manager.py`
- **Modify**:
    - `pyproject.toml` (add `faster-whisper`, `pyaudio`)
    - `docker-compose.yml` (add audio device access)
    - `src/core/config.py` (add STT, TTS, and Audio config parameters)
    - `src/main.py` (add new services to orchestrator)
    - `src/services/gui/gui_service.py` (add new subscriptions and UI elements)
    - `src/services/llm/llm_engine.py` (subscribe to STT channel)
    - `DEVELOPMENT_LOG.md` (add new entry for Phase 2)

### E. TESTING PLAN (Using the GUI)

1.  **Run Freya**: Start all services using `docker-compose` and `python -m src.main`.
2.  **Open GUI**: Navigate to `http://localhost:5173`.
3.  **Check Dashboard**: Verify that `SttService`, `TtsService`, and `AudioManager` appear in the services panel with a green status light.
4.  **Speak**: Unmute the microphone (if needed) and say a phrase like "Hello Freya, what time is it?"
5.  **Verify STT**: Watch the GUI chat window. Your transcribed speech should appear, perhaps with a microphone icon next to it.
6.  **Verify LLM & Tool**: The LLM should process the text, call the `get_time` tool, and generate a response.
7.  **Verify TTS**: You should hear Freya's response spoken through your speakers.
8.  **Check Logs**: The GUI's tool log should show the `elevenlabs_tts` tool being called.

### F. DOCUMENTATION UPDATES

- **`DEVELOPMENT_LOG.md`**: Add a comprehensive entry for the completion of Phase 2.
- **`README.md`**: Update the main `README` to reflect that Freya now has voice capabilities.
- **`docs/GUI_SETUP.md`**: Add a section on how to test the new audio features.

---

## Final Instruction for Claude

Please review this entire document. Refine the plan above, especially the implementation steps and message bus channel names, into a final proposal. Present your refined plan for confirmation before you begin writing any code. The GUI is your best friend for this phase—use it for all your testing!
```
