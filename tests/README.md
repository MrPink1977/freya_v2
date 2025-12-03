# Freya v2.0 Tests

This directory contains tests for the Freya v2.0 project.

## Manual Tests

### STT Service Test

Test the Speech-to-Text service by publishing audio to the message bus.

**Prerequisites**:
- Redis running (via Docker Compose)
- Freya services running (including STT Service)

**Usage**:

```bash
# Test with generated tone (basic connectivity test)
python tests/test_stt_manual.py

# Test with your own WAV file
python tests/test_stt_manual.py path/to/your/audio.wav
```

**What it does**:
1. Loads or generates audio data
2. Connects to the message bus
3. Subscribes to `stt.transcription` channel
4. Publishes audio to `audio.stream` channel
5. Waits for and displays the transcription

**Example Output**:
```
======================================================================
📝 TRANSCRIPTION RECEIVED:
======================================================================
Text: "Hello, this is a test of the speech to text service"
Language: en
Confidence: 95.23%
Duration: 1.23s
Timestamp: 2025-12-03T10:30:45.123456
======================================================================
```

## Unit Tests

Unit tests will be added in future phases.

**Planned tests**:
- `test_message_bus.py` - Message bus functionality
- `test_stt_service.py` - STT service unit tests
- `test_llm_engine.py` - LLM engine unit tests
- `test_config.py` - Configuration validation

**To run unit tests** (when implemented):
```bash
pytest
pytest --cov=src --cov-report=html
```

## Test Fixtures

The `fixtures/` directory contains sample data for testing:

- Sample audio files (WAV format)
- Test conversation transcripts
- Mock responses

## Creating Good Test Audio

For best STT testing results:

**Audio Requirements**:
- Format: WAV
- Sample Rate: 16000 Hz (16kHz)
- Channels: 1 (mono)
- Bit Depth: 16-bit
- Duration: 1-30 seconds
- Clear speech, minimal background noise

**Creating test audio on Linux/Mac**:
```bash
# Record 5 seconds of audio
arecord -d 5 -f S16_LE -r 16000 -c 1 tests/fixtures/test_audio.wav

# Convert existing audio to correct format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 tests/fixtures/test_audio.wav
```

**Creating test audio on Windows**:
- Use Audacity or similar tool
- Set project rate to 16000 Hz
- Record in mono
- Export as WAV (16-bit PCM)

## Troubleshooting

**Issue**: "Connection refused" error
**Solution**: Ensure Redis is running via `docker-compose up -d redis`

**Issue**: "Model not found" error
**Solution**: The Whisper model will auto-download on first run. Ensure internet connectivity.

**Issue**: No transcription received
**Solution**:
- Check that Freya services are running
- Check that STT Service initialized successfully
- Verify audio format is correct (WAV, 16kHz, mono)
- Check logs: `docker-compose logs -f freya-core`

**Issue**: Poor transcription quality
**Solution**:
- Ensure audio is clear with minimal background noise
- Try a larger model in config: `stt_model=small` or `stt_model=medium`
- Adjust beam_size for better quality (slower): `stt_beam_size=10`
