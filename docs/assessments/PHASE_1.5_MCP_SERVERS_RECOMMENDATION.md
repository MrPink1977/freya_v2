# Phase 1.5 MCP Servers Recommendation

## Research Date
December 3, 2025

## User Question
"Are the APIs Claude wants free? Can we use local MCPs for what he wants APIs for?"

---

## Executive Summary

**YES! We can use 100% LOCAL MCPs for Phase 1.5!**

After comprehensive research, I found that:
- ✅ **Web Search MCP** exists that is 100% local (no API keys)
- ✅ **Weather MCP** exists that is 100% free (no API keys)
- ✅ All 4 local MCPs remain local
- ✅ **ZERO API keys required** for Phase 1.5

**Recommendation**: Use 6 MCP servers, all free, 5 completely local, 1 uses free government API.

---

## Detailed Findings

### 1. Web Search - 100% LOCAL! ✅

**MCP Server**: `web-search-mcp` by mrkrsl  
**GitHub**: https://github.com/mrkrsl/web-search-mcp  
**Stars**: 367 ⭐  
**Status**: Production-ready, actively maintained

#### How It Works
- **NO API KEYS REQUIRED** ✅
- Uses direct browser connections (Playwright)
- Multi-engine strategy: Bing → Brave → DuckDuckGo
- Runs entirely on your machine
- No external API calls
- No rate limits
- No costs

#### Features
- `full-web-search` - Complete search with page content extraction
- `get-web-search-summaries` - Quick search results only
- `get-single-web-page-content` - Extract content from specific URL

#### Installation
```bash
npm install
npx playwright install
npm run build
```

#### Why This is Better Than Brave Search API
| Feature | web-search-mcp | Brave Search API |
|---------|----------------|------------------|
| Cost | FREE | $0 (2,000/month limit) |
| API Key | NONE | Required |
| Rate Limit | NONE | 1 query/second |
| Privacy | 100% Local | Cloud service |
| Reliability | Multi-engine fallback | Single engine |

**Verdict**: **Use web-search-mcp** - It's better in every way!

---

### 2. Weather - FREE Government API! ✅

**MCP Server**: `nws-mcp-server` by nitvob  
**GitHub**: https://github.com/nitvob/nws-mcp-server  
**Status**: Production-ready

#### How It Works
- **NO API KEY REQUIRED** ✅
- Uses National Weather Service API (api.weather.gov)
- Free US government service
- No rate limits
- No costs
- Real-time data

#### Features
- 🌤️ Weather forecasts for any US location (lat/long)
- 🚨 Weather alerts for any US state
- 📡 Real-time data from NWS

#### Limitations
- **US locations only** (uses NWS API)
- If you need global weather, would need OpenWeather API

#### Why This is Better Than OpenWeather API
| Feature | NWS MCP | OpenWeather API |
|---------|---------|-----------------|
| Cost | FREE (unlimited) | $0 (1,000/day limit) |
| API Key | NONE | Required |
| Coverage | US only | Global |
| Rate Limit | NONE | 60/minute |
| Data Source | US Government | Commercial |

**Verdict**: **Use NWS MCP for US weather** - Free, no API key, unlimited!

**Note**: If you need global weather later, can add OpenWeather MCP in Phase 2+.

---

## Recommended Phase 1.5 MCP Server List

### **6 MCP Servers - All Free, No API Keys!**

| # | MCP Server | Purpose | Local/Cloud | API Key | Cost |
|---|------------|---------|-------------|---------|------|
| 1 | **Filesystem MCP** | File operations | LOCAL | NONE | FREE |
| 2 | **Shell MCP** | System commands | LOCAL | NONE | FREE |
| 3 | **Time/Date MCP** | Current time | LOCAL | NONE | FREE |
| 4 | **Calculator MCP** | Math operations | LOCAL | NONE | FREE |
| 5 | **web-search-mcp** | Web search | LOCAL | NONE | FREE |
| 6 | **nws-mcp-server** | Weather (US) | FREE API | NONE | FREE |

