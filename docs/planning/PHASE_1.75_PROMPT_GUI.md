# AI Coding Assistant Prompt - Freya v2.0 - Phase 1.75: GUI Dashboard

**Purpose**: This document provides the complete context and instructions for an AI coding assistant (Claude) to implement the GUI Dashboard for Freya v2.0.

**Version**: 1.0  
**Date**: December 3, 2025

---

## Initial Prompt for Claude

*Please copy and paste the following instructions as your initial prompt.*

```
You are an expert full-stack Python and React developer tasked with building the GUI for Freya v2.0, a sophisticated personal AI assistant. You will be implementing **Phase 1.75** of the project.

**REPOSITORY**: https://github.com/MrPink1977/freya_v2

**YOUR TASK**:
1.  **Assess the current state** of the repository. Note that Phase 1.5 (MCP Gateway) is complete, and the repository has been cleaned and organized.
2.  **Review the plan for Phase 1.75** outlined below.
3.  **Refine and confirm the implementation plan** before you begin coding. You do not need to create a plan from scratch; use the detailed plan provided in this document as your starting point.
4.  **Implement the GUI Dashboard** following all project standards for code quality, documentation, and error handling.

**CRITICAL INSTRUCTIONS**:
- **READ THESE FILES FIRST**: `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `DEVELOPMENT_LOG.md`, `AI_CODING_PROMPT.md`.
- **CONFIRM THE PLAN**: Present your refined plan for review before writing any code. The plan below is detailed, but you should verify it and make any necessary adjustments.
- **FOLLOW STANDARDS**: Adhere strictly to the code quality, documentation, and commit message standards defined in `AI_CODING_PROMPT.md`.

---

## Current Project State (as of Dec 3, 2025)

- **Version**: 0.2.0
- **Phases Complete**: 
    - ✅ Phase 1: Foundation
    - ✅ Phase 1.5: MCP Gateway & Tool Calling
- **Current Status**: Freya is a functional, command-line-driven AI assistant capable of using 6 different tools (web search, file system, weather, etc.) via the MCP Gateway. The core infrastructure is stable and production-quality.
- **Repository Status**: The `master` branch is up-to-date. All documentation has been organized into the `/docs` directory. Temporary and junk files have been removed.
- **Next Step**: **Phase 1.75: GUI Dashboard** as defined in `ROADMAP.md`.

---

## Detailed Plan: Phase 1.75 - GUI Dashboard

*This is your working plan. Review, refine, and present it for confirmation.*

### A. OBJECTIVE

Build a sharp, functional GUI dashboard for development, testing, and system monitoring. This interface is critical for providing visibility into Freya's internal state and for enabling text-based interaction.

**Success Criteria**:
1.  A web-based GUI is accessible in the browser.
2.  The GUI connects to the Freya backend via WebSockets for real-time updates.
3.  **Status Dashboard**: Displays the health of all running services (LLM, MCP Gateway, etc.) with green/yellow/red indicators.
4.  **Text Conversation Interface**: Allows a user to type a message to Freya and see the conversation history, including tool calls.
5.  **Logging Window**: Streams logs from all services in real-time, with filtering capabilities.
6.  The GUI is built with a modern tech stack (FastAPI, React/Vite, TailwindCSS).
7.  All code meets the project's production-quality standards.

### B. PREREQUISITES

- Phase 1.5 is complete and merged into `master`. ✅
- The tech stack is defined in `ROADMAP.md`: FastAPI (backend), React/Vite (frontend), TailwindCSS (styling). ✅
- Docker environment is functional. ✅

### C. IMPLEMENTATION STEPS

**Part 1: Backend Setup (FastAPI)** (Est: 2 hours)

1.  **Create GUI Service**: In `src/services/`, create a new `gui_service` directory. Inside, create `gui_service.py`.
2.  **Implement FastAPI App**: Set up a basic FastAPI application within the `GuiService` class.
3.  **WebSocket Endpoint**: Create a WebSocket endpoint (e.g., `/ws`) that the frontend will connect to. This endpoint will broadcast messages from the Freya message bus.
4.  **Message Bus Integration**: The `GuiService` should subscribe to relevant message bus channels:
    - `service.*.status` (for service health)
    - `service.*.log` (for log streaming - **Note**: a new logging handler will be needed to push logs to the bus)
    - `llm.conversation.history` (for chat interface)
    - `mcp.tool.call` (for tool call visualization)
5.  **Broadcast Logic**: When a message is received from the bus, format it as JSON and broadcast it to all connected WebSocket clients.
6.  **Docker Integration**: Update `docker-compose.yml` to expose the GUI service's port (e.g., 8000).

