# Architecture Research

**Domain:** LiveKit-based voice AI assistant with external LLM, RAG, and calendar integration
**Researched:** 2026-02-23
**Confidence:** HIGH (existing codebase analyzed directly; LiveKit, OpenRouter, LightRAG official docs verified)

## Standard Architecture

### System Overview — Current State

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js)                            │
│  ┌────────────────────┐   ┌──────────────────────────────────────┐   │
│  │  /api/connection-  │   │  React UI (LiveKit client SDK)       │   │
│  │  details route.ts  │   │  WebRTC audio in/out                 │   │
│  └─────────┬──────────┘   └───────────────┬──────────────────────┘   │
└────────────│──────────────────────────────│──────────────────────────┘
             │ JWT token                    │ WebRTC
             ▼                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                  LiveKit Server (self-hosted Docker)                │
│  - WebRTC signaling and media relay                                │
│  - Agent dispatch                                                   │
└────────────────────────────┬───────────────────────────────────────┘
                             │ WebRTC + agent protocol
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                   livekit_agent (Python, Docker)                    │
│  Assistant(Agent) + AgentSession                                    │
│  Pipeline: Silero VAD → Nemotron STT → llama.cpp LLM → Kokoro TTS │
└──────┬──────────────────────────────────────────┬──────────────────┘
       │ HTTP POST /v1/audio/transcriptions        │ HTTP POST /v1/audio/speech
       ▼                                           ▼
 ┌─────────────┐   HTTP POST /v1/chat/completions  ┌─────────────┐
 │ Nemotron    │◄─────────────────────────────────►│  Kokoro TTS │
 │ STT (Docker)│                                   │   (Docker)  │
 └─────────────┘   ┌─────────────────┐             └─────────────┘
                   │ llama.cpp Docker│
                   │ (local LLM)     │
                   └─────────────────┘
```

### System Overview — Target State

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js)                            │
│  ┌────────────────────┐   ┌──────────────────────────────────────┐   │
│  │  /api/connection-  │   │  React UI (LiveKit client SDK)       │   │
│  │  details route.ts  │   │  WebRTC audio in/out                 │   │
│  │  (unchanged)       │   │  + Document upload UI (new)          │   │
│  └─────────┬──────────┘   └───────────────┬──────────────────────┘   │
└────────────│──────────────────────────────│──────────────────────────┘
             │ JWT token                    │ WebRTC
             ▼                              ▼
┌────────────────────────────────────────────────────────────────────┐
│              LiveKit Cloud (replaces self-hosted Docker)            │
│  - Same API surface, same SDKs, only LIVEKIT_URL changes           │
│  - Managed WebRTC signaling, media relay, agent dispatch           │
└────────────────────────────┬───────────────────────────────────────┘
                             │ WebRTC + agent protocol
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                   livekit_agent (Python, Docker)                    │
│  Assistant(Agent) + AgentSession                                    │
│  Pipeline: Silero VAD → Nemotron STT → OpenRouter LLM → Kokoro TTS│
│                                                                     │
│  @function_tool() decorated methods:                                │
│    query_knowledge(query) → HTTP GET LightRAG /query               │
│    save_knowledge(text)   → HTTP POST LightRAG /documents          │
│    get_calendar_events()  → CalDAV async client                    │
│    create_event(...)      → CalDAV async client                    │
└──────┬──────────────┬──────────────┬──────────────────────────────┘
       │              │              │
       ▼              ▼              ▼
 ┌──────────┐  ┌───────────┐  ┌──────────────────────────────────┐
 │ Nemotron │  │ Kokoro TTS│  │  External Services               │
 │ STT      │  │ (Docker,  │  │  ┌─────────────┐ ┌────────────┐  │
 │ (Docker, │  │ unchanged)│  │  │  OpenRouter  │ │ LightRAG   │  │
 │unchanged)│  └───────────┘  │  │  (cloud LLM) │ │ (Coolify)  │  │
 └──────────┘                 │  │  POST /chat/ │ │ POST /query│  │
                              │  │  completions │ │ GET /docs  │  │
                              │  └─────────────┘ └────────────┘  │
                              │  ┌──────────────────────────────┐ │
                              │  │ CalDAV Server (user-provided)│ │
                              │  │ Google/iCloud/Nextcloud etc. │ │
                              │  └──────────────────────────────┘ │
                              └──────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| Next.js Frontend | Browser UI, WebRTC session init, document upload | LiveKit Cloud, livekit_agent (via LiveKit), `/api/connection-details` |
| `/api/connection-details` route | JWT token generation, room naming | LiveKit Cloud (token validation) |
| LiveKit Cloud | WebRTC signaling, media relay, agent dispatch | Frontend (browser), livekit_agent |
| livekit_agent (Python) | Conversation orchestration, tool dispatch, session state | LiveKit Cloud, Nemotron, Kokoro, OpenRouter, LightRAG, CalDAV |
| Nemotron STT (Docker) | Speech-to-text transcription | livekit_agent (HTTP) |
| Kokoro TTS (Docker) | Text-to-speech synthesis | livekit_agent (HTTP) |
| Silero VAD | Voice activity detection (in-process) | livekit_agent (Python library) |
| OpenRouter | LLM inference (replaces llama.cpp) | livekit_agent (HTTPS) |
| LightRAG (Coolify) | Knowledge graph retrieval and ingestion | livekit_agent (HTTP), document upload endpoint |
| CalDAV Server | Calendar read/write | livekit_agent (HTTPS via caldav lib) |

## Recommended Project Structure

No major restructuring needed. Key changes are additive:

```
livekit_agent/src/
├── agent.py              # Main agent — update LLM config, add tool imports
├── tools/                # New directory (create)
│   ├── __init__.py
│   ├── rag.py            # LightRAG query/ingest tools
│   ├── calendar.py       # CalDAV read/write tools
│   └── memory.py         # Voice-commanded knowledge save tool
├── clients/              # New directory (create)
│   ├── __init__.py
│   ├── lightrag.py       # HTTP client for LightRAG API
│   └── caldav_client.py  # Async CalDAV wrapper
└── config.py             # Env var loading (currently inline in agent.py)
```

### Structure Rationale

- **tools/**: Separates `@function_tool()` decorated methods from agent class. Keeps `agent.py` readable as scope grows.
- **clients/**: HTTP/protocol clients decoupled from tool logic. LightRAG client and CalDAV wrapper can be tested independently.
- **config.py**: Centralizes env var validation as the number of env vars grows significantly with this milestone.

## Architectural Patterns

### Pattern 1: OpenRouter as Drop-in LLM Replacement

**What:** OpenRouter exposes an OpenAI-compatible API at `https://openrouter.ai/api/v1`. The existing `openai.LLM()` plugin in the agent accepts any `base_url`, so swapping is a config change, not a code change.

