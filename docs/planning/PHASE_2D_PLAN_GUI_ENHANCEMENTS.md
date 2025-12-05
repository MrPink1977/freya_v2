# Phase 2D Implementation Plan: GUI Frontend Enhancements

**Author:** Claude (AI Assistant)
**Date:** December 5, 2025
**Phase:** 2D - GUI Frontend Enhancements
**Estimated Time:** 6-8 hours
**Status:** 📋 Planning

---

## Executive Summary

Phase 2D enhances the Freya GUI dashboard with real-time debugging tools, audio testing interfaces, and improved monitoring capabilities. This phase focuses on making the audio pipeline testable and observable through the web interface.

**Goal:** Transform the GUI from a basic monitoring tool into a comprehensive development and testing platform for the audio pipeline.

---

## A. OBJECTIVE

Build frontend components that enable:
1. **Real-time debugging** of all services and message bus traffic
2. **Audio device management** through the browser
3. **Interactive testing** of the STT/TTS pipeline
4. **Visual feedback** for audio processing stages
5. **Test execution** and coverage visualization

### Success Criteria

1. ✅ Debug panel shows live message bus traffic
2. ✅ Audio device selector allows switching input/output
3. ✅ Audio tester enables mic recording and playback
4. ✅ Service status shows detailed metrics
5. ✅ STT transcriptions appear in real-time
6. ✅ TTS generation can be triggered manually
7. ✅ Test runner executes pytest from GUI
8. ✅ Coverage visualization shows test results

---

## B. PREREQUISITES

### Required (Already Complete)
- ✅ Phase 2 backend verified and functional
- ✅ GUI Service with WebSocket support
- ✅ React frontend with basic components
- ✅ Message bus integration
- ✅ Audio services operational

### Optional (Nice to Have)
- 🔲 Backend API endpoints for test execution
- 🔲 Coverage data export from pytest
- 🔲 WebSocket support for real-time logs

---

