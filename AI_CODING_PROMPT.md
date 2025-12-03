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

Phase 2 (Multi-room Audio): ⏳ NEXT
- Audio Manager for device management
- STT Service with faster-whisper
- TTS Service with ElevenLabs
- Multi-room coordination

Phase 3-6: See ROADMAP.md for details

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
