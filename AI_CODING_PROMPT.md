# AI Coding Assistant Prompt - Freya v2.0

**Purpose**: This document provides comprehensive instructions for AI coding assistants (like Claude, GPT-4, etc.) working on the Freya v2.0 project. Use this as your initial prompt when starting a coding session.

**Version**: 1.0  
**Last Updated**: 2025-12-03

---

## Initial Prompt for AI Coding Assistants

Copy and paste the following prompt when starting a new coding session:

```
You are an expert Python developer working on Freya v2.0, a sophisticated personal AI assistant with multi-room audio/video capabilities, persistent memory, and extensive tool integration.

REPOSITORY: https://github.com/MrPink1977/freya_v2

YOUR TASK:
1. Assess the current state of the repository
2. Review what has been completed
3. Identify what needs to be done according to the project plan
4. Create a detailed plan for the next development chunk
5. Present the plan for review and confirmation before proceeding

ASSESSMENT PROCESS:

Step 1: READ THESE FILES FIRST (in order)
- README.md - Project overview
- ROADMAP.md - 12-week implementation plan
- ARCHITECTURE.md - System design
- DEVELOPMENT_LOG.md - Recent changes and current status
- CODE_QUALITY_REPORT.md - Quality standards
- CONTRIBUTING.md - Development guidelines

Step 2: ANALYZE CURRENT STATE
- Check which phase we're in (see ROADMAP.md)
- Review recent commits (git log)
- Check DEVELOPMENT_LOG.md for latest changes
- Identify completed services vs. pending services
- Note any known issues or blockers

Step 3: IDENTIFY NEXT CHUNK
- Based on ROADMAP.md, determine the next logical chunk of work
- Typical chunks:
  * Implement a new service (e.g., STT Service, TTS Service)
  * Add a major feature (e.g., multi-room support, memory integration)
  * Enhance existing functionality (e.g., error handling, testing)
  * Create documentation or tooling
- Chunk size: 2-4 hours of focused development

Step 4: CREATE DETAILED PLAN
Your plan should include:

A. OBJECTIVE
   - Clear statement of what will be accomplished
   - Success criteria

B. PREREQUISITES
   - What must be in place before starting
   - Dependencies on other services
   - Required external resources (API keys, models, etc.)

C. IMPLEMENTATION STEPS
   - Numbered list of specific tasks
   - File-by-file breakdown
   - Estimated time for each step

D. FILES TO CREATE/MODIFY
   - List all files that will be created
   - List all files that will be modified
   - Specify what changes will be made to each

E. TESTING PLAN
   - How to verify the implementation works
   - Manual testing steps
   - Unit tests to create (if applicable)

F. DOCUMENTATION UPDATES
   - Which docs need updating
   - What information needs to be added

G. INTEGRATION POINTS
   - How this integrates with existing services
   - Message bus channels to use
   - Configuration parameters needed

H. POTENTIAL ISSUES
   - Known challenges or risks
   - Mitigation strategies

I. ROLLBACK PLAN
   - How to revert if something goes wrong
   - What to check before committing

Step 5: PRESENT PLAN FOR CONFIRMATION
Format your plan clearly and ask:
"Does this plan look good? Should I proceed with implementation, or would you like me to adjust anything?"

WAIT FOR CONFIRMATION before writing any code.

CODE QUALITY STANDARDS:

When writing code, you MUST follow these standards:

1. TYPE HINTS
   - Every function and method must have complete type hints
   - Use proper types: Dict, List, Optional, Any, etc.
   - Example:
     ```python
     async def process_data(self, data: Dict[str, Any]) -> List[str]:
         pass
     ```

2. DOCSTRINGS
   - Every module, class, and public method needs a docstring
   - Use Google style format
   - Include: description, Args, Returns, Raises, Example
   - Example:
     ```python
     async def process_audio(self, audio_data: bytes) -> str:
         """
         Process raw audio data and return transcription.
         
         Args:
             audio_data: Raw audio bytes in WAV format
             
         Returns:
             Transcribed text string
             
         Raises:
             AudioError: If audio processing fails
             
         Example:
             >>> text = await service.process_audio(wav_bytes)
         """
     ```

3. ERROR HANDLING
   - Create custom exceptions for your module
   - Use try-except with specific exceptions
   - Always chain exceptions with `from e`
   - Log errors appropriately
   - Example:
     ```python
     try:
         result = await operation()
     except SpecificError as e:
         logger.error(f"[{self.name}] Operation failed: {e}")
         raise MyServiceError(f"Failed: {e}") from e
     ```

4. LOGGING
   - Use loguru logger
   - Include service name: `logger.info(f"[{self.name}] Message")`
   - Use appropriate levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Add emoji for visual clarity: ✅ ❌ ⚠️ 📤 📥 📨
   - Example:
     ```python
     logger.debug(f"[{self.name}] Processing {len(items)} items")
     logger.info(f"[{self.name}] ✓ Service started successfully")
     logger.error(f"[{self.name}] ❌ Failed to connect: {e}")
     ```

5. SERVICE STRUCTURE
   - All services inherit from BaseService
   - Implement: initialize(), start(), stop(), health_check()
   - Use message bus for communication
   - Publish status and metrics
   - Example:
     ```python
     class MyService(BaseService):
         def __init__(self, message_bus: MessageBus) -> None:
             super().__init__("my_service", message_bus)
             
         async def initialize(self) -> None:
             # Setup code
             self._healthy = True
             
         async def start(self) -> None:
             self._mark_started()
             await self.message_bus.subscribe("my.channel", self._handler)
             await self.publish_status("started")
             
         async def stop(self) -> None:
             await self.message_bus.unsubscribe("my.channel")
             self._mark_stopped()
             await self.publish_status("stopped")
     ```

6. CONFIGURATION
   - Add new config parameters to src/core/config.py
   - Use Pydantic Field with validation
   - Include description and examples
   - Example:
     ```python
     my_parameter: str = Field(
         default="default_value",
         description="What this parameter does",
         examples=["example1", "example2"]
     )
     ```

7. MESSAGE BUS CONVENTIONS
   - Channel naming: `{source}.{data_type}`
   - Examples: `stt.transcription`, `llm.response`, `audio.stream`
   - Service status: `service.{service_name}.status`
   - Service metrics: `service.{service_name}.metrics`
   - Always include timestamp in messages

8. FILE ORGANIZATION
   - One service per file
   - Service file in src/services/{service_name}/{service_name}.py
   - Supporting files in same directory
   - __init__.py in every directory

TESTING REQUIREMENTS:

Every new service or feature MUST include comprehensive tests. Follow these guidelines:

1. TEST STRUCTURE
   - Unit tests in tests/unit/ for individual components
   - Integration tests in tests/integration/ for multi-component interactions
   - Shared fixtures in tests/conftest.py
   - Mock utilities in tests/mocks/
   - Use pytest markers: @pytest.mark.unit, @pytest.mark.integration, @pytest.mark.slow

2. COVERAGE EXPECTATIONS
   - Minimum: 70% coverage for new code
   - Core modules: Aim for 85%+ coverage
   - All public methods must be tested
   - Test both success and failure paths
   - Test edge cases and error conditions

3. WRITING UNIT TESTS
   Example:
   ```python
   import pytest
   from unittest.mock import AsyncMock, MagicMock, patch
   
   @pytest.mark.unit
   @pytest.mark.asyncio
   async def test_service_initialization(mock_message_bus, mock_config):
       """Test that MyService initializes correctly."""
       service = MyService(mock_message_bus)
       await service.initialize()
       
       assert service._healthy is True
       assert service.name == "my_service"
       mock_message_bus.subscribe.assert_called_once()
   
   @pytest.mark.unit
   @pytest.mark.asyncio
   async def test_error_handling(mock_message_bus):
       """Test that service handles errors gracefully."""
       service = MyService(mock_message_bus)
       
       # Simulate error
       mock_message_bus.publish.side_effect = Exception("Connection error")
       
       with pytest.raises(MyServiceError) as exc_info:
           await service._process_data({})
       
       assert "Connection error" in str(exc_info.value)
       assert service._error_count > 0
   ```

4. WRITING INTEGRATION TESTS
   Example:
   ```python
   @pytest.mark.integration
   @pytest.mark.asyncio
   async def test_full_pipeline(mock_message_bus, mock_whisper, mock_ollama, mock_mcp_gateway):
       """Test complete audio pipeline: STT -> LLM -> TTS."""
       # Setup services
       stt = STTService(mock_message_bus)
       llm = LLMEngine(mock_message_bus)
       tts = TTSService(mock_message_bus)
       
       await stt.initialize()
       await llm.initialize()
       await tts.initialize()
       
       # Simulate audio input
       audio_data = generate_test_audio()
       await mock_message_bus.publish("audio.input.stream", {"audio": audio_data})
       
       # Wait for pipeline to complete
       await asyncio.sleep(0.1)
       
       # Verify message flow
       assert mock_message_bus.publish.call_count >= 3
       # Verify STT published transcription
       # Verify LLM published response
       # Verify TTS published audio
   ```

5. MOCKING STRATEGIES
   - Mock external dependencies (Redis, Ollama, PyAudio, ElevenLabs)
   - Use shared fixtures from conftest.py
   - Create realistic mock responses
   - Example mock fixtures:
     * mock_message_bus: Mocked MessageBus
     * mock_redis: Mocked aioredis client
     * mock_ollama: Mocked Ollama client
     * mock_pyaudio: Mocked PyAudio instance
     * mock_mcp_gateway: Mocked MCP Gateway
     * sample_audio_data: Synthetic audio for testing

6. ASYNC TESTING
   - Always use @pytest.mark.asyncio for async tests
   - Use await for async operations
   - Use asyncio.sleep() for timing-dependent tests
   - Use asyncio.gather() for concurrent operations
   - Example:
   ```python
   @pytest.mark.asyncio
   async def test_concurrent_requests():
       # Create multiple tasks
       tasks = [service.process(data) for data in test_data]
       # Run concurrently
       results = await asyncio.gather(*tasks)
       # Verify all succeeded
       assert all(r.success for r in results)
   ```

7. RUNNING TESTS
   ```bash
   # All tests with coverage
   pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
   
   # Unit tests only
   pytest tests/unit/ -v
   
   # Integration tests only
   pytest tests/integration/ -v
   
   # Specific test
   pytest tests/unit/test_my_service.py::test_initialization -v
   
   # With markers
   pytest -m unit -v
   pytest -m "not slow" -v
   ```

8. TEST DOCUMENTATION
   - Every test needs a clear docstring
   - Explain what is being tested and why
   - Document any complex setup or mocking
   - Reference TESTING.md for comprehensive guide

SECURITY BEST PRACTICES:

When implementing security features, follow these patterns from Phase 2:

1. JWT AUTHENTICATION
   ```python
   from datetime import datetime, timedelta
   import jwt
   
   class TokenManager:
       def __init__(self, secret_key: str, token_expiry: int):
           self.secret_key = secret_key
           self.token_expiry = token_expiry
       
       def generate_token(self, session_id: str) -> str:
           """Generate JWT token for session."""
           payload = {
               "session_id": session_id,
               "exp": datetime.utcnow() + timedelta(seconds=self.token_expiry),
               "iat": datetime.utcnow()
           }
           return jwt.encode(payload, self.secret_key, algorithm="HS256")
       
       def validate_token(self, token: str) -> Optional[str]:
           """Validate JWT and return session_id."""
           try:
               payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
               return payload.get("session_id")
           except jwt.ExpiredSignatureError:
               logger.warning("Token expired")
               return None
           except jwt.InvalidTokenError:
               logger.warning("Invalid token")
               return None
   ```

2. RATE LIMITING (Sliding Window)
   ```python
   from collections import deque
   from datetime import datetime, timedelta
   
   class RateLimiter:
       def __init__(self, rate: float, burst: int):
           self.rate = rate  # requests per second
           self.burst = burst  # maximum burst size
           self.requests: Dict[str, deque] = {}
       
       async def check_limit(self, key: str) -> bool:
           """Check if request is within rate limit."""
           now = datetime.now()
           
           if key not in self.requests:
               self.requests[key] = deque()
           
           # Remove old requests outside window
           window_start = now - timedelta(seconds=1)
           while self.requests[key] and self.requests[key][0] < window_start:
               self.requests[key].popleft()
           
           # Check if at limit
           if len(self.requests[key]) >= self.burst:
               return False
           
           # Add current request
           self.requests[key].append(now)
           return True
   ```

3. SESSION MANAGEMENT
   ```python
   class SessionManager:
       def __init__(self, session_timeout: int, max_sessions: int):
           self.sessions: Dict[str, SessionInfo] = {}
           self.session_timeout = session_timeout
           self.max_sessions = max_sessions
       
       def create_session(self, client_ip: str, user_agent: str) -> str:
           """Create new session, enforce max sessions."""
           if len(self.sessions) >= self.max_sessions:
               # Clean up expired sessions
               self.cleanup_expired_sessions()
               
               if len(self.sessions) >= self.max_sessions:
                   raise TooManySessionsError()
           
           session_id = str(uuid.uuid4())
           self.sessions[session_id] = SessionInfo(
               session_id=session_id,
               created_at=datetime.now(),
               last_activity=datetime.now(),
               client_ip=client_ip,
               user_agent=user_agent
           )
           return session_id
   ```

4. WEBSOCKET SECURITY
   ```python
   @app.websocket("/ws")
   async def websocket_endpoint(
       websocket: WebSocket,
       token: str = Query(...),
       request: Request = None
   ):
       # Validate JWT token
       session_id = token_manager.validate_token(token)
       if not session_id:
           await websocket.close(code=1008, reason="Invalid token")
           return
       
       # Check rate limit
       client_ip = request.client.host
       if not await rate_limiter.check_limit(client_ip):
           await websocket.close(code=1008, reason="Rate limit exceeded")
           return
       
       # Accept connection
       await websocket.accept()
       
       try:
           while True:
               data = await websocket.receive_json()
               
               # Check per-session rate limit
               if not await rate_limiter.check_limit(session_id):
                   await websocket.send_json({"error": "Rate limit exceeded"})
                   continue
               
               # Process message
               await handle_message(data)
               
       except WebSocketDisconnect:
           session_manager.remove_session(session_id)
   ```

PHASE 2 IMPLEMENTATION PATTERNS:

Use these patterns from Phase 2 as reference for new services:

1. AUDIO SERVICE PATTERN (TTS Service)
   ```python
   class TTSService(BaseService):
       def __init__(self, message_bus: MessageBus) -> None:
           super().__init__("tts_service", message_bus)
           self.generation_count = 0
           self.total_characters = 0
       
       async def initialize(self) -> None:
           """Initialize service and check dependencies."""
           if not config.elevenlabs_api_key:
               raise TTSServiceError("ElevenLabs API key not configured")
           self._healthy = True
       
       async def start(self) -> None:
           """Start service and subscribe to channels."""
           self._mark_started()
           await self.message_bus.subscribe("llm.final_response", self._handle_llm_response)
           await self.message_bus.subscribe("tts.generate", self._handle_tts_request)
           await self.publish_status("started")
       
       async def _handle_llm_response(self, data: Dict[str, Any]) -> None:
           """Process LLM response and generate speech."""
           text = data.get("text", "")
           if len(text) < 5:  # Skip very short responses
               return
           
           try:
               audio = await self._generate_speech(text)
               await self.message_bus.publish("audio.output.stream", {
                   "audio": audio,
                   "format": "mp3",
                   "timestamp": datetime.now().isoformat()
               })
           except Exception as e:
               logger.error(f"[{self.name}] ❌ Speech generation failed: {e}")
               self.increment_error_count()
   ```

2. MCP GATEWAY INTEGRATION
   ```python
   async def _call_mcp_tool(self, server: str, tool: str, arguments: Dict[str, Any]) -> Any:
       """Call MCP tool via gateway and wait for result."""
       request_id = str(uuid.uuid4())
       result_channel = f"mcp.tool.result.{request_id}"
       
       # Subscribe to result channel
       result = asyncio.Future()
       
       async def handle_result(data: Dict[str, Any]):
           if not result.done():
               result.set_result(data)
       
       await self.message_bus.subscribe(result_channel, handle_result)
       
       try:
           # Publish tool execution request
           await self.message_bus.publish("mcp.tool.execute", {
               "request_id": request_id,
               "server": server,
               "tool": tool,
               "arguments": arguments,
               "result_channel": result_channel
           })
           
           # Wait for result with timeout
           return await asyncio.wait_for(result, timeout=30.0)
           
       finally:
           await self.message_bus.unsubscribe(result_channel)
   ```

3. AUDIO I/O WITH THREADING
   ```python
   class AudioManager(BaseService):
       def __init__(self, message_bus: MessageBus) -> None:
           super().__init__("audio_manager", message_bus)
           self.pyaudio = None
           self.input_stream = None
           self.output_stream = None
           self.input_thread = None
           self.output_thread = None
           self.input_queue = queue.Queue(maxsize=100)
           self.output_queue = queue.Queue(maxsize=100)
           self._input_running = False
           self._output_running = False
       
       def _input_loop(self):
           """Input thread loop - reads from mic and publishes to message bus."""
           while self._input_running:
               try:
                   data = self.input_stream.read(config.audio_chunk_size, exception_on_overflow=False)
                   self.input_queue.put(data, block=False)
                   
                   # Async publish from thread
                   asyncio.run_coroutine_threadsafe(
                       self._publish_audio(data),
                       self._event_loop
                   )
               except queue.Full:
                   logger.warning(f"[{self.name}] Input queue full, dropping frame")
               except Exception as e:
                   logger.error(f"[{self.name}] Input error: {e}")
       
       def _output_loop(self):
           """Output thread loop - reads from queue and plays to speaker."""
           while self._output_running:
               try:
                   data = self.output_queue.get(timeout=0.1)
                   self.output_stream.write(data)
               except queue.Empty:
                   continue
               except Exception as e:
                   logger.error(f"[{self.name}] Output error: {e}")
   ```

4. COMPREHENSIVE FIXTURE SETUP (conftest.py)
   ```python
   @pytest.fixture
   def mock_message_bus():
       """Mock MessageBus with realistic pub/sub behavior."""
       bus = AsyncMock(spec=MessageBus)
       subscriptions = {}
       
       async def mock_publish(channel, data):
           # Trigger subscribed callbacks
           if channel in subscriptions:
               for callback in subscriptions[channel]:
                   await callback(data)
       
       async def mock_subscribe(channel, callback):
           if channel not in subscriptions:
               subscriptions[channel] = []
           subscriptions[channel].append(callback)
       
       bus.publish.side_effect = mock_publish
       bus.subscribe.side_effect = mock_subscribe
       
       return bus
   ```

CODE QUALITY CHECKLIST:

Before committing, verify:
- [ ] All functions have type hints
- [ ] All public methods have docstrings
- [ ] Error handling with custom exceptions
- [ ] Logging at appropriate levels with emojis
- [ ] Tests written (unit + integration if applicable)
- [ ] Test coverage ≥70% for new code
- [ ] All tests passing locally
- [ ] No hardcoded secrets or API keys
- [ ] Configuration via environment variables
- [ ] Health checks implemented for services
- [ ] Metrics tracking for important operations
- [ ] Graceful shutdown with cleanup
- [ ] Documentation updated (README, DEVELOPMENT_LOG, etc.)

AFTER IMPLEMENTATION:

1. UPDATE DEVELOPMENT_LOG.md
   - Add entry with date, changes, rationale, impact
   - Update metrics and status

2. UPDATE CHANGELOG.md (if applicable)
   - Add to [Unreleased] section
   - Note any breaking changes

3. TEST THOROUGHLY
   - Run manual tests
   - Verify integration with other services
   - Check logs for errors

4. COMMIT WITH PROPER MESSAGE
   - Format: `<type>: <subject>`
   - Types: feat, fix, docs, style, refactor, test, chore
   - Include detailed body explaining changes

5. UPDATE RELEVANT DOCS
   - Update README if user-facing changes
   - Update ARCHITECTURE if design changes
   - Update PHASE_X_SETUP if setup changes

REFERENCE IMPLEMENTATIONS:

Look at these files as examples of proper implementation:
- src/core/message_bus.py - Comprehensive error handling
- src/core/base_service.py - Service structure
- src/services/llm/llm_engine.py - Full service implementation
- src/main.py - Orchestration and lifecycle management

CURRENT PROJECT STATE:

Phase 1 (Foundation): ✅ COMPLETE
- MessageBus implemented with Redis
- BaseService abstract class created
- Configuration management with Pydantic
- LLM Engine with Ollama integration
- Docker Compose setup
- All code enhanced to production quality

Phase 1.5 (MCP Gateway): ✅ COMPLETE
- MCP Gateway service operational
- 6 MCP servers connected (filesystem, web-search, weather, shell, time, calculator)
- Tool calling integrated in LLM Engine
- Zero API keys for local tools

Phase 1.75 (GUI Dashboard): ✅ COMPLETE
- FastAPI backend with WebSocket support
- React frontend with real-time updates
- Service status monitoring
- Text chat interface
- Tool call visualization

Phase 2 (Audio Pipeline & Backend Infrastructure): ✅ COMPLETE
- Testing framework (pytest, pytest-asyncio, pytest-cov)
- WebSocket security (JWT auth, rate limiting)
- TTS Service with ElevenLabs via MCP
- Audio Manager with PyAudio
- Integration tests for audio pipeline
- CI/CD pipeline with GitHub Actions
- 43+ tests, 70% coverage

Phase 3 (Multi-Room & Location Awareness): ⏳ NEXT
- Multi-room audio coordination
- Location awareness
- Wake word detection
- Conversation windowing

Phase 4-6: See ROADMAP.md for details

Now, please:
1. Assess the current repository state
2. Determine what needs to be done next
3. Create a detailed plan for the next chunk
4. Present the plan for my review and confirmation

Do NOT start coding until I confirm the plan.
```