## C. ARCHITECTURE

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│              Freya GUI Dashboard                    │
│  (http://localhost:5173 - React + Vite)             │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Debug Panel  │ │ Audio Tester │ │ Test Runner  │
│              │ │              │ │              │
│ - Bus msgs   │ │ - Device sel │ │ - Run tests  │
│ - Logs       │ │ - Record/Play│ │ - Coverage   │
│ - Metrics    │ │ - STT/TTS    │ │ - Results    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │ WebSocket + REST
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ GUI Service  │ │Audio Manager │ │ Test Service │
│   (FastAPI)  │ │  (Backend)   │ │   (New)      │
└──────────────┘ └──────────────┘ └──────────────┘
```

### New Components

#### Frontend (React)
1. **DebugPanel.jsx** - Real-time debugging interface
2. **AudioTester.jsx** - Audio device testing
3. **TestRunner.jsx** - Test execution interface
4. **ServiceMetrics.jsx** - Enhanced service monitoring
5. **MessageLog.jsx** - Message bus traffic viewer

#### Backend (FastAPI)
1. **TestService** - New service for running tests
2. **Enhanced GUI endpoints** - More detailed status APIs
3. **WebSocket enhancements** - Real-time log streaming

---

## D. IMPLEMENTATION STEPS

### Part 1: Debug Panel Component (2-3 hours)

**Goal:** Real-time visibility into message bus traffic and service logs.

#### Step 1.1: Create DebugPanel Component (1 hour)
```jsx
// src/gui/frontend/src/components/DebugPanel.jsx
- Message bus traffic viewer
  * Channel filter (show/hide specific channels)
  * Message content inspector
  * Auto-scroll toggle
  * Search/filter messages
- Real-time log streaming
  * Log level filter (DEBUG, INFO, WARNING, ERROR)
  * Service filter (show logs from specific services)
  * Color-coded by level
- Service metrics display
  * Uptime, error count, health status
  * Request/response times
  * Memory usage (if available)
```

#### Step 1.2: Backend Message Logging (30 min)
```python
# src/services/gui/gui_service.py
- Subscribe to all message bus channels (using wildcard)
- Buffer last 100 messages in memory
- Add REST endpoint: GET /api/debug/messages
- Add WebSocket message type: "bus_message"
- Add log streaming via WebSocket
```

#### Step 1.3: Integrate into Dashboard (30 min)
- Add DebugPanel to App.jsx
- Create collapsible panel layout
- Add keyboard shortcut (Ctrl+D) to toggle
- Style with dark theme for better readability

**Deliverable:** Working debug panel showing real-time message bus traffic

---

### Part 2: Audio Tester Component (2-3 hours)

**Goal:** Interactive testing of audio devices and STT/TTS pipeline.

#### Step 2.1: Audio Device Selector (1 hour)
```jsx
// src/gui/frontend/src/components/AudioTester.jsx
- Device enumeration
  * List all input devices
  * List all output devices
  * Show default device indicator
- Device selection
  * Dropdown for input device
  * Dropdown for output device
  * Apply button to update Audio Manager
- Device status
  * Show current device in use
  * Indicate if device is available
```

#### Step 2.2: Recording Interface (1 hour)
```jsx
// Recording controls
- Record button (start/stop)
- Recording duration indicator
- Volume level meter (visual feedback)
- Recorded audio preview
- Play button for recorded audio
- Submit to STT button

// WebRTC MediaRecorder integration
- Capture audio from browser microphone
- Save as WAV/WebM
- Send to backend for STT processing
```

#### Step 2.3: TTS Testing Interface (30 min)
```jsx
// TTS controls
- Text input field
- Voice selector (from config)
- Generate Speech button
- Play generated audio
- Download audio file

// Integration
- Call POST /api/tts/generate endpoint
- Receive audio stream
- Play in browser audio element
```

#### Step 2.4: Backend API Endpoints (30 min)
```python
# src/services/gui/gui_service.py

@app.get("/api/audio/devices")
async def get_audio_devices():
    """Get available audio devices."""
    # Publish to audio.control.list_devices
    # Return device list

@app.post("/api/audio/device")
async def set_audio_device(device_config: DeviceConfig):
    """Set input/output device."""
    # Publish to audio.control.set_device

@app.post("/api/tts/generate")
async def generate_speech(request: TTSRequest):
    """Generate speech from text."""
    # Publish to tts.generate
    # Return audio bytes

@app.post("/api/stt/transcribe")
async def transcribe_audio(audio: UploadFile):
    """Transcribe uploaded audio."""
    # Publish to audio.stream
    # Wait for stt.transcription
    # Return transcribed text
```

**Deliverable:** Complete audio testing interface with device selection and STT/TTS testing

---

### Part 3: Test Runner Component (2-3 hours)

**Goal:** Execute tests from the GUI and visualize results.

#### Step 3.1: Create TestService (1.5 hours)
```python
# src/services/test/test_service.py
class TestService(BaseService):
    """
    Service for running pytest tests from the GUI.

    Subscribes to:
        - test.run: Execute test suite
        - test.coverage: Generate coverage report

    Publishes to:
        - test.result: Test execution results
        - test.coverage.data: Coverage data
        - service.test_service.status: Service status
    """

    async def run_tests(self, pattern: str = None):
        """Run pytest with optional pattern filter."""
        # Execute: pytest tests/ -v --cov=src
        # Parse output and publish results

    async def get_coverage(self):
        """Get current coverage data."""
        # Read coverage.xml or coverage.json
        # Parse and return structured data
```

#### Step 3.2: Create TestRunner Component (1 hour)
```jsx
// src/gui/frontend/src/components/TestRunner.jsx
- Test execution controls
  * Run All Tests button
  * Run Unit Tests button
  * Run Integration Tests button
  * Test pattern input field
  * Running indicator (spinner)

- Test results display
  * Total tests, passed, failed, errors
  * Execution time
  * Individual test results (collapsible)
  * Error messages and stack traces

- Coverage visualization
  * Overall coverage percentage
  * Coverage by module (bar chart)
  * Coverage heatmap (if possible)
  * Link to HTML coverage report
```

#### Step 3.3: Backend Integration (30 min)
```python
# Add endpoints to gui_service.py

@app.post("/api/tests/run")
async def run_tests(request: TestRunRequest):
    """Run test suite."""
    # Publish to test.run
    # Return job ID

@app.get("/api/tests/result/{job_id}")
async def get_test_result(job_id: str):
    """Get test execution result."""
    # Return cached result

@app.get("/api/coverage")
async def get_coverage():
    """Get current test coverage data."""
    # Return coverage metrics
```

**Deliverable:** Working test runner with real-time results and coverage visualization

---

### Part 4: Enhanced Service Monitoring (1 hour)

**Goal:** Better visibility into service health and performance.

#### Step 4.1: Service Metrics Component (45 min)
```jsx
// src/gui/frontend/src/components/ServiceMetrics.jsx
- Detailed service cards
  * Service name and status
  * Uptime (formatted duration)
  * Error count and last error
  * Request count and rate
  * Memory usage (if available)

- Visual indicators
  * Green: Healthy (0 errors, uptime > 1 min)
  * Yellow: Degraded (1-5 errors, uptime < 1 min)
  * Red: Unhealthy (5+ errors or not responding)
  * Gray: Stopped

- Service actions
  * Restart button (future)
  * View logs button (link to debug panel)
  * Clear errors button
```

#### Step 4.2: Update ServiceStatus Display (15 min)
- Replace simple status panel with ServiceMetrics cards
- Add expandable detail view
- Show message subscriptions and publications
- Display last 5 messages sent/received

**Deliverable:** Enhanced service monitoring with detailed metrics

---

### Part 5: Integration & Polish (1 hour)

#### Step 5.1: Layout Improvements (30 min)
```jsx
// Update App.jsx layout
- Add tabbed interface
  * Home: Service Status + Chat
  * Audio: Audio Tester
  * Debug: Debug Panel
  * Tests: Test Runner
  * Tools: Tool Log (existing)

- Responsive design
  * Mobile-friendly tabs
  * Collapsible panels
  * Keyboard shortcuts

- Dark/Light mode toggle
```

#### Step 5.2: Error Handling & UX (20 min)
- Add loading states for all async operations
- Add error toast notifications
- Add success confirmations
- Improve WebSocket reconnection UX
- Add helpful tooltips

#### Step 5.3: Documentation (10 min)
- Update docs/GUI_SETUP.md with new features
- Add screenshots or diagrams
- Document API endpoints
- Add keyboard shortcuts reference

**Deliverable:** Polished, production-ready GUI with all enhancements

---

## E. FILES TO CREATE

### Frontend Components (React)
```
src/gui/frontend/src/components/
├── DebugPanel.jsx          # Debug interface (new)
├── AudioTester.jsx         # Audio testing (new)
├── TestRunner.jsx          # Test execution (new)
├── ServiceMetrics.jsx      # Enhanced service cards (new)
└── MessageLog.jsx          # Message bus viewer (new)
```

### Backend Service
```
src/services/test/
├── __init__.py
└── test_service.py         # Test execution service (new)
```

### Styles
```
src/gui/frontend/src/styles/
├── DebugPanel.css          # Debug panel styles (new)
├── AudioTester.css         # Audio tester styles (new)
└── TestRunner.css          # Test runner styles (new)
```

---

## F. FILES TO MODIFY

### Frontend
- `src/gui/frontend/src/App.jsx` - Add new components and tabbed layout
- `src/gui/frontend/src/index.css` - Add global styles for new components
- `src/gui/frontend/src/main.jsx` - No changes needed

### Backend
- `src/services/gui/gui_service.py` - Add new API endpoints
- `src/main.py` - Add TestService to orchestrator
- `src/core/config.py` - Add test service configuration

### Documentation
- `docs/GUI_SETUP.md` - Document new features
- `DEVELOPMENT_LOG.md` - Add Phase 2D entry

---

## G. API ENDPOINTS (New)

### Audio Management
```
GET  /api/audio/devices          # List available devices
POST /api/audio/device           # Set input/output device
POST /api/stt/transcribe         # Upload audio for transcription
POST /api/tts/generate           # Generate speech from text
```

### Test Execution
```
POST /api/tests/run              # Run test suite
GET  /api/tests/result/{job_id}  # Get test result
GET  /api/coverage               # Get coverage data
GET  /api/coverage/html          # Serve coverage HTML report
```

### Debug & Monitoring
```
GET  /api/debug/messages         # Get recent message bus traffic
GET  /api/debug/logs             # Get recent service logs
GET  /api/services/metrics       # Get detailed service metrics
```

---

## H. WEBSOCKET MESSAGES (New)

### From Backend to Frontend
```json
{
  "type": "bus_message",
  "data": {
    "channel": "stt.transcription",
    "message": {...},
    "timestamp": "2025-12-05T12:00:00"
  }
}
```

```json
{
  "type": "log_message",
  "data": {
    "level": "INFO",
    "service": "tts_service",
    "message": "Speech generated",
    "timestamp": "2025-12-05T12:00:00"
  }
}
```

```json
{
  "type": "test_progress",
  "data": {
    "total": 52,
    "passed": 20,
    "failed": 0,
    "running": "test_audio_pipeline.py::test_full_audio_pipeline"
  }
}
```

---

## I. TESTING PLAN

### Manual Testing

#### Test 1: Debug Panel
1. Start Freya and open GUI
2. Open Debug Panel (Ctrl+D or tab)
3. Send a message via chat
4. **Verify:** Message appears in bus traffic log
5. **Verify:** Transcription, LLM, and TTS messages visible
6. Filter by channel: `llm.*`
7. **Verify:** Only LLM messages shown

#### Test 2: Audio Tester
1. Navigate to Audio tab
2. Click "List Devices" button
3. **Verify:** Available devices shown in dropdowns
4. Select different input device
5. **Verify:** Audio Manager updates (check status)
6. Type "Hello Freya" in TTS field
7. Click "Generate Speech"
8. **Verify:** Audio plays in browser

#### Test 3: Recording & STT
1. Click "Start Recording" button
2. Speak: "Testing STT from GUI"
3. Click "Stop Recording"
4. **Verify:** Recording duration shown
5. Click "Transcribe" button
6. **Verify:** Transcription appears after ~2 seconds
7. **Verify:** Matches spoken text

#### Test 4: Test Runner
1. Navigate to Tests tab
2. Click "Run All Tests" button
3. **Verify:** Spinner shows while running
4. **Verify:** Results appear after ~15 seconds
5. **Verify:** Pass/fail counts accurate
6. Click on failed test
7. **Verify:** Error message and stack trace visible

#### Test 5: Coverage Visualization
1. After tests complete, view Coverage section
2. **Verify:** Overall percentage shown
3. **Verify:** Module breakdown displayed
4. Click "View HTML Report"
5. **Verify:** Coverage report opens in new tab

### Automated Testing

Create test files:
- `tests/unit/test_test_service.py` - Unit tests for TestService
- `tests/integration/test_gui_audio_tester.py` - Integration test for audio testing
- `tests/integration/test_gui_test_runner.py` - Integration test for test runner

---

## J. CONFIGURATION

### Add to .env.example
```bash
# Test Service Configuration
TEST_SERVICE_ENABLED=true
TEST_COVERAGE_MIN=50
TEST_TIMEOUT=300  # 5 minutes max for test execution

# GUI Debug Settings
GUI_DEBUG_MESSAGE_BUFFER=100
GUI_DEBUG_LOG_BUFFER=200
GUI_ENABLE_TEST_RUNNER=true
```

### Add to src/core/config.py
```python
# Test Service Configuration
test_service_enabled: bool = Field(
    default=True,
    description="Enable test execution service"
)

test_coverage_min: int = Field(
    default=50,
    description="Minimum required test coverage percentage",
    ge=0, le=100
)

test_timeout: int = Field(
    default=300,
    description="Maximum test execution time in seconds",
    ge=60, le=600
)

# GUI Debug Configuration
gui_debug_message_buffer: int = Field(
    default=100,
    description="Number of message bus messages to buffer",
    ge=10, le=1000
)

gui_debug_log_buffer: int = Field(
    default=200,
    description="Number of log messages to buffer",
    ge=10, le=1000
)

gui_enable_test_runner: bool = Field(
    default=True,
    description="Enable test runner in GUI"
)
```

---

## K. POTENTIAL ISSUES & MITIGATIONS

### Issue 1: Test Execution Performance
**Problem:** Running tests from GUI may be slow or block the interface.

**Mitigation:**
- Run tests in subprocess (non-blocking)
- Use asyncio to stream results
- Add cancel button for long-running tests
- Show progress indicator

### Issue 2: Audio Device Permission
**Problem:** Browser may block microphone access.

**Mitigation:**
- Use HTTPS in production (or localhost in dev)
- Show clear permission request dialog
- Add troubleshooting guide
- Provide alternative file upload method

### Issue 3: WebSocket Message Volume
**Problem:** Debug panel may receive too many messages, causing lag.

**Mitigation:**
- Implement message filtering on backend
- Use circular buffer (max 100-200 messages)
- Add pause/resume button
- Virtualize message list (only render visible items)

### Issue 4: Browser Audio Format Compatibility
**Problem:** Generated TTS audio may not play in all browsers.

**Mitigation:**
- Convert audio to MP3 or WAV on backend
- Use HTML5 Audio element (broad support)
- Add format fallbacks
- Provide download option

### Issue 5: Test Output Parsing
**Problem:** pytest output may be difficult to parse reliably.

**Mitigation:**
- Use pytest JSON report plugin
- Parse structured output (--json-report)
- Handle unexpected output gracefully
- Cache parsed results

---

## L. ROLLBACK PLAN

If Phase 2D implementation causes issues:

1. **Frontend Rollback:**
   ```bash
   cd src/gui/frontend
   git checkout main -- src/components/
   npm run build
   ```

2. **Backend Rollback:**
   ```bash
   # Remove TestService from main.py
   # Remove new API endpoints from gui_service.py
   # Restart services
   ```

3. **Verification:**
   - Ensure basic GUI still works
   - Check WebSocket connection
   - Verify service status panel
   - Test chat functionality

4. **Checklist Before Rollback:**
   - [ ] Basic GUI functionality works
   - [ ] WebSocket connection stable
   - [ ] No breaking changes to existing features
   - [ ] Can switch between new and old UI

---

## M. DEPENDENCIES

### NPM Packages (Frontend)
```json
{
  "devDependencies": {
    "chart.js": "^4.4.0",           // For coverage charts
    "react-chartjs-2": "^5.2.0",    // React wrapper for Chart.js
    "react-syntax-highlighter": "^15.5.0",  // For log/error display
    "prism-react-renderer": "^2.3.1"        // Code highlighting
  }
}
```

### Python Packages (Backend)
```python
# Add to requirements.txt
pytest-json-report>=1.5.0  # JSON output for test results
coverage[toml]>=7.3.0      # Coverage with TOML support
```

---

## N. TIMELINE ESTIMATE

### Part 1: Debug Panel (2-3 hours)
- Component: 1 hour
- Backend: 30 min
- Integration: 30 min
- Testing: 30-60 min

### Part 2: Audio Tester (2-3 hours)
- Device Selector: 1 hour
- Recording: 1 hour
- TTS Testing: 30 min
- Backend: 30 min
- Testing: 30-60 min

### Part 3: Test Runner (2-3 hours)
- TestService: 1.5 hours
- Component: 1 hour
- Backend: 30 min
- Testing: 30-60 min

### Part 4: Service Monitoring (1 hour)
- Metrics Component: 45 min
- Integration: 15 min

### Part 5: Polish (1 hour)
- Layout: 30 min
- UX: 20 min
- Docs: 10 min

**Total: 6-8 hours** (assuming no major blockers)

---

## O. SUCCESS METRICS

### Functionality
- ✅ All 5 new components working
- ✅ All new API endpoints functional
- ✅ WebSocket messages flowing correctly
- ✅ Audio recording and playback works
- ✅ Test execution completes successfully

### Quality
- ✅ No console errors in browser
- ✅ No backend errors in logs
- ✅ Responsive design works on mobile
- ✅ Dark mode looks good
- ✅ Performance acceptable (<100ms UI updates)

### User Experience
- ✅ Intuitive navigation
- ✅ Clear error messages
- ✅ Loading states for async operations
- ✅ Helpful tooltips and hints
- ✅ Keyboard shortcuts work

### Documentation
- ✅ GUI_SETUP.md updated
- ✅ API endpoints documented
- ✅ Component usage explained
- ✅ Screenshots/diagrams added

---

## P. NEXT STEPS AFTER PHASE 2D

### Option 1: Fix Immediate Issues (2 hours)
- Add `publish_metrics` method to BaseService
- Review and fix health check logic
- Fix test mock setup issues

### Option 2: Phase 3 (Multi-Room) (2-3 weeks)
- Multi-room audio coordination
- Wake word detection
- Location awareness
- Conversation windowing

### Option 3: Production Deployment (1 week)
- Create DEPLOYMENT.md
- Set up systemd services
- Configure production environment
- Add monitoring and alerting

---

## Q. NOTES & CONSIDERATIONS

### Design Decisions

**Decision:** Use tabs vs. separate pages
**Rationale:** Tabs keep all functionality accessible without page reloads, better for real-time monitoring.

**Decision:** Run tests in subprocess
**Rationale:** Prevents blocking the main application, allows cancellation.

**Decision:** Buffer messages on backend
**Rationale:** Reduces WebSocket traffic, improves performance, allows history retrieval.

**Decision:** Use Chart.js for visualization
**Rationale:** Lightweight, well-documented, React wrapper available.

### Future Enhancements (Post-Phase 2D)

1. **Audio Waveform Visualization**
   - Show real-time audio input levels
   - Display waveform during recording
   - Visual feedback for speech detection

2. **Performance Profiling**
   - Measure latency at each pipeline stage
   - Graph performance over time
   - Identify bottlenecks

3. **Configuration UI**
   - Edit config.py settings from GUI
   - Save/load configuration profiles
   - Restart services with new config

4. **Advanced Debugging**
   - Step-through message flow
   - Breakpoints on channels
   - Message replay/simulation

---

## R. APPROVAL CHECKLIST

Before starting implementation:

- [ ] User approves overall approach
- [ ] Timeline acceptable (6-8 hours)
- [ ] Dependencies can be installed
- [ ] Design mockups reviewed (if needed)
- [ ] Priority features confirmed
- [ ] Success criteria clear
- [ ] Rollback plan understood

---

**Plan Status:** 📋 **READY FOR REVIEW**

Please review this plan and confirm:
1. Are these the right features to build?
2. Is the timeline reasonable?
3. Any features you want to add/remove/modify?
4. Should we proceed with implementation?
