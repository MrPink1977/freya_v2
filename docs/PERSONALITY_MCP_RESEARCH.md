# Personality MCP Server Research

## Research Date
December 3, 2025

## Question
Is there an existing MCP server for personality management that could replace building a custom Personality Manager service?

## Answer
**YES!** There are at least 2 production-ready MCP servers for personality management:

---

## Option 1: Clueo MCP (OpenClueo)

**GitHub**: https://github.com/ClueoFoundation/ClueoMCP  
**Stars**: 65  
**Status**: Active, production-ready

### What It Does
- **Scientific Approach**: Uses Big Five personality model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- **Numerical Precision**: Each trait scored 1-10
- **8 Presets**: Professional, Creative, Empathetic, Analytical, Enthusiastic, Casual Friend, Luxury Brand, Startup Brand
- **Custom Personalities**: Define your own Big Five scores
- **Cross-Platform**: Works with Claude, Cursor, Windsurf, VS Code, any MCP client

### Key Features
- `inject_personality` - Apply custom Big Five traits to text
- `inject_preset_personality` - Use predefined personalities
- `simulate_response` - Generate responses with specific personality
- **Memory System**: Learns your personality preferences over time
- **Enterprise Features**: Brand personality management, compliance tracking

### How It Works
```json
{
  "text": "Hello, how can I help you today?",
  "personality": {
    "openness": 7,
    "conscientiousness": 8,
    "extraversion": 6,
    "agreeableness": 9,
    "neuroticism": 3
  }
}
```

### Pros
- ✅ Scientific, proven psychological model
- ✅ Numerical precision (reproducible)
- ✅ 8 ready-made presets
- ✅ Memory system (learns preferences)
- ✅ Enterprise-grade
- ✅ Active development

### Cons
- ❌ Requires API key (cloud service)
- ❌ Not fully local (calls backend.clueoai.com)
- ❌ May have usage limits/costs

### Freya Fit
**EXCELLENT** - The "Casual Friend" preset (7,5,7,8,3) is close to Freya's personality. Could customize to:
- Openness: 8 (witty, creative)
- Conscientiousness: 9 (excellent at her job)
- Extraversion: 7 (engaging, playful)
- Agreeableness: 8 (helpful, but can be sarcastic)
- Neuroticism: 2 (stable, confident)

---

## Option 2: Persona MCP Server

**GitHub**: https://github.com/mickdarling/persona-mcp-server  
**LobeHub**: https://lobehub.com/mcp/mickdarling-persona-mcp-server  
**Status**: Active, production-ready

### What It Does
- **Markdown-Based**: Define personas in simple .md files
- **YAML Frontmatter**: Metadata (name, description, triggers, version, author)
- **Hot Reload**: Change personas without restarting
- **Flexible**: Activate by name or filename
- **Local**: No API keys, runs entirely on your machine

### Persona File Format
```markdown
---
name: "Freya"
description: "Witty, sarcastic, excellent AI assistant"
triggers: ["casual", "playful", "sarcastic"]
version: "1.0"
author: "MrPink1977"
---

# Freya Personality

You are Freya, a witty, funny, and playfully sarcastic AI assistant.

## Response Style
- Be engaging and humorous when appropriate
- Know when to be serious vs. playful
- Excellent at your job - provide accurate, helpful responses
- Maintain your unique charm

## Key Traits
- Witty and clever with words
- Playfully sarcastic (not mean)
- Adaptable to context (serious when needed)
- Confident and knowledgeable
```

### Key Features
- `activate_persona` - Load a persona by name
- `list_personas` - See all available personas
- `reload_personas` - Hot reload without restart
- **Multiple Personas**: Switch between different personalities
- **Easy to Edit**: Just markdown files

### Pros
- ✅ 100% LOCAL (no API keys, no cloud)
- ✅ Simple markdown format
- ✅ Easy to customize
- ✅ Hot reload (no restart needed)
- ✅ Free and open source
- ✅ Privacy-friendly

### Cons
- ❌ Less scientific than Big Five model
- ❌ No numerical precision
- ❌ No memory/learning system
- ❌ More manual (you write the personality description)

### Freya Fit
**EXCELLENT** - Perfect for Freya! You can write exactly the personality you want in plain English. No need to translate to numerical scores.

---

## Recommendation

### For Freya v2.0: Use **Persona MCP Server**

**Why?**
1. **100% Local** - Aligns with your local-first philosophy
2. **Simple** - Just write Freya's personality in a markdown file
3. **Flexible** - Easy to adjust and refine the personality
4. **No Costs** - Free, no API keys, no usage limits
5. **Privacy** - Everything stays on your machine
6. **Easy Integration** - Standard MCP server, works with your MCP Gateway

### Implementation Plan
1. Install Persona MCP server
2. Create `personas/freya.md` with Freya's personality
3. MCP Gateway connects to Persona MCP
4. LLM Engine calls `activate_persona "freya"` at startup
5. Persona context is injected into every conversation

### Alternative: Clueo MCP (If You Want Science)
If you prefer the Big Five psychological model and don't mind a cloud service, Clueo is more sophisticated. But for Freya's needs, Persona MCP is simpler and more aligned with your local-first approach.

---

## Conclusion

**YES, there ARE personality MCPs!** And they're production-ready.

**Persona MCP Server is the best fit for Freya** because:
- Local and private
- Simple and flexible
- Free and open source
- Easy to customize

**This completely eliminates the need for a custom Personality Manager service.**

---

## Next Steps
1. Update PRE_IMPLEMENTATION_AUDIT.md with this finding
2. Add Persona MCP to the Phase 1.5 MCP server list
3. Create `personas/freya.md` file
4. Update architecture diagram (no Personality Manager, just Persona MCP)
