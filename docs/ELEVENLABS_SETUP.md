# ElevenLabs Setup Guide

Guide for configuring ElevenLabs TTS with Freya v2.0.

## Prerequisites

- ElevenLabs account ([https://elevenlabs.io](https://elevenlabs.io))
- Active API key
- MCP Gateway configured

## Quick Setup

### 1. Get Your API Key

1. Go to [ElevenLabs](https://elevenlabs.io)
2. Sign up or log in
3. Navigate to your [Profile Settings](https://elevenlabs.io/app/settings)
4. Copy your API key from the "API Key" section

### 2. Configure Environment Variable

Add to your `.env` file:

```bash
ELEVENLABS_API_KEY=your_api_key_here
```

### 3. Choose a Voice

Browse available voices at [ElevenLabs Voice Library](https://elevenlabs.io/voice-library).

Configure in `.env`:

```bash
# Default voice (Rachel)
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Or use a different voice
# ELEVENLABS_VOICE_ID=your_voice_id_here
```

### 4. Configure Voice Settings (Optional)

Fine-tune voice characteristics in `.env`:

```bash
# Voice stability (0.0-1.0): Higher = more consistent, Lower = more expressive
ELEVENLABS_STABILITY=0.5

# Similarity boost (0.0-1.0): How closely to match the voice
ELEVENLABS_SIMILARITY_BOOST=0.75

# Model selection
ELEVENLABS_MODEL=eleven_monolingual_v1
```

## Configuration Options

### Voice Settings

| Parameter | Range | Description | Default |
|-----------|-------|-------------|---------|
| `ELEVENLABS_STABILITY` | 0.0 - 1.0 | Voice consistency vs expressiveness | 0.5 |
| `ELEVENLABS_SIMILARITY_BOOST` | 0.0 - 1.0 | Voice matching accuracy | 0.75 |

**Recommendations:**
- **Stability 0.3-0.5**: More expressive, varied intonation
- **Stability 0.6-0.8**: Balanced, natural speech
- **Stability 0.8-1.0**: Very consistent, monotone

### Available Models

1. **eleven_monolingual_v1** (Default)
   - Best for English
   - High quality, low latency
   
2. **eleven_multilingual_v1**
   - Supports 28+ languages
   - Slightly higher latency

3. **eleven_multilingual_v2**
   - Latest multilingual model
   - Best quality for non-English

Configure in `.env`:
```bash
ELEVENLABS_MODEL=eleven_multilingual_v2
```

## Testing Your Setup

### 1. Test TTS Service

```bash
# Run Freya with debug logging
export LOG_LEVEL=DEBUG
python -m src.main
```

### 2. Send Test Message

Use the GUI or send a direct TTS request:

```python
# Via message bus
await message_bus.publish(\"tts.generate\", {
    \"text\": \"Hello, this is a test of the text to speech system.\",
    \"location\": \"test\"
})
```

### 3. Verify Audio Output

Check logs for:
```
[tts_service] 🎙️  Generating speech for LLM response (XX characters)...
[tts_service] ✓ Speech generated and published (XXXXX bytes)
```

## Troubleshooting

### No Audio Output

**Check 1: API Key**
```bash
# Verify API key is set
echo $ELEVENLABS_API_KEY

# Check logs for authentication errors
docker-compose logs freya-core | grep elevenlabs
```

**Check 2: Audio Pipeline**
```bash
# Verify Audio Manager is running
docker-compose ps
```

**Check 3: MCP Gateway**
```bash
# Ensure MCP Gateway is configured for ElevenLabs
cat config/mcp_servers.yaml | grep elevenlabs
```

### Poor Audio Quality

1. **Increase Stability**
   ```bash
   ELEVENLABS_STABILITY=0.7
   ```

2. **Try Different Voice**
   - Browse [Voice Library](https://elevenlabs.io/voice-library)
   - Update `ELEVENLABS_VOICE_ID`

3. **Switch Model**
   ```bash
   ELEVENLABS_MODEL=eleven_multilingual_v2
   ```

### API Rate Limits

ElevenLabs has usage limits based on your plan:

- **Free Tier**: 10,000 characters/month
- **Starter**: 30,000 characters/month
- **Creator**: 100,000 characters/month
- **Pro**: 500,000 characters/month

**Monitor Usage:**
1. Check [ElevenLabs Dashboard](https://elevenlabs.io/app/usage)
2. Review TTS Service metrics in Freya GUI

**Reduce Usage:**
- Shorten LLM responses
- Cache common responses
- Use local TTS for development

### Connection Errors

```
Error: Connection to ElevenLabs timed out
```

**Solutions:**
1. Check internet connection
2. Verify API key is valid
3. Check ElevenLabs status: [https://status.elevenlabs.io](https://status.elevenlabs.io)
4. Increase timeout in config:
   ```bash
   MCP_TOOL_TIMEOUT=120
   ```

## Advanced Configuration

### Custom Voice Cloning

If you have a Pro/Enterprise plan with voice cloning:

1. Clone your voice in ElevenLabs dashboard
2. Copy the voice ID
3. Update configuration:
   ```bash
   ELEVENLABS_VOICE_ID=your_cloned_voice_id
   ```

### Multiple Voices

Configure different voices for different contexts:

```python
# In your code
await message_bus.publish(\"tts.generate\", {
    \"text\": \"Hello!\",
    \"voice_id\": \"alternate_voice_id\"  # Override default
})
```

### Webhook Integration (Enterprise)

For real-time status updates:

```yaml
# config/mcp_servers.yaml
elevenlabs:
  webhook_url: https://your-domain.com/webhook
  webhook_secret: your_webhook_secret
```

## Cost Optimization

### Tips to Reduce Costs

1. **Use Shorter Responses**
   ```python
   # Configure LLM for concise responses
   PERSONALITY_VERBOSITY=concise
   ```

2. **Cache Common Phrases**
   - Pre-generate audio for common responses
   - Store in local cache

3. **Development Mode**
   ```bash
   # Use mock TTS during development
   export ELEVENLABS_API_KEY=""
   ```

4. **Monitor Usage**
   - Track character count in TTS Service metrics
   - Set up alerts for usage thresholds

## Security Best Practices

### API Key Management

**DO:**
- ✅ Store API key in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate keys regularly
- ✅ Use environment variables in production

**DON'T:**
- ❌ Commit API keys to Git
- ❌ Share keys in chat/email
- ❌ Use same key across multiple environments
- ❌ Log API keys

### Production Deployment

```bash
# Use secrets management
export ELEVENLABS_API_KEY=$(vault read -field=api_key secret/freya/elevenlabs)

# Or Kubernetes secrets
kubectl create secret generic freya-secrets \\
  --from-literal=elevenlabs-api-key=your_key_here
```

## Support

- **ElevenLabs Documentation**: [https://elevenlabs.io/docs](https://elevenlabs.io/docs)
- **API Reference**: [https://elevenlabs.io/docs/api-reference](https://elevenlabs.io/docs/api-reference)
- **Support**: [support@elevenlabs.io](mailto:support@elevenlabs.io)
- **Freya Issues**: [GitHub Issues](https://github.com/MrPink1977/freya_v2/issues)

## Next Steps

1. ✅ Configure ElevenLabs API key
2. ✅ Test TTS functionality
3. 📊 Monitor usage and metrics
4. 🎨 Customize voice settings
5. 🚀 Deploy to production

---

*Last Updated: December 4, 2025*
