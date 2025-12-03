# Freya v2.0 - GUI Dashboard Setup Guide

**Author**: Claude (AI Assistant)
**Version**: 1.0
**Date**: 2025-12-03
**Phase**: 1.75

---

## Overview

The Freya v2.0 GUI Dashboard provides a real-time web interface for monitoring and controlling the Freya AI assistant. It features:

- **Service Status Monitoring** - Real-time health indicators for all services
- **Conversation Interface** - Chat with Freya directly from the browser
- **Tool Call Logging** - See which MCP tools are being executed in real-time
- **WebSocket Updates** - Instant updates with no page refresh needed

---

## Architecture

```
┌─────────────────────────────────────┐
│      React Frontend (Port 5173)     │
│   - Service Panel                   │
│   - Chat Window                     │
│   - Tool Log                        │
└──────────────┬──────────────────────┘
               │ WebSocket + REST
┌──────────────┴──────────────────────┐
│   FastAPI Backend (Port 8000)       │
│   - REST API endpoints              │
│   - WebSocket real-time updates    │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│       Redis Message Bus              │
│   (All service events)              │
└─────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Node.js 18+ and npm 9+
- Docker and Docker Compose
- Python 3.11+

### Step 1: Install Frontend Dependencies

```bash
cd src/gui/frontend
npm install
```

### Step 2: Start Development Server

**For Development** (with hot-reload):
```bash
npm run dev
```

The Vite development server will start on `http://localhost:5173`

**For Production** (build static files):
```bash
npm run build
```

This creates a `dist/` folder that FastAPI can serve directly.

---

## Running the GUI

### Development Mode

1. **Start Backend Services**:
   ```bash
   docker-compose up -d redis ollama chromadb
   ```

2. **Start Freya Core** (includes GUI backend):
   ```bash
   python -m src.main
   ```

3. **Start Frontend Dev Server** (in separate terminal):
   ```bash
   cd src/gui/frontend
   npm run dev
   ```

4. **Access the Dashboard**:
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

### Production Mode

1. **Build Frontend**:
   ```bash
   cd src/gui/frontend
   npm run build
   ```

2. **Start All Services**:
   ```bash
   docker-compose up -d
   ```

3. **Access Dashboard**:
   - GUI: `http://localhost:8000`

---

## Configuration

GUI settings are in `src/core/config.py`:

```python
# GUI Configuration
gui_enabled: bool = True                    # Enable/disable GUI
gui_host: str = "0.0.0.0"                   # Host to bind to
gui_port: int = 8000                        # Port for FastAPI backend
gui_cors_origins: List[str] = [...]         # Allowed CORS origins
gui_websocket_heartbeat: int = 30           # WebSocket ping interval
gui_log_retention: int = 1000               # Max messages to keep
```

You can override these with environment variables:

```bash
export GUI_ENABLED=true
export GUI_HOST=0.0.0.0
export GUI_PORT=8000
```

---

## API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/status` | GET | System status with all services |
| `/api/services` | GET | List of services with status |
| `/api/conversation` | GET | Recent chat history |
| `/api/tools` | GET | Recent tool call log |
| `/api/message` | POST | Send message to Freya |

### WebSocket

**Endpoint**: `/ws`

**Messages Sent to Client**:

```json
{
  "type": "service_status",
  "data": {
    "name": "llm_engine",
    "status": "started",
    "healthy": true,
    "uptime": 123.45,
    "error_count": 0
  },
  "timestamp": "2025-12-03T12:00:00"
}
```

```json
{
  "type": "chat_message",
  "data": {
    "id": "uuid",
    "role": "user|assistant",
    "content": "Hello!",
    "timestamp": "2025-12-03T12:00:00",
    "location": "web_gui"
  }
}
```

```json
{
  "type": "tool_call",
  "data": {
    "id": "uuid",
    "tool_name": "calculator",
    "arguments": {"expression": "2+2"},
    "result": 4,
    "success": true,
    "duration": 0.05
  }
}
```

---

## Features

### 1. Service Status Panel

Displays real-time status of all Freya services:
- **Green dot**: Service is healthy and running
- **Red dot**: Service is unhealthy or stopped
- **Service name**: Name of the service
- **Status text**: Current state (started, stopped, error)

### 2. Chat Window

Interactive chat interface with Freya:
- Send messages by typing and pressing Enter or clicking Send
- User messages appear on the right (blue)
- Freya's responses appear on the left (gray)
- Timestamps and location tags for each message
- Auto-scrolls to newest message

### 3. Tool Call Log

Shows recent MCP tool executions:
- Tool name and status (success/error)
- Execution duration
- Error messages if tool failed
- Displays last 10 tool calls

### 4. Connection Status

Bottom-right indicator shows WebSocket connection status:
- **Green border**: Connected and receiving updates
- **Red border**: Disconnected, attempting reconnection

---

## Troubleshooting

### Frontend Won't Connect to Backend

**Problem**: Connection refused errors

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check ports in `docker-compose.yml` match config
3. Ensure CORS origins include `http://localhost:5173`

### WebSocket Keeps Disconnecting

**Problem**: WebSocket connection drops repeatedly

**Solutions**:
1. Check backend logs for errors
2. Verify WebSocket endpoint: `ws://localhost:8000/ws`
3. Check browser console for connection errors
4. Ensure no firewall blocking WebSocket traffic

### No Services Showing

**Problem**: Service panel is empty

**Solutions**:
1. Wait 5-10 seconds for initial state message
2. Check backend is publishing service status events
3. Verify Redis message bus is running
4. Check WebSocket connection is established

### Messages Not Appearing

**Problem**: Sent messages don't show up

**Solutions**:
1. Check LLM Engine is subscribed to `gui.user.message`
2. Verify message reaches backend: Check backend logs
3. Ensure `gui_enabled=true` in config
4. Test API directly: `curl -X POST http://localhost:8000/api/message -d '{"content":"test"}'`

---

## Development

### File Structure

```
src/gui/
├── frontend/              # React application
│   ├── src/
│   │   ├── App.jsx        # Main application component
│   │   ├── main.jsx       # Entry point
│   │   └── index.css      # Global styles
│   ├── index.html         # HTML template
│   ├── package.json       # Dependencies
│   └── vite.config.js     # Vite configuration
│
├── __init__.py            # Package init
├── gui_service.py         # FastAPI backend
├── websocket_manager.py   # WebSocket handling
└── models.py              # Pydantic models
```

### Adding New Features

**Adding a new panel**:
1. Create component in `src/gui/frontend/src/components/`
2. Add to `App.jsx`
3. Update CSS in `index.css`

**Adding new API endpoint**:
1. Add route in `gui_service.py` `_setup_routes()`
2. Update models in `models.py` if needed
3. Test with `/docs` Swagger UI

**Adding new WebSocket message type**:
1. Publish from backend service
2. Handle in `websocket_manager.py`
3. Add case in `App.jsx` `handleWebSocketMessage()`

---

## Security Notes

- GUI backend uses CORS - only allowed origins can connect
- WebSocket requires same-origin by default
- No authentication in Phase 1.75 (local use only)
- For production deployment, add authentication layer

---

## Next Steps

- **Phase 2**: Add audio/video endpoint status
- **Phase 3**: Tool execution controls (approve/deny)
- **Phase 4**: Memory browser and editor
- **Phase 5**: Live video feeds
- **Phase 6**: Personality customization UI

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f freya-core`
- Review backend API: `http://localhost:8000/docs`
- Check browser console for frontend errors
- Verify all services running: `docker-compose ps`

