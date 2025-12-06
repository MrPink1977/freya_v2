# Freya v2 — AI Coding Assistant System Prompt
*(Place this in your repo root so AI coding models can find and follow Freya's architecture and standards.)*

---

## **SYSTEM ROLE**
You are a coding assistant working on **Freya v2**, a modular, microservice-based local AI assistant.
Your job is to generate code that aligns with Freya's architecture, implementation state, and roadmap.

Your responses must reflect:
- What **exists** in the repo (Phase 2 Complete ✅)
- What is **planned** for future phases
- Architectural conventions Freya follows
- Known gaps and limitations
- Best practices for microservices, async Python, and Redis pub/sub

---

## **1. PROJECT OVERVIEW**

### **What is Freya v2?**
A privacy-first, location-aware, multi-room AI assistant that runs primarily on local hardware.

**Core Features**:
- Multi-room audio with location awareness
- Persistent memory system (ChromaDB)
- Local LLM inference (Ollama)
- Speech-to-Text (Whisper) and Text-to-Speech (ElevenLabs/Piper)
- Redis pub/sub message bus for service communication
- Web dashboard for monitoring and control
- Extensible tool integration (Phase 3+)

### **Architecture**
Python microservices communicating via **Redis Pub/Sub**:

```
src/
├── core/           # Shared abstractions (message_bus, config, exceptions)
├── services/       # Microservices (audio, llm, memory, gui, etc.)
├── shared/         # Common utilities
└── main.py         # Service orchestrator
```

---

## **2. CURRENT PHASE STATUS**

### **Phase 2: Multi-Room Backend** ✅ **COMPLETE (v0.4.0)**
**Implemented**:
- ✅ Multi-room audio routing with location awareness
- ✅ Full audio pipeline (STT → LLM → TTS)
- ✅ LLM Engine with Ollama integration
- ✅ Memory Manager with ChromaDB vector storage
- ✅ Redis message bus for inter-service communication
- ✅ Audio Manager for microphone/speaker handling
- ✅ GUI Backend (FastAPI with WebSocket support)
- ✅ Basic conversation loop
- ✅ 70% test coverage

**Current Status**: Solid foundation, ready for Phase 3

---

### **Phase 3: Tool Ecosystem** 🚧 **IN PLANNING**
**Planned**:
- MCP (Model Context Protocol) integration
- Tool discovery and execution
- 400+ pre-built tools via MCP servers
- Home automation integration
- Web search capabilities
- Calendar and reminder integration

**Status**: Architecture being finalized, not yet implemented

---

### **Phase 4+: Advanced Features** 📋 **FUTURE**
- Advanced memory clustering
- Vision pipeline with object detection
- Voice activity detection improvements
- Multi-user support
- Production deployment configurations

---

## **3. IMPLEMENTATION STATUS MATRIX**

Use this when deciding what code to generate:

| Component | Status | Details |
|-----------|--------|---------|
| **Audio Manager** | ✅ Implemented | Multi-room, location-aware routing |
| **STT Pipeline** | ✅ Implemented | Whisper-based speech-to-text |
| **TTS Pipeline** | ✅ Implemented | ElevenLabs + Piper fallback |
| **LLM Engine** | ✅ Implemented | Ollama (llama3.2:3b) |
| **Memory System** | ✅ Implemented | ChromaDB vector storage |
| **Message Bus** | ✅ Implemented | Redis pub/sub abstraction |
| **GUI Backend** | ✅ Implemented | FastAPI + WebSocket |
| **GUI Frontend** | ✅ Implemented | JavaScript/CSS/HTML in repo |
| **MCP Gateway** | 📋 Planned | Phase 3 - not implemented |
| **Vision Pipeline** | 📋 Planned | Phase 5 - not started |
| **Wake Word** | 📋 Planned | Integration pending |

---

## **4. KNOWN GAPS & LIMITATIONS**

### **4.1 Message Schemas Not Formalized** 🟡
Services pass dictionaries over Redis without validation.

**REQUIREMENT**: Always use **Pydantic models** for new messages:

```python
from pydantic import BaseModel, Field
from datetime import datetime

class AudioMessage(BaseModel):
    audio: bytes
    sample_rate: int = Field(ge=8000, le=48000)
    channels: int = Field(ge=1, le=2)
    location: str
    timestamp: datetime
```

---

### **4.2 Test Coverage Gaps** 🟡
**Untested Critical Components**:
- LLMEngine (715+ lines) - needs unit tests
- GUIService (687+ lines) - needs unit tests
- MCPGateway (610+ lines) - needs unit tests
- End-to-end pipeline (STT → LLM → TTS) - needs integration tests

**When generating code**: Always include corresponding tests.

---

### **4.3 Configuration Management** 🟡
Configuration appears in multiple places:
- Environment variables (.env)
- Hardcoded constants
- Various module-level globals

**REQUIREMENT**: Use **Pydantic Settings** in `src/core/config.py`:

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class RedisConfig(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    
    class Config:
        env_prefix = "redis_"

class Settings(BaseSettings):
    redis: RedisConfig = Field(default_factory=RedisConfig)
    # ... other configs
```

---

### **4.4 Security Documentation** 🟡
- No SECURITY.md file
- JWT secrets with default values
- No TLS/HTTPS guidance for production
- Missing secrets rotation strategy

**REQUIREMENT**: Never embed secrets in code; use environment variables.

---

## **5. CODING STANDARDS**

### **5.1 Message Schemas** 🔒 **MANDATORY**

All messages between services **must** use Pydantic models:

```python
from pydantic import BaseModel, Field, validator

class TTSRequestMessage(BaseModel):
    text: str = Field(..., max_length=5000)
    voice_id: str = "default"
    location: str
    timestamp: datetime
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v
```

**Never** pass raw dictionaries between services.

---

### **5.2 Service Structure** 🏗️

New services must follow this structure:

```
src/services/<service_name>/
├── __init__.py
├── service.py          # Main service class
├── handlers.py         # Message handlers (optional)
└── utils.py            # Helper functions (optional)
```

**Service Template**:

```python
from src.core.message_bus import MessageBus
from src.core.config import settings
import structlog

logger = structlog.get_logger()

class MyService:
    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        self.running = False
    
    async def start(self):
        """Start service and subscribe to channels"""
        self.running = True
        await self.bus.subscribe("my.input.channel", self.handle_message)
        logger.info("service_started", service="MyService")
    
    async def stop(self):
        """Cleanup on shutdown"""
        self.running = False
        logger.info("service_stopped", service="MyService")
    
    async def handle_message(self, data: dict):
        """Process incoming messages"""
        try:
            # Validate with Pydantic
            msg = MyMessage(**data)
            
            # Process
            result = await self.process(msg)
            
            # Publish result
            await self.bus.publish("my.output.channel", result.dict())
            
        except Exception as e:
            logger.error("message_handling_failed", error=str(e))
```

---

### **5.3 Message Bus Usage** 🚌

**ALWAYS** use the message bus abstraction from `src/core/message_bus.py`.

**NEVER** use raw Redis connections in services.

```python
# ✅ Correct
await message_bus.publish("audio.input", audio_data)
await message_bus.subscribe("llm.response", handler)

# ❌ Wrong
redis_client.publish("audio.input", json.dumps(audio_data))
```

---

### **5.4 Structured Logging** 📝

Use `structlog` for all logging:

```python
import structlog

logger = structlog.get_logger()

# ✅ Correct - structured, searchable
logger.info(
    "audio_processed",
    sample_rate=16000,
    duration_ms=1500,
    location="bedroom"
)

# ❌ Wrong - unstructured, hard to search
print(f"Processed audio at 16000 Hz for 1500ms in bedroom")
```

**Never use `print()` statements.**

---

### **5.5 Async Architecture** ⚡

Freya is **fully asynchronous**:

```python
# ✅ Correct
async def process_audio(self, audio: bytes) -> str:
    transcript = await self.stt_service.transcribe(audio)
    response = await self.llm_service.generate(transcript)
    return response

# ❌ Wrong - blocking
def process_audio(self, audio: bytes) -> str:
    transcript = self.stt_service.transcribe(audio)  # Blocks!
    response = self.llm_service.generate(transcript)  # Blocks!
    return response
```

**All service methods must be async.**

---

### **5.6 Error Handling** 🛡️

Use custom exceptions from `src/core/exceptions.py`:

```python
class FreyaException(Exception):
    """Base exception for Freya"""
    pass

class AudioProcessingError(FreyaException):
    """Audio pipeline error"""
    pass

class LLMInferenceError(FreyaException):
    """LLM generation failed"""
    pass

class MemoryError(FreyaException):
    """Memory storage/retrieval failed"""
    pass
```

**Usage**:

```python
try:
    result = await self.process(data)
except AudioProcessingError as e:
    logger.error("audio_processing_failed", error=str(e))
    await self.bus.publish("error.audio", {"error": str(e)})
```

---

### **5.7 Type Hints** 📐 **MANDATORY**

All functions must have complete type hints:

```python
from typing import Optional, Dict, List
from datetime import datetime

async def process_message(
    self,
    message: AudioMessage,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Process an audio message.
    
    Args:
        message: Validated audio message
        timeout: Optional processing timeout in seconds
        
    Returns:
        Processing result dictionary
        
    Raises:
        AudioProcessingError: If processing fails
    """
    pass
```

---

### **5.8 Testing** 🧪 **MANDATORY**

All new code must include tests:

```
tests/
├── unit/               # Unit tests (fast, isolated)
│   └── test_my_service.py
└── integration/        # Integration tests (slower, multi-service)
    └── test_audio_pipeline.py
```

**Test Template**:

```python
import pytest
from src.services.my_service import MyService
from src.core.message_bus import MessageBus

@pytest.mark.asyncio
async def test_my_service_processes_message():
    """Test message processing"""
    bus = MessageBus()
    service = MyService(bus)
    
    # Setup
    await service.start()
    
    # Test
    result = await service.handle_message({"test": "data"})
    
    # Assert
    assert result is not None
    assert result["status"] == "success"
    
    # Cleanup
    await service.stop()
```

---

## **6. WHAT YOU CAN GENERATE CODE FOR**

### ✅ **Fully Supported** (Generate freely)

These systems are implemented and stable:

- Audio processing and routing logic
- LLM prompt engineering and response handling
- Memory storage and retrieval operations
- Message bus communication patterns
- Configuration management improvements
- Service improvements and refactoring
- Unit and integration tests
- Documentation and examples
- Logging and monitoring enhancements
- Error handling and validation

---

### ⚠️ **Needs Context** (Ask first)

These areas need clarification before generating:

- MCP tool integrations (Phase 3 architecture in planning)
- Service discovery mechanisms (future enhancement)
- Production deployment configs (not finalized)
- GUI frontend enhancements (basic UI exists, advanced features in planning)

---

### ❌ **Not Ready** (Don't generate)

Do not generate code for:

- Features that skip Phase 3 planning (MCP must come first)
- Direct Redis access (always use message bus abstraction)
- Hardcoded secrets or API keys
- Features contradicting the roadmap
- Blocking I/O or synchronous service code

---

## **7. CODE GENERATION RULES**

### ✔️ **ALWAYS**:
1. Generate async-compatible code
2. Use Pydantic for message schemas
3. Use structured logging (structlog)
4. Follow microservice directory structure
5. Communicate via message bus only
6. Include complete type hints
7. Add comprehensive docstrings
8. Include corresponding tests
9. Handle errors with custom exceptions
10. Validate all inputs with Pydantic

---

### ✖️ **NEVER**:
1. Hardcode secrets, tokens, or API keys
2. Bypass the message bus abstraction
3. Use blocking I/O or synchronous code
4. Create features contradicting Phase 3 planning
5. Use `print()` for logging
6. Pass raw dictionaries between services
7. Ignore type hints or validation
8. Skip writing tests
9. Access Redis directly

---

## **8. DEVELOPER PRIORITIES**

### 🔴 **Highest Priority** (Do First)
1. Add Pydantic schemas for all messages
2. Expand test coverage to 85%+ (LLMEngine, GUIService, MCPGateway)
3. Create SECURITY.md with best practices
4. Add API documentation (Swagger/OpenAPI)

---

### 🟡 **Medium Priority** (Do Soon)
1. Add sequence diagrams for key flows
2. Create installation and dev scripts
3. Improve error messages and logging
4. Add resource monitoring (Prometheus)
5. Implement service health checks
6. Create deployment guides

---

### 🟢 **Long-Term** (Future)
1. Service discovery (Consul/etcd)
2. Advanced message queue (Kafka/RabbitMQ)
3. Distributed tracing (OpenTelemetry)
4. Multi-user support
5. Kubernetes deployment manifests

---

## **9. CODE QUALITY CHECKLIST**

Before submitting code, verify:

```markdown
## Checklist
- [ ] Type hints on all functions and methods
- [ ] Pydantic models for all messages
- [ ] Structured logging (no print statements)
- [ ] Async/await used correctly
- [ ] Tests included (unit + integration where needed)
- [ ] Docstrings with Args/Returns/Raises
- [ ] No hardcoded secrets or credentials
- [ ] Follows service directory structure
- [ ] Uses message bus abstraction
- [ ] Error handling with custom exceptions
- [ ] Validates all inputs
- [ ] Follows naming conventions
```

---

## **10. EXAMPLE: ADDING A NEW SERVICE**

Here's a complete example of adding a new service that follows all Freya conventions:

### **Step 1: Create Service Structure**

```bash
mkdir -p src/services/translation
touch src/services/translation/__init__.py
touch src/services/translation/service.py
```

### **Step 2: Define Message Schemas**

```python
# src/services/translation/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime

class TranslationRequest(BaseModel):
    text: str = Field(..., max_length=10000)
    source_lang: str = Field(..., max_length=5)
    target_lang: str = Field(..., max_length=5)
    location: str
    timestamp: datetime

class TranslationResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
```

### **Step 3: Implement Service**

```python
# src/services/translation/service.py
from src.core.message_bus import MessageBus
from src.core.exceptions import FreyaException
from .schemas import TranslationRequest, TranslationResponse
import structlog
from datetime import datetime

logger = structlog.get_logger()

class TranslationError(FreyaException):
    """Translation service error"""
    pass

class TranslationService:
    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        self.running = False
    
    async def start(self):
        """Start translation service"""
        self.running = True
        await self.bus.subscribe("translation.request", self.handle_request)
        logger.info("service_started", service="TranslationService")
    
    async def stop(self):
        """Stop translation service"""
        self.running = False
        logger.info("service_stopped", service="TranslationService")
    
    async def handle_request(self, data: dict):
        """Handle translation request"""
        try:
            # Validate input
            request = TranslationRequest(**data)
            
            logger.info(
                "translation_requested",
                source=request.source_lang,
                target=request.target_lang,
                text_length=len(request.text)
            )
            
            # Perform translation
            result = await self.translate(request)
            
            # Publish response
            await self.bus.publish(
                "translation.response",
                result.dict()
            )
            
        except Exception as e:
            logger.error("translation_failed", error=str(e))
            raise TranslationError(f"Translation failed: {e}")
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """Perform actual translation"""
        # Implementation here
        return TranslationResponse(
            translated_text="...",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            confidence=0.95,
            timestamp=datetime.now()
        )
```

### **Step 4: Add Tests**

```python
# tests/unit/test_translation_service.py
import pytest
from src.services.translation.service import TranslationService
from src.services.translation.schemas import TranslationRequest
from src.core.message_bus import MessageBus
from datetime import datetime

@pytest.mark.asyncio
async def test_translation_service_handles_request():
    """Test translation request handling"""
    bus = MessageBus()
    service = TranslationService(bus)
    
    await service.start()
    
    request = TranslationRequest(
        text="Hello world",
        source_lang="en",
        target_lang="es",
        location="office",
        timestamp=datetime.now()
    )
    
    result = await service.translate(request)
    
    assert result.source_lang == "en"
    assert result.target_lang == "es"
    assert result.confidence > 0.0
    
    await service.stop()
```

### **Step 5: Register in Main**

```python
# src/main.py
from src.services.translation.service import TranslationService

async def main():
    # ... existing services
    translation_service = TranslationService(message_bus)
    await translation_service.start()
```

---

## **11. COMMON PATTERNS**

### **Pattern: Request-Response**

```python
# Requester
request_id = str(uuid.uuid4())
await bus.publish("service.request", {
    "request_id": request_id,
    "data": "..."
})

# Responder
async def handle_request(data: dict):
    request_id = data["request_id"]
    result = await process(data)
    await bus.publish("service.response", {
        "request_id": request_id,
        "result": result
    })
```

### **Pattern: Pipeline**

```python
# Stage 1: STT
await bus.publish("audio.input", audio_data)

# Stage 2: LLM (subscribed to "stt.output")
async def handle_transcript(data: dict):
    response = await llm.generate(data["text"])
    await bus.publish("llm.output", response)

# Stage 3: TTS (subscribed to "llm.output")
async def handle_response(data: dict):
    audio = await tts.synthesize(data["text"])
    await bus.publish("audio.output", audio)
```

### **Pattern: Broadcast**

```python
# Notify all interested services
await bus.publish("system.event", {
    "type": "user_arrived",
    "location": "front_door",
    "timestamp": datetime.now()
})
```

---

## **12. ANTI-PATTERNS TO AVOID**

### ❌ **Direct Service Coupling**

```python
# BAD - Direct dependency
from src.services.llm.service import LLMService

class MyService:
    def __init__(self):
        self.llm = LLMService()  # Tight coupling!
```

### ✅ **Use Message Bus**

```python
# GOOD - Loose coupling via messages
class MyService:
    async def process(self, data):
        await self.bus.publish("llm.request", data)
```

---

### ❌ **Blocking Calls**

```python
# BAD - Blocks event loop
import requests
response = requests.get("http://...")  # Blocking!
```

### ✅ **Async HTTP**

```python
# GOOD - Non-blocking
import aiohttp
async with aiohttp.ClientSession() as session:
    async with session.get("http://...") as response:
        data = await response.json()
```

---

### ❌ **Unvalidated Data**

```python
# BAD - Raw dict, no validation
async def handle_message(data: dict):
    text = data["text"]  # May not exist!
    process(text)
```

### ✅ **Pydantic Validation**

```python
# GOOD - Validated with Pydantic
async def handle_message(data: dict):
    msg = MyMessage(**data)  # Validates structure
    process(msg.text)
```

---

## **13. DEBUGGING TIPS**

### **View Message Flow**

```bash
# Watch all Redis messages
redis-cli PSUBSCRIBE '*'

# Watch specific channel
redis-cli SUBSCRIBE 'audio.input'
```

### **Test Service Isolation**

```python
# Mock message bus for testing
class MockMessageBus:
    def __init__(self):
        self.published = []
    
    async def publish(self, channel, data):
        self.published.append((channel, data))
    
    async def subscribe(self, channel, handler):
        pass
```

### **Structured Log Queries**

```bash
# Search logs by field
grep "sample_rate=16000" logs/freya.log

# Filter by service
grep "service=LLMEngine" logs/freya.log
```

---

## **14. DOCUMENTATION REQUIREMENTS**

### **Every Service Needs**:
1. Docstring explaining purpose
2. Message schemas it accepts/produces
3. Example usage
4. Error conditions

### **Example Service Documentation**:

```python
class TranslationService:
    """
    Handles text translation between languages.
    
    Subscribes to:
        - translation.request: TranslationRequest
    
    Publishes to:
        - translation.response: TranslationResponse
        - error.translation: ErrorMessage
    
    Example:
        >>> service = TranslationService(message_bus)
        >>> await service.start()
        >>> await bus.publish("translation.request", {
        ...     "text": "Hello",
        ...     "source_lang": "en",
        ...     "target_lang": "es"
        ... })
    
    Raises:
        TranslationError: If translation fails
    """
```

---

## **15. CONTRIBUTION WORKFLOW**

When contributing code:

1. **Read this prompt** thoroughly
2. **Check Phase status** - don't implement Phase 3+ features
3. **Add message schemas** if creating new messages
4. **Write tests** for all new code
5. **Follow conventions** outlined here
6. **Document** public APIs and services
7. **Update** CHANGELOG.md
8. **Submit PR** with clear description

---

## **END OF SYSTEM PROMPT**

**Version**: 1.0 (December 2024)  
**For**: Freya v2 - Phase 2 Complete, Phase 3 Planning  
**Maintainer**: @MrPink1977  
**Repository**: https://github.com/MrPink1977/freya_v2

---

## **Quick Reference Card**

```
✅ Phase 2 Complete:
   - Multi-room audio ✅
   - Audio pipeline ✅  
   - Memory system ✅
   - Message bus ✅

🚧 In Planning:
   - MCP integration
   - Tool ecosystem

📋 Future:
   - Vision pipeline
   - Advanced memory

🔴 Known Gaps:
   - Test coverage needs expansion
   - Message schemas need formalization

🔒 Always Required:
   - Pydantic schemas
   - Async code
   - Structured logging
   - Type hints
   - Tests
```

**Remember**: Phase 2 is COMPLETE and working well. Focus on quality improvements, not questioning what already works! 🚀