**Part 2: Frontend Setup (React + Vite)** (Est: 1.5 hours)

1.  **Initialize Frontend Project**: Inside `src/gui/`, create a `frontend` directory. Use `npm create vite@latest` to initialize a new React + TypeScript project.
2.  **Install Dependencies**: Add `tailwindcss`, `socket.io-client` (or a similar WebSocket library), and any other necessary UI libraries.
3.  **Structure Project**: Create a standard React project structure (`components`, `hooks`, `contexts`).

**Part 3: GUI Component Development** (Est: 3.5 hours)

1.  **WebSocket Connection**: Create a React hook (e.g., `useFreyaSocket`) to manage the WebSocket connection and message state.
2.  **Status Dashboard Component**: Create a component that receives service status messages and displays them with colored indicators.
3.  **Logging Window Component**: Create a component that displays a real-time, auto-scrolling list of log messages. Add basic filtering by log level.
4.  **Conversation View Component**: Create a component to display the chat history. Differentiate between user messages, Freya's responses, and tool call blocks.
5.  **Chat Input Component**: Create a form to send a new text message to Freya. This will publish a message to the `llm.input.text` channel via an HTTP endpoint on the GUI service.
6.  **Main Layout**: Assemble all components into a main application layout (e.g., using a grid system).

**Part 4: Finalization & Documentation** (Est: 1 hour)

1.  **Refine Styling**: Ensure the UI is clean, modern, and uses the specified green accent colors.
2.  **Testing**: Perform end-to-end testing to ensure all features work as expected.
3.  **Update `DEVELOPMENT_LOG.md`**: Add a detailed entry for Phase 1.75.
4.  **Create `README.md` for GUI**: Add a `README.md` inside `src/gui/frontend` explaining how to run the frontend in development mode.

### D. FILES TO CREATE/MODIFY

- **Create**:
    - `src/services/gui_service/__init__.py`
    - `src/services/gui_service/gui_service.py` (FastAPI backend)
    - `src/gui/frontend/` (entire React/Vite project)
    - `src/gui/frontend/src/components/StatusDashboard.tsx`
    - `src/gui/frontend/src/components/LoggingWindow.tsx`
    - `src/gui/frontend/src/components/ConversationView.tsx`
    - `src/gui/frontend/src/hooks/useFreyaSocket.ts`
    - `src/gui/frontend/README.md`
- **Modify**:
    - `docker-compose.yml` (expose GUI port, add GUI service)
    - `src/main.py` (add `GuiService` to the orchestrator)
    - `src/core/config.py` (add `gui_port` parameter)
    - `src/core/logging_config.py` (or similar, to add a handler that publishes logs to Redis)
    - `DEVELOPMENT_LOG.md` (add new entry)

### E. TESTING PLAN

1.  **Backend**: Use a WebSocket client tool to connect to `/ws` and verify that messages from the message bus are being broadcast.
2.  **Frontend**: Run the frontend and verify it connects to the backend WebSocket.
3.  **End-to-End**:
    - Stop/start a service and see its status light change on the dashboard.
    - Send a message in the chat input and watch the full conversation appear.
    - Send a query that triggers a tool call (e.g., "What's the weather?") and verify the tool call is visualized.
    - Verify logs from all services appear in the logging window.

### F. DOCUMENTATION UPDATES

- **`DEVELOPMENT_LOG.md`**: Add a comprehensive entry for the completion of Phase 1.75.
- **`README.md`**: Add a section about the GUI and how to access it.

### G. INTEGRATION POINTS

- **Message Bus (Input)**: The GUI service will subscribe to `service.*.status`, `*.log`, `llm.conversation.history`, and `mcp.tool.call`.
- **Message Bus (Output)**: The GUI's text input will publish to `llm.input.text`.
- **Networking**: The frontend connects to the backend via WebSockets on the port defined in `config.py` and exposed in `docker-compose.yml`.

### H. POTENTIAL ISSUES

- **Log Volume**: Streaming all logs might be too much for the WebSocket. Consider sampling or filtering logs on the backend before broadcasting.
- **State Management**: Managing real-time data on the frontend can be complex. A state management library (like Zustand or Redux Toolkit) might be beneficial.
- **Styling**: Achieving a "sharp" interface requires careful attention to TailwindCSS configuration and component design.

### I. ROLLBACK PLAN

- All work will be done on a new feature branch (e.g., `feature/phase-1.75-gui`).
- If the implementation fails, the branch can be discarded without affecting `master`.
- The merge to `master` will only occur after successful testing and review.

---

## Final Instruction for Claude

Please review this entire document. Refine the plan above, especially the implementation steps and file structure, into a final proposal. Present your refined plan for confirmation before you begin writing any code.
```