**When to use:** Any time you want to change LLM provider without rewriting agent logic.

**Trade-offs:** Requires internet access from agent container; rate-limited on free tier (20 req/min, 200/day). Adds ~50-150ms network latency vs local inference.

**Example:**
```python
# Before (llama.cpp local)
llm=openai.LLM(
    base_url="http://llama_cpp:11434/v1",
    model="qwen3-4b",
    api_key="no-key-needed"
)

# After (OpenRouter)
llm=openai.LLM(
    base_url="https://openrouter.ai/api/v1",
    model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
```

**Confidence:** HIGH — OpenRouter confirmed OpenAI-compatible at `https://openrouter.ai/api/v1` via official docs.

### Pattern 2: LiveKit Cloud Migration (Config-Only Change)

**What:** Swap self-hosted LiveKit Docker service for LiveKit Cloud by changing three environment variables. Agent code, frontend code, and SDK usage are identical — LiveKit Cloud runs the same open-source server binary.

**When to use:** Eliminating infra maintenance overhead. Automatically done when removing `livekit` Docker service from compose.

**Trade-offs:** Ongoing cost (LiveKit Cloud pricing). Loss of full offline operation capability.

**Changes required:**
```bash
# docker-compose.yml — remove livekit service block entirely
# .env changes:
LIVEKIT_URL=wss://your-project.livekit.cloud  # was ws://livekit:7880
LIVEKIT_API_KEY=<cloud key>
LIVEKIT_API_SECRET=<cloud secret>

# frontend docker-compose environment:
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud  # was ws://localhost:7880
```

**Confidence:** HIGH — LiveKit official docs confirm "client and agent code remains portable" and only the endpoint URL changes.

### Pattern 3: LightRAG as Async HTTP Tool

**What:** LightRAG exposes a FastAPI REST server on port 9621. The agent calls it via HTTP inside `@function_tool()` async methods. Authentication via `X-API-Key` header.