---

## Quick Start for AI Assistants

If you're an AI assistant starting work on Freya v2.0:

1. **Read the prompt above** - This is your primary instruction set

2. **Clone the repository** (if needed):
   ```bash
   git clone https://github.com/MrPink1977/freya_v2.git
   cd freya_v2
   ```

3. **Read these files in order**:
   - README.md
   - ROADMAP.md
   - DEVELOPMENT_LOG.md
   - ARCHITECTURE.md
   - CODE_QUALITY_REPORT.md
   - CONTRIBUTING.md

4. **Assess the current state**:
   ```bash
   git log --oneline -10
   git status
   ```

5. **Create your plan** following the format in the prompt

6. **Wait for confirmation** before writing code

7. **Follow the quality standards** when implementing

8. **Update documentation** when done

---

## Example Plan Format

Here's an example of a well-structured plan:

```markdown
# Development Plan: STT Service Implementation

## A. OBJECTIVE
Implement the Speech-to-Text (STT) Service using faster-whisper for local GPU-accelerated transcription.

Success Criteria:
- STT Service can transcribe audio from message bus
- GPU acceleration working
- Integration with Audio Manager
- Proper error handling and logging
- Health checks implemented

## B. PREREQUISITES
- Phase 1 complete ✅
- NVIDIA GPU available ✅
- faster-whisper model downloaded
- Audio Manager implemented (dependency)

## C. IMPLEMENTATION STEPS
1. Create STTService class inheriting from BaseService (30 min)
2. Implement faster-whisper integration (45 min)
3. Add message bus subscriptions for audio streams (20 min)
4. Implement transcription logic with error handling (40 min)
5. Add health checks and metrics (20 min)
6. Test with sample audio (30 min)
7. Update documentation (15 min)

Total estimated time: 3 hours 20 minutes

## D. FILES TO CREATE/MODIFY

Create:
- src/services/stt/stt_service.py (main implementation)
- src/services/stt/__init__.py

Modify:
- src/core/config.py (add STT configuration parameters)
- src/main.py (add STT service to orchestrator)
- DEVELOPMENT_LOG.md (add entry)

## E. TESTING PLAN
Manual Testing:
1. Start Freya with docker-compose
2. Publish test audio to audio.stream channel
3. Verify transcription published to stt.transcription
4. Check logs for proper operation
5. Test error cases (invalid audio, timeout)

## F. DOCUMENTATION UPDATES
- DEVELOPMENT_LOG.md: Add implementation entry
- README.md: Update service status
- Add inline code documentation

## G. INTEGRATION POINTS
- Subscribes to: `audio.stream` (from Audio Manager)
- Publishes to: `stt.transcription` (for LLM Engine)
- Config: `stt_model`, `stt_language`, `stt_device`

## H. POTENTIAL ISSUES
- GPU memory usage with large models
  * Mitigation: Use "base" model by default, configurable
- Audio format compatibility
  * Mitigation: Validate format before processing
- Transcription latency
  * Mitigation: Use faster-whisper's streaming mode

## I. ROLLBACK PLAN
- Git revert if issues found
- STT Service is optional, system works without it
- Check: Message bus connectivity, GPU availability

Does this plan look good? Should I proceed?
```

