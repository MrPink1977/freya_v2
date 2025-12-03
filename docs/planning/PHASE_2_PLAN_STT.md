# Development Plan: STT Service Implementation

**Phase**: 2 - Multi-room Audio
**Component**: Speech-to-Text Service
**Date**: 2025-12-03
**Estimated Time**: 3-4 hours
**Status**: 📋 Planned - Awaiting Approval

---

## A. OBJECTIVE

Implement the Speech-to-Text (STT) Service using faster-whisper for local, GPU-accelerated transcription. This service will subscribe to audio streams on the message bus and publish transcriptions for the LLM Engine to process.

**Success Criteria**:
- ✅ STT Service can receive audio data from message bus
- ✅ GPU-accelerated transcription with faster-whisper
- ✅ Proper error handling and logging following established patterns
- ✅ Health checks and metrics implemented
- ✅ Production-grade code quality (type hints, docstrings, error handling)
- ✅ Configuration parameters added to config.py
- ✅ Service integrated into main orchestrator

## B. PREREQUISITES

**Already in Place**:
- ✅ Phase 1 foundation complete
- ✅ MessageBus operational
- ✅ BaseService pattern established
- ✅ Docker environment ready
- ✅ GPU available (NVIDIA RTX 5060 Ti)

**Required**:
- faster-whisper Python package
- CUDA/GPU drivers (assumed already installed)
- Whisper model files (will auto-download on first run)

## C. IMPLEMENTATION STEPS

1. **Add faster-whisper dependency** (5 min)
   - Update pyproject.toml with faster-whisper package

2. **Add STT configuration parameters** (10 min)
   - Update src/core/config.py with STT-specific settings
   - Model name, language, device, compute type, etc.

3. **Create STTService class** (45 min)
   - Create src/services/stt/stt_service.py
   - Inherit from BaseService
   - Implement initialize(), start(), stop(), health_check()
   - Load faster-whisper model with GPU support

4. **Implement transcription logic** (40 min)
   - Subscribe to audio.stream channel
   - Process incoming audio data
   - Handle audio format conversion if needed
   - Publish transcriptions to stt.transcription channel
   - Comprehensive error handling

5. **Add custom exceptions and logging** (15 min)
   - Create STTServiceError exception
   - Add detailed logging with emoji indicators
   - Log model loading, transcription timing, errors

6. **Add metrics and health checks** (20 min)
   - Track transcription count, duration, confidence scores
   - Implement health check to verify model loaded
   - Publish metrics to message bus

7. **Integrate with orchestrator** (15 min)
   - Update src/main.py to include STT Service
   - Add to service initialization and lifecycle

8. **Create test infrastructure** (30 min)
   - Create sample audio file for testing
   - Test script to publish audio to message bus
   - Verify transcription output

9. **Update documentation** (20 min)
   - Update DEVELOPMENT_LOG.md with changes
   - Update README.md service status
   - Add inline code documentation

**Total Estimated Time**: 3 hours 20 minutes

## D. FILES TO CREATE/MODIFY

### Create:
- `src/services/stt/stt_service.py` (main service implementation, ~400 lines)
- `tests/test_stt_service.py` (unit tests, future)
- `tests/fixtures/sample_audio.wav` (test audio file)

### Modify:
- `pyproject.toml` (add faster-whisper dependency)
- `src/core/config.py` (add STT configuration section)
- `src/services/stt/__init__.py` (export STTService)
- `src/main.py` (add STT service to orchestrator)
- `DEVELOPMENT_LOG.md` (add implementation entry)
- `README.md` (update service status)

## E. TESTING PLAN

### Manual Testing Steps:
1. **Model Loading Test**:
   ```bash
   docker-compose up -d
   # Check logs for successful model loading
   docker-compose logs -f freya-core | grep STT
   ```

2. **Transcription Test**:
   - Create simple test script to publish audio to message bus
   - Verify transcription appears on stt.transcription channel
   - Check timing metrics in logs

3. **Error Handling Test**:
   - Test with invalid audio data
   - Test with empty audio
   - Verify graceful error handling

4. **Health Check Test**:
   - Verify health_check() returns True when model loaded
   - Test health check after error conditions

### Unit Tests (Future):
- Test model initialization
- Test audio processing
- Test error conditions
- Test metrics tracking

## F. DOCUMENTATION UPDATES

1. **DEVELOPMENT_LOG.md**:
   - Add entry with date, changes, rationale, impact
   - Update service status table
   - Update metrics

2. **README.md**:
   - Update service status (STT Service: ✅)
   - Update phase progress if applicable