**When to use:** All knowledge retrieval and ingestion from agent tools.

**Key endpoints:**
- `POST /query` — RAG query with `mode` parameter (`hybrid` recommended for best recall)
- `POST /documents/upload` — Ingest new documents
- `GET /health` — Health check

**Trade-offs:** Network hop adds latency (mitigated by async; LightRAG on Coolify should be low-latency if same datacenter region). LightRAG on Coolify is a separate service to manage/monitor.

**Example:**
```python
# clients/lightrag.py
import httpx

class LightRAGClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    async def query(self, query: str, mode: str = "hybrid") -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/query",
                json={"query": query, "mode": mode},
                headers=self.headers,
                timeout=8.0,
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def insert(self, text: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/documents/text",
                json={"text": text},
                headers=self.headers,
                timeout=30.0,
            )
```

**Confidence:** MEDIUM — LightRAG API server endpoints confirmed via GitHub README and DeepWiki; exact request/response schema for `/query` needs validation against running instance.

### Pattern 4: CalDAV via Async Python Client

**What:** The `caldav` library (python-caldav) provides an async client via `caldav[async]` using httpx. Wrap it in thin tool functions decorated with `@function_tool()`.

**When to use:** All calendar read (list events) and write (create reminders) operations from agent tools.

**Trade-offs:** CalDAV is the lowest-common-denominator protocol — works with Google, iCloud, Nextcloud without provider-specific code. However, CalDAV server URLs differ per provider and must be documented for self-hosters. Async support is available but requires `pip install caldav[async]`.

**Example:**
```python
# tools/calendar.py
import caldav
from livekit.agents import function_tool, RunContext, ToolError

@function_tool()
async def get_upcoming_events(self, context: RunContext, days: int = 7) -> str:
    """Retrieve calendar events for the next N days.

    Args:
        days: Number of days ahead to look. Default is 7.
    """
    try:
        async with caldav.aio.get_async_davclient(
            url=os.getenv("CALDAV_URL"),
            username=os.getenv("CALDAV_USERNAME"),
            password=os.getenv("CALDAV_PASSWORD"),
        ) as client:
            principal = await client.principal()
            calendars = await principal.calendars()
            # fetch events from first calendar
            events = await calendars[0].date_search(...)
            return format_events(events)
    except Exception as e:
        raise ToolError(f"Calendar unavailable: {e}")
```

**Confidence:** MEDIUM — caldav async support confirmed via official caldav docs. CalDAV protocol compatibility with Google/iCloud/Nextcloud is well-established. Exact async API methods need verification against current caldav 1.x docs.

### Pattern 5: Voice-Commanded Knowledge Saving

**What:** Agent detects phrases like "Remember this..." or "Save a note about..." via LLM intent, calls a `@function_tool()` that POSTs the content to LightRAG `/documents/text`. No separate NLP layer required — the LLM decides when to invoke the tool based on the tool's description.

**When to use:** When user explicitly asks agent to save information.

**Trade-offs:** Relies on LLM correctly interpreting save intent. With a good system prompt and clear tool description, this is reliable. Avoid triggering on every user statement — tool description must be precise.

**Example:**
```python
@function_tool()
async def save_knowledge(
    self,
    context: RunContext,
    content: str,
    topic: str,
) -> str:
    """Save important information the user wants remembered for future conversations.
    Only call this when the user explicitly asks to save, remember, or note something.

    Args:
        content: The information to save verbatim.
        topic: A short label for what this information is about.
    """
    await self.rag_client.insert(f"[{topic}] {content}")
    return f"Got it, I've saved that note about {topic}."
```

**Confidence:** HIGH — this is the standard LiveKit `@function_tool()` pattern, confirmed via official LiveKit docs.

## Data Flow

### Voice Interaction with RAG Augmentation

```
User speaks
    ↓
WebRTC audio → LiveKit Cloud → livekit_agent
    ↓
Silero VAD (in-process) — detects speech end
    ↓
Nemotron STT (HTTP POST /v1/audio/transcriptions) → transcript text
    ↓
LLM (OpenRouter HTTPS POST /chat/completions)
    ↓ (if LLM decides context is needed)
    ├── tool call: query_knowledge → LightRAG HTTP POST /query → knowledge text
    ├── tool call: get_calendar_events → CalDAV HTTPS → event list
    └── tool call: save_knowledge → LightRAG HTTP POST /documents/text
    ↓
LLM final response text
    ↓
Kokoro TTS (HTTP POST /v1/audio/speech) → audio bytes
    ↓
WebRTC audio → LiveKit Cloud → Browser → user hears response
```