---

## Tips for Effective AI Coding Sessions

### DO:
✅ Read all documentation before starting  
✅ Create a detailed plan and get confirmation  
✅ Follow the established code patterns  
✅ Write comprehensive tests  
✅ Update all relevant documentation  
✅ Commit with clear, descriptive messages  
✅ Ask questions if anything is unclear  

### DON'T:
❌ Start coding without a confirmed plan  
❌ Skip error handling or logging  
❌ Forget to update DEVELOPMENT_LOG.md  
❌ Ignore type hints or docstrings  
❌ Make breaking changes without discussion  
❌ Commit without testing  
❌ Leave TODO comments without tracking them  

---

## Common Tasks

### Adding a New Service

1. Create service file: `src/services/{name}/{name}_service.py`
2. Inherit from BaseService
3. Implement required methods
4. Add configuration to config.py
5. Add to main.py orchestrator
6. Write tests
7. Update documentation

### Adding a Configuration Parameter

1. Add to `src/core/config.py` with Field()
2. Include description and validation
3. Add to `.env.example`
4. Document in relevant service
5. Update PHASE_X_SETUP.md if user-facing

### Fixing a Bug

1. Reproduce the bug
2. Write a test that fails
3. Fix the bug
4. Verify test passes
5. Add error handling if missing
6. Update DEVELOPMENT_LOG.md
7. Commit with "fix:" prefix

### Adding Documentation

1. Identify what needs documentation
2. Write clear, comprehensive docs
3. Add examples where helpful
4. Update table of contents if applicable
5. Commit with "docs:" prefix

---

## Troubleshooting

### If the AI assistant seems confused:
- Point them to this file
- Ask them to read DEVELOPMENT_LOG.md
- Have them check the current git status
- Review the ROADMAP.md for context

### If code quality is inconsistent:
- Reference CODE_QUALITY_REPORT.md
- Point to example implementations
- Review CONTRIBUTING.md together

### If integration isn't working:
- Check ARCHITECTURE.md for message bus channels
- Verify configuration in config.py
- Review logs for connection issues
- Check Docker Compose services are running

---

## Version History

### Version 1.0 (2025-12-03)
- Initial version of AI coding prompt
- Comprehensive instructions for assessment and planning
- Code quality standards included
- Example plan format provided

---

**Remember**: This prompt is designed to ensure consistency, quality, and proper planning. Always follow the assessment → plan → confirm → implement → document workflow.
