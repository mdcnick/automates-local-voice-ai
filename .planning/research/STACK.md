# Stack Research

**Domain:** Local/hybrid voice AI assistant (LiveKit + Python agent) — milestone additions
**Researched:** 2026-02-23
**Confidence:** MEDIUM-HIGH (most recommendations verified against official docs; voice cloning section is MEDIUM due to rapidly-evolving landscape)

---

## Existing Stack (Do Not Change)

| Technology | Version | Role |
|------------|---------|------|
| livekit-agents | ~1.3 (upgrade to ~1.4) | Python agent framework |
| livekit-plugins-openai | bundled with agents | STT/TTS/LLM OpenAI-compat adapters |
| livekit-plugins-silero | bundled | VAD |
| livekit-plugins-turn-detector | bundled | Multilingual turn detection |
| livekit-plugins-noise-cancellation | ~0.2 | Background noise suppression |
| Kokoro-FastAPI (remsky/Kokoro-FastAPI) | Docker | Local TTS server, OpenAI-compat endpoint |
| Nemotron STT | Docker | Local STT, OpenAI-compat endpoint |
| Next.js | existing | Browser frontend |
| Docker Compose | existing | Orchestration |

---

## Recommended Stack — New Capabilities

### LLM: OpenRouter

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| openai.LLM.with_openrouter() | livekit-agents ~1.4 | Route LLM calls to OpenRouter | Built into the existing livekit-plugins-openai. No new package needed. Uses `OPENROUTER_API_KEY` env var. Supports 300+ models, fallback_models list, and provider routing. |

**Integration pattern (verified against official LiveKit docs):**

```python
from livekit.plugins import openai as lk_openai

llm = lk_openai.LLM.with_openrouter(
    model="meta-llama/llama-3.3-70b-instruct:free",
    fallback_models=["meta-llama/llama-3.1-8b-instruct:free"],
)
```

**Also remove:** The `llama_cpp` Docker service and replace the `base_url` hack with the above. The agent's `openai.LLM(base_url=llama_base_url)` pattern works but `with_openrouter()` is the idiomatic path with proper header injection (X-Title, HTTP-Referer).

**Confidence:** HIGH — verified at https://docs.livekit.io/agents/models/llm/plugins/openrouter/

---

### Infrastructure: LiveKit Cloud

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| LiveKit Cloud | SaaS | Replace self-hosted livekit server container | Same API/SDK as self-hosted. Migration = change LIVEKIT_URL env var + API keys. Eliminates `livekit` Docker service. Cloud adds global TURN infrastructure, observability, and noise cancellation offloaded from local. |

**Migration steps:** Remove `livekit:` service from docker-compose. Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` to LiveKit Cloud values in `.env.local`. Frontend `NEXT_PUBLIC_LIVEKIT_URL` must point to wss://[your-project].livekit.cloud.

**Confidence:** HIGH — verified: code portability guaranteed per official LiveKit docs; no agent code changes required.

---

### Knowledge Retrieval: LightRAG

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| lightrag-hku | 1.4.9.11 (Jan 2026) | Graph-aware RAG with REST API | Combines knowledge graph + vector retrieval. Has built-in HTTP server (`lightrag-server`) on port 9621. OpenAI-compatible LLM backend. Active EMNLP 2025 paper. Runs standalone on Coolify. |
| httpx | >=0.27 | Async HTTP client for LightRAG queries | Needed for async `@function_tool` calls from the agent without blocking the voice pipeline. Already an httpx user via caldav[async]. |

**LightRAG HTTP API endpoints (verified):**
- `POST /documents/upload` — ingest a file
- `POST /documents/scan` — scan directory
- `POST /query` — RAG query (returns JSON)
- `POST /query/stream` — streaming query

**Install on Coolify:** Use Docker image `hkuds/lightrag` or `pip install "lightrag-hku[api]"` then `lightrag-server`. Requires an LLM backend (use OpenRouter's OpenAI-compat URL) and an embedding model.

**Agent integration pattern:**

```python
import httpx