### Document Upload Flow (New)

```
User selects file in browser UI
    ↓
Next.js API route (new: /api/upload-document)
    ↓
HTTP POST to LightRAG /documents/upload (with X-API-Key header)
    ↓
LightRAG ingests, parses, builds knowledge graph
    ↓
Response: success/failure status shown in UI
```

**Design note:** Document upload goes directly from frontend API route to LightRAG, bypassing the agent. This avoids routing large files through WebRTC and the voice pipeline. The agent only queries LightRAG; ingest happens via HTTP from the server-side Next.js route.

### Session Memory Flow

```
Session starts → AgentSession holds conversation context in memory
    ↓
User speaks → turns accumulate in session context window
    ↓
Session ends → context discarded (stateless agent)
Cross-session recall → LightRAG (explicit save by user or agent)
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 users | Current architecture works; OpenRouter free tier may hit rate limits with concurrent users |
| 10-100 users | Upgrade to OpenRouter paid tier; LightRAG may need dedicated CPU/RAM on Coolify |
| 100+ users | LiveKit Cloud handles WebRTC scaling automatically; agent needs horizontal scaling (multiple Docker containers or K8s); LightRAG needs its own VM |

### Scaling Priorities

1. **First bottleneck:** OpenRouter rate limits (20 req/min free tier). Fix: upgrade to paid tier (~$0.10-0.30/M tokens for Llama 3.3 70B).
2. **Second bottleneck:** Single agent container handling all sessions sequentially. Fix: LiveKit supports spawning multiple agent workers; run multiple agent containers behind a shared queue.

## Anti-Patterns

### Anti-Pattern 1: Synchronous HTTP Calls Inside Tool Functions

**What people do:** Use `requests.get()` or blocking I/O inside `@function_tool()` methods.
**Why it's wrong:** The agent event loop is async; blocking calls stall the entire session. STT/TTS pipeline backs up, user hears silence.
**Do this instead:** Use `httpx.AsyncClient`, `aiohttp`, or `await caldav.aio.*` for all network calls inside tools. Every tool must be `async def`.

### Anti-Pattern 2: Querying LightRAG on Every Turn

**What people do:** Call `query_knowledge()` before every LLM response to "enrich context."
**Why it's wrong:** LightRAG queries add 100-500ms latency per turn. Voice AI is extremely latency-sensitive; users notice delays above ~300ms.
**Do this instead:** Let the LLM decide when to invoke RAG tools based on conversation context. Write the tool description to be specific: "query knowledge base when the user asks about something that may be in their saved notes or documents." Trust the LLM's judgment.

### Anti-Pattern 3: Hardcoding LiveKit Server URL in Frontend

**What people do:** Set `NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880` in production builds.
**Why it's wrong:** Browser-facing WebSocket URL must match the actual server. Self-hosters who change the URL get a broken UI.
**Do this instead:** Pass `LIVEKIT_URL` as a build-time env var. The existing pattern in `docker-compose.yml` already does this — maintain it when switching to LiveKit Cloud (`wss://` prefix required for cloud).

### Anti-Pattern 4: Putting CalDAV Credentials in Agent System Prompt

**What people do:** Include calendar credentials or personal data in the agent's system instructions for "personalization."
**Why it's wrong:** System prompt contents are often logged and may appear in LLM provider training data or monitoring tools. Credentials in prompts are a security risk.
**Do this instead:** Load credentials from environment variables in the Python client layer. Never pass credentials through the LLM.

### Anti-Pattern 5: Removing llama.cpp Before OpenRouter is Verified Working

**What people do:** Delete the local LLM Docker service first, then discover environment/network issues with OpenRouter.
**Why it's wrong:** Leaves the system non-functional during debugging. Hard to isolate whether issues are in the agent code or the new provider.
**Do this instead:** Add OpenRouter config alongside llama.cpp first. Switch with an env var (`LLM_PROVIDER=openrouter`). Verify in production. Then remove llama.cpp service.

## Integration Points

### External Services