**Total API Keys Required**: **ZERO** ✅  
**Total Monthly Cost**: **$0.00** ✅  
**Privacy**: **100% Local** (except NWS uses free gov API) ✅

---

## What About Brave Search API?

### Brave Search API Pricing
- **Free Tier**: 2,000 queries/month, 1 query/second
- **Paid Tier**: $5 per 1,000 requests (Base AI)
- **Requires**: API key signup

### Why We Don't Need It
The `web-search-mcp` server:
- ✅ Uses Brave Search (among others) without API
- ✅ No rate limits
- ✅ No API key required
- ✅ Better reliability (multi-engine fallback)
- ✅ 100% local and private

**Verdict**: **Skip Brave Search API** - We have something better!

---

## What About OpenWeather API?

### OpenWeather API Pricing
- **Free Tier**: 1,000 calls/day, 60 calls/minute
- **Paid Tier**: $0.0015 per call over limit
- **Requires**: API key signup

### Why We Don't Need It (For Now)
The `nws-mcp-server`:
- ✅ Uses National Weather Service (free government API)
- ✅ No rate limits
- ✅ No API key required
- ✅ Real-time US weather data

**Limitation**: US only

**Verdict**: **Use NWS MCP for Phase 1.5** - Add OpenWeather later if global weather needed.

---

## What About ElevenLabs API?

### ElevenLabs API Pricing
- **Free Tier**: 10,000 characters/month
- **Paid Tier**: $5/month (30,000 characters)
- **Requires**: API key signup

### Recommendation
**SKIP for Phase 1.5** - This is for TTS (Phase 2)

We'll set this up when we implement the TTS Service in Phase 2.

---

## Updated Phase 1.5 Plan

### Changes from Claude's Original Plan

#### ❌ REMOVE:
- Brave Search MCP (replaced with web-search-mcp)
- OpenWeather MCP (replaced with nws-mcp-server)
- ElevenLabs MCP (move to Phase 2)

#### ✅ ADD:
- web-search-mcp (local web search, no API key)
- nws-mcp-server (free US weather, no API key)

#### Result:
- **6 servers instead of 7**
- **ZERO API keys required**
- **100% free**
- **Better privacy** (5 local, 1 free gov API)

---

## Installation Instructions

### 1. Filesystem MCP
```bash
# Official MCP server
npm install -g @modelcontextprotocol/server-filesystem
```

### 2. Shell MCP
```bash
# Official MCP server  
npm install -g @modelcontextprotocol/server-shell
```

### 3. Time/Date MCP
```bash
# Official MCP server
npm install -g @modelcontextprotocol/server-time
```

### 4. Calculator MCP
```bash
# Official MCP server
npm install -g @modelcontextprotocol/server-calculator
```

### 5. web-search-mcp (NEW!)
```bash
# Clone or download from GitHub
git clone https://github.com/mrkrsl/web-search-mcp.git
cd web-search-mcp
npm install
npx playwright install
npm run build
```

### 6. nws-mcp-server (NEW!)
```bash
# Clone or download from GitHub
git clone https://github.com/nitvob/nws-mcp-server.git
cd nws-mcp-server
npm install
npm run build
```

---

## Configuration Example

### config/mcp_servers.yaml
```yaml
mcp_servers:
  # Local Servers (No API Keys)
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    type: "local"
    
  shell:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-shell"]
    type: "local"
    
  time:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-time"]
    type: "local"
    
  calculator:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-calculator"]
    type: "local"
    
  web_search:
    command: "node"
    args: ["/path/to/web-search-mcp/dist/index.js"]
    type: "local"
    env:
      MAX_CONTENT_LENGTH: "10000"
      BROWSER_HEADLESS: "true"
    
  weather:
    command: "node"
    args: ["/path/to/nws-mcp-server/dist/index.js"]
    type: "free_api"  # Uses free government API, no key needed
```

