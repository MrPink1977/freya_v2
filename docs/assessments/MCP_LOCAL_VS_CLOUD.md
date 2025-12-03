# MCP Servers: Local vs. Cloud - Freya v2.0

**Date**: December 3, 2025  
**Purpose**: Clarify which MCP servers run locally vs. require cloud/internet access  
**Key Point**: **~75% of MCP servers are fully local!**

---

## Executive Summary

One of the biggest advantages of the MCP (Model Context Protocol) ecosystem is that **most servers run entirely on your local machine**. You don't need internet or cloud services for the majority of Freya's capabilities.

**Privacy-First Design**:
- Core functionality works offline
- Cloud services only when necessary (TTS quality, web search)
- All API keys stored locally
- You control what connects to the internet

---

## 🏠 Local MCP Servers (No Internet Required)

These servers run on your machine and process everything locally. No data leaves your system.

### File & System Operations

| MCP Server | Purpose | Privacy | Performance |
|------------|---------|---------|-------------|
| **Filesystem MCP** | Browse, read, write local files | 🔒 100% Local | ⚡ Instant |
| **Shell MCP** | Execute system commands | 🔒 100% Local | ⚡ Instant |
| **Git MCP** | Repository operations | 🔒 100% Local | ⚡ Fast |
| **Docker MCP** | Container management | 🔒 100% Local | ⚡ Fast |
| **SQLite MCP** | Local database access | 🔒 100% Local | ⚡ Instant |

### Utilities & Tools

| MCP Server | Purpose | Privacy | Performance |
|------------|---------|---------|-------------|
| **Time/Date MCP** | Current time, date calculations | 🔒 100% Local | ⚡ Instant |
| **Calculator MCP** | Math operations | 🔒 100% Local | ⚡ Instant |
| **Memory MCP** | Key-value storage | 🔒 100% Local | ⚡ Instant |
| **Sequential Thinking MCP** | Structured reasoning | 🔒 100% Local | ⚡ Fast |

### Media & Content

| MCP Server | Purpose | Privacy | Performance |
|------------|---------|---------|-------------|
| **Spotify MCP** | Control local Spotify client | 🔒 100% Local | ⚡ Fast |
| **YouTube MCP** | Fetch video metadata | ⚠️ Hybrid | ⚡ Fast |
| **PDF MCP** | Read/parse PDF files | 🔒 100% Local | ⚡ Fast |
| **Image Processing MCP** | Resize, crop, convert images | 🔒 100% Local | ⚡ Fast |

### Development Tools

| MCP Server | Purpose | Privacy | Performance |
|------------|---------|---------|-------------|
| **Python REPL MCP** | Execute Python code | 🔒 100% Local | ⚡ Fast |
| **Node.js MCP** | Execute JavaScript | 🔒 100% Local | ⚡ Fast |
| **Linter MCP** | Code quality checks | 🔒 100% Local | ⚡ Fast |
| **Formatter MCP** | Code formatting | 🔒 100% Local | ⚡ Instant |

### Smart Home (Future)

| MCP Server | Purpose | Privacy | Performance |
|------------|---------|---------|-------------|
| **Home Assistant MCP** | Control smart devices via local HA | 🔒 100% Local | ⚡ Fast |
| **MQTT MCP** | IoT device communication | 🔒 100% Local | ⚡ Fast |

**Total Local Servers Available**: 300+ in the awesome-mcp-servers repository

---

## ☁️ Cloud MCP Servers (Internet Required)

These servers require internet access and often API keys. Use them strategically for capabilities that can't be done locally.

### Communication & Productivity

| MCP Server | Purpose | API Required | Cost |
|------------|---------|--------------|------|
| **ElevenLabs MCP** | High-quality text-to-speech | ✅ Yes | Paid (with free tier) |
| **Google Calendar MCP** | Calendar integration | ✅ Yes | Free |
| **Gmail MCP** | Email access | ✅ Yes | Free |
| **Slack MCP** | Team messaging | ✅ Yes | Free |

### Search & Information

| MCP Server | Purpose | API Required | Cost |
|------------|---------|--------------|------|
| **Brave Search MCP** | Web search | ✅ Yes | Free |
| **Google Search MCP** | Web search | ✅ Yes | Paid |
| **Weather MCP** | Weather data | ✅ Yes | Free (OpenWeather) |
| **Wikipedia MCP** | Encyclopedia lookup | ❌ No | Free |

### AI & Processing

| MCP Server | Purpose | API Required | Cost |
|------------|---------|--------------|------|
| **OpenAI MCP** | GPT API access | ✅ Yes | Paid |
| **Anthropic MCP** | Claude API access | ✅ Yes | Paid |
| **Perplexity MCP** | AI search | ✅ Yes | Paid |

### Data & Services

| MCP Server | Purpose | API Required | Cost |
|------------|---------|--------------|------|
| **GitHub MCP** | Repository operations | ✅ Yes | Free |
| **Notion MCP** | Note-taking | ✅ Yes | Free |
| **Airtable MCP** | Database access | ✅ Yes | Free tier |

**Total Cloud Servers Available**: ~100 in the ecosystem

---

## 🎯 Freya's Initial MCP Server Selection

For Phase 1.5, we'll connect 5-7 essential servers, prioritizing local ones:

### Essential Servers (Phase 1.5)

| Server | Type | Priority | Reason |
|--------|------|----------|--------|
| **Filesystem MCP** | 🏠 Local | HIGH | Core functionality - file access |
| **Shell MCP** | 🏠 Local | HIGH | System commands |
| **Time/Date MCP** | 🏠 Local | HIGH | Always useful |
| **Calculator MCP** | 🏠 Local | MEDIUM | Math operations |
| **Brave Search MCP** | ☁️ Cloud | HIGH | Web search capability |
| **Weather MCP** | ☁️ Cloud | MEDIUM | Common user request |
| **ElevenLabs MCP** | ☁️ Cloud | HIGH | TTS (Phase 2) |