| Service | Integration Pattern | Auth | Latency Expectation | Notes |
|---------|---------------------|------|---------------------|-------|
| OpenRouter | OpenAI-compatible HTTPS POST to `https://openrouter.ai/api/v1` | Bearer token (`OPENROUTER_API_KEY`) | 300-800ms (network + inference) | Drop-in for current llama.cpp; supports streaming |
| LiveKit Cloud | Change `LIVEKIT_URL` + credentials; same SDK | API key + secret (JWT) | Managed; edge nodes | `wss://` required (not `ws://`) |
| LightRAG (Coolify) | HTTP REST to `http[s]://your-lightrag.coolify.domain` | `X-API-Key` header | 100-500ms per query | Port 9621 default; expose via Coolify reverse proxy |
| CalDAV Server | caldav Python library async client (httpx under the hood) | Username + password or app-specific password | 50-300ms | URL format varies: Google=`https://www.googleapis.com/caldav/v3/...`, iCloud=`https://caldav.icloud.com/` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| livekit_agent ↔ Nemotron STT | HTTP POST `/v1/audio/transcriptions` (OpenAI-compatible) | Unchanged from current arch |
| livekit_agent ↔ Kokoro TTS | HTTP POST `/v1/audio/speech` (OpenAI-compatible) | Unchanged; voice selection becomes configurable |
| livekit_agent ↔ OpenRouter | HTTPS POST (outbound from Docker container) | Agent container needs internet access; add `OPENROUTER_API_KEY` to compose env |
| livekit_agent ↔ LightRAG | HTTP to Coolify hostname (cross-host network) | LightRAG URL must be reachable from agent container; verify firewall/network routing |
| livekit_agent ↔ CalDAV | HTTPS (outbound) | Provider URL + credentials via env vars |
| Next.js ↔ LightRAG | HTTP POST for document upload API route | Server-side only; API key stored server-side, not exposed to browser |

## Build Order Implications

Dependencies between new components determine the implementation sequence:

1. **LiveKit Cloud migration first** — Everything else depends on a stable LiveKit connection. This is config-only (env vars), lowest risk. Unblocks testing of all subsequent changes in the real environment.

2. **OpenRouter LLM swap second** — Config-only change in agent.py (change `base_url`, `model`, `api_key`). Remove llama.cpp Docker service after verification. Unblocks testing agent tools with a powerful model (70B can reliably invoke function tools; smaller local models sometimes miss).

3. **LightRAG client + query tool third** — Requires LightRAG to be deployed on Coolify (separate infrastructure task). Implement `clients/lightrag.py` and the `query_knowledge` tool. Test independently before adding more tools.

4. **Knowledge save tool fourth** — Depends on LightRAG client (step 3). Adds `save_knowledge` tool and document upload API route to Next.js.

5. **CalDAV tools fifth** — Independent of RAG but adds complexity. Implement `clients/caldav_client.py` and calendar tools. Test with one provider (Nextcloud) before documenting multi-provider support.

6. **Voice cloning / TTS voice selection sixth** — Depends on evaluating Kokoro's existing voice options vs. adding Coqui XTTS. Lowest dependency on other steps; can be done in parallel with step 5.

## Sources

- LiveKit Agents architecture: https://docs.livekit.io/agents/ (MEDIUM confidence — fetched 2026-02-23)
- LiveKit function tools: https://docs.livekit.io/agents/build/tools/ (HIGH confidence — fetched 2026-02-23)
- LiveKit Cloud migration: https://docs.livekit.io/intro/cloud/ (HIGH confidence — fetched 2026-02-23)
- OpenRouter API compatibility: https://openrouter.ai/docs/api/reference/authentication (HIGH confidence — multiple sources confirm OpenAI-compatible at `https://openrouter.ai/api/v1`)
- LightRAG API server: https://github.com/HKUDS/LightRAG/blob/main/lightrag/api/README.md (MEDIUM confidence — endpoints confirmed, exact schema needs validation)
- caldav async library: https://caldav.readthedocs.io/latest/about.html (MEDIUM confidence — async support via `caldav[async]` confirmed)
- Coqui XTTS v2 voice cloning: https://huggingface.co/coqui/XTTS-v2 (MEDIUM confidence — 10-second reference audio for cloning confirmed)
- Existing codebase: `livekit_agent/src/agent.py`, `docker-compose.yml` (HIGH confidence — direct analysis)

---
*Architecture research for: Local Voice AI Assistant — milestone integration*
*Researched: 2026-02-23*