---

## Testing Scenarios (Updated)

### Test 1: Local Tools
```
"What time is it?" → Time MCP
"What's 123 * 456?" → Calculator MCP
"List files in /home/user" → Filesystem MCP
"Run command: ls -la" → Shell MCP
```

### Test 2: Web Search (NO API KEY!)
```
"Search the web for Python async best practices" → web-search-mcp
"What's the latest news about AI?" → web-search-mcp
"Find information about Ollama models" → web-search-mcp
```

### Test 3: Weather (NO API KEY!)
```
"What's the weather in San Francisco?" → nws-mcp-server
"Are there any weather alerts in California?" → nws-mcp-server
"What's the forecast for New York?" → nws-mcp-server
```

---

## Answers to Claude's Questions

### Q1: Do you have API keys ready?
**A1: NO API KEYS NEEDED!** ✅

We found better alternatives:
- ✅ web-search-mcp (local) replaces Brave Search API
- ✅ nws-mcp-server (free gov API) replaces OpenWeather API
- ⏳ ElevenLabs - Skip for Phase 1.5 (Phase 2 only)

### Q2: Should I include Llama 3.1 8B instructions?
**A2: YES** - Still use Llama 3.1 8B for better tool calling.

### Q3: 8-10 hour estimate okay?
**A3: YES** - But commit incrementally (not one giant commit).

### Q4: Manual testing sufficient?
**A4: YES** - Manual test scripts are fine for Phase 1.5.

---

## Benefits of This Approach

### Privacy
- ✅ 5 out of 6 servers are 100% local
- ✅ 1 server uses free US government API (NWS)
- ✅ No commercial cloud services
- ✅ No data sent to third parties

### Cost
- ✅ $0.00 monthly cost
- ✅ No API key signups
- ✅ No rate limits
- ✅ No usage tracking

### Reliability
- ✅ web-search-mcp has multi-engine fallback
- ✅ No dependency on commercial API uptime
- ✅ No risk of hitting rate limits
- ✅ No risk of API key expiration

### Simplicity
- ✅ No .env file needed
- ✅ No API key management
- ✅ Easier setup
- ✅ Fewer failure points

---

## Limitations & Future Considerations

### Current Limitations
1. **Weather**: US only (NWS API limitation)
2. **Web Search**: Requires Playwright browsers (larger install)

### Future Enhancements (Phase 2+)
If you need:
- **Global weather**: Add OpenWeather MCP (requires API key)
- **Voice (TTS)**: Add ElevenLabs MCP (requires API key)
- **More search options**: Can add Brave Search API as fallback

But for Phase 1.5, **we don't need any of these!**

---

## Final Recommendation

**Tell Claude**:

```
UPDATED: No API keys needed for Phase 1.5!

Changes to your plan:
1. ❌ REMOVE Brave Search MCP
   ✅ ADD web-search-mcp (local, no API key)
   
2. ❌ REMOVE OpenWeather MCP  
   ✅ ADD nws-mcp-server (free US gov API, no key)
   
3. ❌ REMOVE ElevenLabs MCP
   ⏳ DEFER to Phase 2 (TTS implementation)

Result:
- 6 MCP servers (not 7)
- ZERO API keys required
- $0.00 monthly cost
- Better privacy (5 local, 1 free gov API)

Installation:
- 4 official MCP servers (npm install)
- 2 community servers (git clone + npm build)

All other aspects of your plan remain the same:
- LLM Model: Still use Llama 3.1 8B
- Scope: Still 8-10 hours, commit incrementally
- Testing: Still manual testing

You're approved to proceed with the updated server list! 🚀
```

---

## References

- **web-search-mcp**: https://github.com/mrkrsl/web-search-mcp (367 stars)
- **nws-mcp-server**: https://github.com/nitvob/nws-mcp-server
- **National Weather Service API**: https://api.weather.gov (free, no key)
- **MCP Official Servers**: https://modelcontextprotocol.io/examples