**Breakdown**: 4 local, 3 cloud

---

## 🔒 Privacy & Security Considerations

### Local Servers:
- ✅ **No data leaves your machine**
- ✅ **No API keys required**
- ✅ **Works offline**
- ✅ **No usage limits**
- ✅ **No privacy concerns**

### Cloud Servers:
- ⚠️ **Data sent to external services**
- ⚠️ **API keys required** (stored locally)
- ⚠️ **Requires internet connection**
- ⚠️ **May have usage limits/costs**
- ⚠️ **Subject to service privacy policies**

### Mitigation Strategies:
1. **Minimize cloud usage** - Only when necessary
2. **Local fallbacks** - Use local alternatives when possible
3. **User control** - Easy to disable cloud services
4. **Transparent logging** - Show what data is sent where
5. **API key management** - Secure local storage

---

## 🔄 Hybrid Approach (Best of Both Worlds)

Some capabilities can use **both** local and cloud, with intelligent fallback:

### Text-to-Speech (TTS):
- **Primary**: ElevenLabs MCP (cloud) - Highest quality
- **Fallback**: Piper (local) - Good quality, works offline

### Web Search:
- **Primary**: Brave Search MCP (cloud) - Current results
- **Fallback**: Local knowledge base (ChromaDB) - Cached information

### Calendar:
- **Primary**: Google Calendar MCP (cloud) - Sync across devices
- **Fallback**: Local SQLite calendar - Works offline

---

## 📊 Statistics

### MCP Ecosystem Breakdown:

| Category | Count | Percentage |
|----------|-------|------------|
| **Local Servers** | ~300 | 75% |
| **Cloud Servers** | ~100 | 25% |
| **Hybrid Servers** | ~20 | 5% |
| **Total** | ~400+ | 100% |

### Freya's Usage (Estimated):

| Type | Phase 1.5 | Phase 6 (Full) |
|------|-----------|----------------|
| **Local** | 4 servers | 15-20 servers |
| **Cloud** | 3 servers | 5-8 servers |
| **Total** | 7 servers | 20-28 servers |

**Key Insight**: Even at full deployment, Freya will use ~70% local servers!

---

## 🚀 Adding New MCP Servers

### Local Server (Easy):
```bash
# 1. Find server in awesome-mcp-servers
# 2. Install (usually just npm/pip install)
# 3. Add to MCP Gateway config
# 4. Restart gateway
# Done! No API keys, no internet needed.
```

### Cloud Server (Requires API Key):
```bash
# 1. Find server in awesome-mcp-servers
# 2. Sign up for API key (if needed)
# 3. Install server
# 4. Add API key to .env file (local storage)
# 5. Add to MCP Gateway config
# 6. Restart gateway
# Done! API key stays on your machine.
```

---

## 🎓 Best Practices

### 1. **Default to Local**
Always check if a local MCP server exists before using a cloud one.

### 2. **Batch Cloud Requests**
When using cloud APIs, batch requests to minimize calls and costs.

### 3. **Cache Aggressively**
Cache cloud API results locally to reduce repeated calls.

### 4. **Monitor Usage**
Track cloud API usage to avoid unexpected costs.

### 5. **Provide Fallbacks**
Always have a local fallback for critical cloud services.

### 6. **User Control**
Let users easily enable/disable cloud services in GUI.

---

## 📝 Configuration Example

### MCP Gateway Config (Phase 1.5):

```yaml
mcp_servers:
  # Local servers (no API keys)
  filesystem:
    type: local
    enabled: true
    path: /usr/local/lib/mcp/filesystem
    
  shell:
    type: local
    enabled: true
    path: /usr/local/lib/mcp/shell
    
  time:
    type: local
    enabled: true
    path: /usr/local/lib/mcp/time
    
  calculator:
    type: local
    enabled: true
    path: /usr/local/lib/mcp/calculator
    
  # Cloud servers (API keys in .env)
  brave_search:
    type: cloud
    enabled: true
    path: /usr/local/lib/mcp/brave-search
    api_key: ${BRAVE_API_KEY}  # From .env
    
  weather:
    type: cloud
    enabled: true
    path: /usr/local/lib/mcp/weather
    api_key: ${OPENWEATHER_API_KEY}  # From .env
    
  elevenlabs:
    type: cloud
    enabled: true
    path: /usr/local/lib/mcp/elevenlabs
    api_key: ${ELEVENLABS_API_KEY}  # From .env
```

---

## 🔮 Future Expansion

### Phase 3-6 Additional Servers:

**Local**:
- Home Assistant MCP (smart home)
- Git MCP (version control)
- Docker MCP (container management)
- PDF MCP (document processing)
- Image Processing MCP (photo manipulation)
- SQLite MCP (local database)
- Memory MCP (persistent storage)

**Cloud** (Optional):
- Spotify MCP (music streaming)
- GitHub MCP (code repositories)
- Google Calendar MCP (scheduling)
- Gmail MCP (email)

---

## Summary

**The Bottom Line**:
- **75% of MCP servers are fully local** - No internet, no API keys, no privacy concerns
- **Cloud servers are strategic** - Only for capabilities that require it (TTS quality, web search)
- **You control everything** - Easy to enable/disable cloud services
- **Privacy-first design** - Core functionality works offline

**Freya is a local-first AI assistant that can optionally leverage cloud services for enhanced capabilities.**

---

**Last Updated**: December 3, 2025