3. **Code Documentation**:
   - Complete module docstring with author/version/date
   - Class docstring with usage examples
   - Method docstrings with Args/Returns/Raises/Example
   - Inline comments for complex logic

## G. INTEGRATION POINTS

### Message Bus Channels:
- **Subscribes to**: `audio.stream` (raw audio data from Audio Manager/test script)
  - Expected format: `{"audio_data": bytes, "format": str, "sample_rate": int, "timestamp": str}`

- **Publishes to**: `stt.transcription` (transcribed text)
  - Format: `{"text": str, "confidence": float, "language": str, "duration": float, "timestamp": str}`

- **Status**: `service.stt.status` (service status updates)
- **Metrics**: `service.stt.metrics` (performance metrics)

### Configuration Parameters:
```python
# STT Configuration (to add to config.py)
stt_model: str = "base"  # tiny, base, small, medium, large
stt_language: str = "en"
stt_device: str = "cuda"  # cuda or cpu
stt_compute_type: str = "float16"  # float16, int8
stt_beam_size: int = 5
stt_vad_filter: bool = True  # Voice activity detection
```

### Dependencies:
- MessageBus (for communication)
- Config (for settings)
- BaseService (for service structure)
- faster-whisper package
- CUDA runtime

## H. POTENTIAL ISSUES

### Issue 1: GPU Memory
**Risk**: Large Whisper models may consume significant GPU memory
**Mitigation**:
- Use "base" model by default (only 74M parameters)
- Make model size configurable
- Add memory usage logging
- Document GPU requirements

### Issue 2: Audio Format Compatibility
**Risk**: faster-whisper expects specific audio formats
**Mitigation**:
- Validate audio format before processing
- Add format conversion if needed (using pydub or similar)
- Clear error messages for unsupported formats
- Document expected formats

### Issue 3: Transcription Latency
**Risk**: Real-time transcription may be too slow
**Mitigation**:
- Use faster-whisper (optimized for speed)
- Enable VAD filtering to skip silence
- Monitor and log transcription duration
- Adjust beam_size for speed vs accuracy tradeoff

### Issue 4: Model Download on First Run
**Risk**: First run requires downloading model files
**Mitigation**:
- Log download progress clearly
- Add retry logic for downloads
- Document expected first-run behavior
- Consider pre-downloading in Docker image (future optimization)

### Issue 5: Audio Data Encoding
**Risk**: Audio bytes may need specific encoding/decoding
**Mitigation**:
- Accept common formats (WAV, raw PCM)
- Add clear documentation of expected format
- Validate audio data before processing
- Provide helpful error messages

## I. ROLLBACK PLAN

### How to Revert:
```bash
git revert <commit-hash>
```

### Safety Checks Before Committing:
1. ✅ All type hints in place
2. ✅ All docstrings complete
3. ✅ Error handling comprehensive
4. ✅ Logging detailed
5. ✅ Service starts without errors
6. ✅ Health check passes
7. ✅ Test transcription works
8. ✅ No breaking changes to existing services

### Service Independence:
- STT Service is optional - system continues to work without it
- LLM Engine doesn't depend on STT (yet)
- Can be disabled in main.py without affecting other services

### Rollback Checklist:
- [ ] Check MessageBus connectivity before commit
- [ ] Verify model loads successfully
- [ ] Test with sample audio
- [ ] Review all error paths
- [ ] Confirm no memory leaks

---

## Rationale

The STT Service is the logical first component for Phase 2 because:

1. **Self-contained**: Can be developed and tested independently using the message bus
2. **Follows established patterns**: Uses BaseService architecture from Phase 1
3. **Manageable scope**: ~3.5 hours of focused development
4. **High value**: Essential building block for voice interaction
5. **Testable**: Can verify functionality with sample audio files without full pipeline
6. **Non-breaking**: Doesn't affect existing Phase 1 services
7. **Foundation for next steps**: Required before Audio Manager and full conversation loop

---

## Next Steps After STT

Once STT is complete, the logical next chunks are:

1. **TTS Service** (Text-to-Speech with ElevenLabs)
   - Similar complexity and structure to STT
   - Can be tested independently via message bus
   - Completes the audio I/O pipeline

2. **Audio Manager** (Single-room first)
   - Routes audio streams to/from endpoints
   - Integrates STT and TTS services
   - Enables basic conversation loop

3. **Multi-room Support** (Location awareness)
   - Extend Audio Manager for multiple endpoints
   - Add wake word detection
   - Implement session management

---

**Status**: Ready for implementation approval