@function_tool()
async def query_knowledge(self, context: RunContext, query: str) -> str:
    """Search long-term memory and personal knowledge base."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{LIGHTRAG_URL}/query",
            json={"query": query, "mode": "hybrid"},
            headers={"X-API-Key": LIGHTRAG_API_KEY},
            timeout=3.0,  # fail fast — voice is latency-sensitive
        )
        return resp.json().get("response", "No relevant information found.")
```

**Confidence:** MEDIUM — API shape verified via GitHub README; `lightrag-hku` PyPI confirmed active. Specific Coolify deployment steps need validation at deployment time.

---

### Calendar: CalDAV

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| caldav | 2.2.6 (Feb 2026) | CalDAV protocol client | Provider-agnostic: works with Google Calendar, iCloud, Nextcloud, Radicale, etc. without provider-specific SDKs. Stable, actively maintained. Latest release Feb 2026. |
| caldav[async] | 2.2.6 | Async HTTP for non-blocking calendar ops | Adds httpx dependency for async; critical so calendar I/O doesn't block the voice pipeline. |

**Install:**

```bash
pip install "caldav[async]"
```

**Usage pattern in agent function tool:**

```python
import caldav
import asyncio

@function_tool()
async def get_calendar_events(self, context: RunContext, date: str) -> str:
    """Get calendar events for a specific date (YYYY-MM-DD format)."""
    # caldav sync client in thread to avoid blocking
    def _fetch():
        client = caldav.DAVClient(
            url=os.getenv("CALDAV_URL"),
            username=os.getenv("CALDAV_USERNAME"),
            password=os.getenv("CALDAV_PASSWORD"),
        )
        principal = client.principal()
        calendars = principal.calendars()
        # ... query events

    return await asyncio.get_event_loop().run_in_executor(None, _fetch)
```

Note: `caldav.aio` module exists for async, but its maturity vs. run_in_executor approach should be validated at implementation time.

**Confidence:** HIGH — PyPI latest version confirmed, docs at https://caldav.readthedocs.io/

---

### TTS: Multi-Voice Support

The existing Kokoro-FastAPI server (remsky/Kokoro-FastAPI) already supports 26+ voices out of the box via voice parameter in the OpenAI-compat API. **No new library needed.** The agent passes `voice="af_nova"` to `openai.TTS()`; expose this as a configurable env var or session parameter.

**Available Kokoro voices (examples):** `af_nova`, `af_heart`, `af_bella`, `am_adam`, `bf_emma`, `bm_george`, etc.

**Multi-voice pattern:** Let users select at session start; store in session context; pass to TTS initialization or a voice-switching wrapper.

**Confidence:** HIGH — confirmed via Kokoro-FastAPI GitHub and LiveKit plugin (taresh18/livekit-kokoro).

---

### Voice Cloning

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| F5-TTS (SWivid/F5-TTS) | latest (pip install f5-tts) | Zero-shot voice cloning from audio sample | Only viable local option for true voice cloning. Kokoro explicitly cannot clone voices from audio — it only blends pre-trained style vectors. F5-TTS uses flow matching for zero-shot cloning from ~5s reference audio. Requires Python 3.10+, PyTorch, CUDA recommended. |

**Critical tradeoff:** F5-TTS has higher latency than Kokoro (~300-800ms TTFB vs Kokoro's ~80ms). This is likely too slow for real-time voice conversation. Voice cloning is better suited as an offline voice creation step: user uploads reference audio, system generates a voice file, that file is used for subsequent TTS calls.

**Alternative approach (recommended):** Use Kokoro voice blending to create custom-feeling voices without the cloning latency hit. True F5-TTS cloning works better as an async "voice creation" feature, not inline TTS.

**No LiveKit plugin exists for F5-TTS.** Would need a custom TTS plugin wrapping F5-TTS's Python API or HTTP server, or a FastAPI wrapper similar to Kokoro-FastAPI.

**Confidence:** MEDIUM — F5-TTS capabilities verified via official GitHub and DigitalOcean comparison article. Latency figures are hardware-dependent and should be measured locally.

---

## Agent Version Upgrade

The pyproject.toml pins `livekit-agents[silero,turn-detector,openai]~=1.3`. Upgrade to `~=1.4` is required because:

- `livekit-agents@1.4.0` dropped Python 3.9 support (requires 3.9+ still, but adds 3.14 support)
- Adds `LLMStream.collect()` API useful for tool result handling
- Fixes memory leaks in process pool (1.4.2)
- Latest stable: **1.4.3** (Feb 23, 2026 — same day as this research)

```toml
dependencies = [
    "livekit-agents[silero,turn-detector,openai]~=1.4",
    "livekit-plugins-noise-cancellation~=0.2",
    "python-dotenv",
    "caldav[async]>=2.2.6",
    "httpx>=0.27",
]
```

**Confidence:** HIGH — release dates verified against GitHub releases page.

---

## Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27 | Async HTTP for LightRAG + any future HTTP tools | Always (async agent context) |
| python-multipart | >=0.0.9 | Form/file upload handling in frontend API | When adding document upload endpoint to Next.js |
| pydantic | >=2.0 | Data validation for tool inputs/outputs | Already likely present via livekit-agents |

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| openai.LLM.with_openrouter() | Direct OpenAI client or LiteLLM | with_openrouter() is already in the installed plugin, idiomatic, handles headers correctly |
| caldav 2.2.6 | Google Calendar API (google-api-python-client) | Provider-specific; fails for iCloud/Nextcloud users |
| caldav 2.2.6 | aiocaldav | Fork of caldav; less maintained, caldav[async] covers the async use case |
| F5-TTS (async workflow) | Coqui TTS, RVC | F5-TTS is the SOTA open-source zero-shot cloner; Coqui is archived; RVC is speaker conversion not synthesis |
| LightRAG HTTP API | LightRAG Python client inline | Decoupled: LightRAG runs on Coolify, agent is stateless; HTTP access enforces that boundary |
| LiveKit Cloud | Continue self-hosting LiveKit | More infra to maintain; Cloud adds global TURN, noise cancellation, and observability for free at dev tier |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| llama_cpp Docker service | Being replaced by OpenRouter; adds ~4GB+ image, GPU requirements, startup time | openai.LLM.with_openrouter() |
| Kokoro for voice cloning | Kokoro cannot clone from audio samples — only blends pre-existing style tensors | F5-TTS for true cloning, or Kokoro voice blending for lighter customization |
| Google Calendar API SDK | Provider-locked; breaks for iCloud/Nextcloud users | caldav library (RFC 4791 compliant) |
| Synchronous calendar/RAG calls inside function tools | Blocks the agent event loop, adds perceived latency to voice responses | asyncio.run_in_executor() or async caldav/httpx |
| LiteLLM as an OpenRouter proxy | Unnecessary indirection since livekit-agents already has with_openrouter() | openai.LLM.with_openrouter() |

---

## Stack Patterns by Variant

**If voice cloning is high priority and latency is acceptable (async pre-generation):**
- Use F5-TTS as an offline voice creation step
- Store generated voice file
- Use generated voice file as reference in subsequent TTS calls
- Do NOT call F5-TTS inline during conversation

**If voice cloning latency is unacceptable for real-time:**
- Use Kokoro voice blending (`voice="0.5*af_nova+0.5*af_heart"` style blending)
- Expose voice selection UI with named presets
- Skip F5-TTS in this milestone

**If LightRAG query latency causes voice pipeline delays:**
- Use LightRAG's streaming endpoint and only surface results if returned within 2s
- Pre-query on session start for likely-relevant context
- Set httpx timeout aggressively (2-3s) and degrade gracefully

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| livekit-agents ~1.4 | Python 3.10+ | Drops 3.9 in 1.4.0; existing Dockerfile must use Python 3.10+ base |
| caldav 2.2.6 | Python 3.8+ | caldav[async] requires httpx |
| lightrag-hku 1.4.9.11 | Python 3.10+ | API server requires uvicorn |
| f5-tts | Python 3.10+ | Requires PyTorch; CUDA recommended for acceptable TTS speed |

---

## Installation

```bash
# Agent pyproject.toml dependencies
# Update livekit-agents pin and add new deps:
uv add "livekit-agents[silero,turn-detector,openai]~=1.4"
uv add "caldav[async]>=2.2.6"
uv add "httpx>=0.27"

# LightRAG on Coolify (separate service):
pip install "lightrag-hku[api]"
# Start with: lightrag-server --port 9621

# F5-TTS (only if voice cloning milestone):
pip install f5-tts
```

---

## Sources

- https://docs.livekit.io/agents/models/llm/plugins/openrouter/ — OpenRouter integration (HIGH confidence)
- https://github.com/livekit/agents/releases — livekit-agents version history (HIGH confidence)
- https://pypi.org/project/caldav/ — caldav 2.2.6 release date and features (HIGH confidence)
- https://pypi.org/project/lightrag-hku/ — lightrag-hku 1.4.9.11 version (HIGH confidence)
- https://github.com/HKUDS/LightRAG/blob/main/lightrag/api/README.md — LightRAG REST API endpoints (MEDIUM confidence — partial content fetched)
- https://github.com/taresh18/livekit-kokoro — Kokoro LiveKit plugin (MEDIUM confidence)
- https://github.com/remsky/Kokoro-FastAPI — Kokoro multi-voice support (MEDIUM confidence)
- https://github.com/SWivid/F5-TTS — F5-TTS voice cloning (MEDIUM confidence)
- https://www.digitalocean.com/community/tutorials/best-text-to-speech-models — TTS comparison F5 vs Kokoro (MEDIUM confidence)
- https://docs.livekit.io/intro/cloud/ — LiveKit Cloud portability (HIGH confidence)

---

*Stack research for: local-voice-ai milestone — OpenRouter, LiveKit Cloud, LightRAG, CalDAV, multi-voice TTS, voice cloning*
*Researched: 2026-02-23*
