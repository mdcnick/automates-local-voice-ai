# Project Research Summary

**Project:** Local Voice AI Assistant — milestone additions
**Domain:** Self-hosted real-time voice AI with RAG memory, calendar integration, and multi-voice TTS
**Researched:** 2026-02-23
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project extends an existing LiveKit-based voice AI assistant (Silero VAD + Nemotron STT + Kokoro TTS) by adding four major capabilities: cloud LLM routing via OpenRouter, persistent knowledge memory via LightRAG, calendar integration via CalDAV, and expanded TTS voice options. The existing architecture is well-structured and the new capabilities are largely additive — no core components need to be replaced, only extended. The recommended approach is to migrate LLM routing first (config-only, lowest risk), then layer in LightRAG, calendar tools, and voice selection sequentially, deferring voice cloning to a separate future phase.

The central technical challenge is latency. Real-time voice conversations tolerate approximately 800ms total pipeline latency; tool-based RAG lookups alone add 1.5-2.5 seconds when wired as LLM function calls. The correct pattern — confirmed by LiveKit official docs and peer-reviewed research — is to use the `on_user_turn_completed` hook to pre-fetch RAG context before LLM generation begins, reserving `@function_tool()` only for write operations (saving knowledge, creating events). Every external I/O path (LightRAG, CalDAV, OpenRouter) must be async with strict timeouts and verbal fallbacks.

The highest-risk integrations are Google CalDAV (requires OAuth 2.0 as of March 2025, not Basic Auth) and LightRAG at scale (query latency degrades severely without DB tuning). Voice cloning via Kokoro is architecturally impossible — it requires a different TTS engine (F5-TTS or Coqui XTTS) and should not be coupled with multi-voice selection work. The project's core privacy advantage (local STT/TTS, cloud-only LLM) is preserved and is a genuine differentiator worth maintaining throughout.

## Key Findings

### Recommended Stack

The existing stack requires minimal changes. The local llama.cpp LLM service should be replaced with `openai.LLM.with_openrouter()` — this is already built into the installed `livekit-plugins-openai` package, requires no new dependencies, and is a config change. LightRAG (lightrag-hku 1.4.9.11) provides graph-aware hybrid RAG via a REST server deployable on Coolify. The `caldav` library (v2.2.6, Feb 2026) handles CalDAV protocol with provider-agnostic support. The existing Kokoro-FastAPI server already supports 26+ voices — no new TTS library is needed for multi-voice selection. Upgrade `livekit-agents` from ~1.3 to ~1.4.3 for memory leak fixes and improved tool handling.

**Core technologies:**
- `openai.LLM.with_openrouter()` (livekit-agents ~1.4): Cloud LLM routing — already in installed plugin, replaces llama.cpp with zero code changes
- `lightrag-hku` 1.4.9.11: Graph-aware RAG server — hybrid knowledge graph + vector retrieval, runs as separate Docker/Coolify service
- `caldav[async]` 2.2.6: Provider-agnostic calendar client — works with Google, iCloud, Nextcloud via CalDAV RFC
- `httpx` >=0.27: Async HTTP for LightRAG calls — required for non-blocking tool execution
- Kokoro-FastAPI (existing): Multi-voice TTS — no changes needed, voice param already supported
- LiveKit Cloud: Managed WebRTC infrastructure — same SDK/API, only LIVEKIT_URL env var changes

### Expected Features

**Must have (table stakes):**
- LLM function tool wiring (OpenRouter) — foundation for all tool-use; without it the assistant can only chat
- Cross-session memory recall via LightRAG — #1 complaint with AI assistants is forgetting; this is the core value add
- Document upload for knowledge ingestion — users need to seed the knowledge base via UI, not just voice
- Voice-commanded knowledge saving — natural voice-first capture pattern, uses LLM intent + LightRAG insert
- Calendar read via CalDAV — "what's on my schedule?" is the most common assistant use case
- Sub-second response latency — any pipeline over 2-3s feels broken; RAG pattern must not add perceived delay

**Should have (competitive):**
- Calendar event creation by voice — closes the loop from "remind me" to actual calendar entry; few self-hostable assistants do this
- Multiple TTS voice options (Kokoro built-ins) — quality-of-life; low-effort since Kokoro already supports it
- LiveKit Cloud migration — reduces maintenance overhead; same API, only env var changes

**Defer (v2+):**
- Voice cloning — requires replacing or augmenting Kokoro with F5-TTS; separate engine, separate phase, consent requirements
- Multi-user profiles — architectural change; rate limits and auth complexity make this premature
- Web search — scope creep; users should index curated sources into LightRAG instead

### Architecture Approach

The architecture is a fan-out from a central Python agent: the agent orchestrates STT, LLM, and TTS sequentially, and dispatches async HTTP calls to LightRAG and CalDAV during the LLM tool phase. LiveKit Cloud replaces the self-hosted LiveKit Docker service (URL change only). Document upload bypasses the agent entirely — Next.js API route posts directly to LightRAG, keeping the voice pipeline free of file I/O. The agent codebase needs a `tools/` directory for `@function_tool()` methods and a `clients/` directory for HTTP client wrappers (LightRAGClient, CalDAVClient), with a `config.py` for centralized env var loading.

**Major components:**
1. `livekit_agent` (Python, Docker) — conversation orchestration, tool dispatch, session state; all new capabilities live here
2. LightRAG (Coolify) — knowledge graph + vector retrieval server; agent calls via HTTP; frontend uploads directly to it
3. CalDAV server (user-provided: Google/iCloud/Nextcloud) — calendar read/write via python-caldav async client
4. OpenRouter (cloud) — LLM inference replacing local llama.cpp; OpenAI-compatible API
5. LiveKit Cloud — managed WebRTC signaling and media relay; replaces self-hosted LiveKit Docker service
6. Nemotron STT + Kokoro TTS (Docker, unchanged) — local audio processing; privacy advantage preserved

### Critical Pitfalls

1. **RAG as tool call adds 1.5-2.5s latency** — Use `on_user_turn_completed` hook to inject retrieved context before LLM generates, not as a function tool call. Research shows tool-based retrieval adds 2.3x overhead vs direct context injection. RAG reads = hook pattern; RAG writes = tool calls.

2. **Google CalDAV requires OAuth 2.0 (not Basic Auth)** — Basic Auth for Google Calendar was deprecated March 14, 2025. Testing on Nextcloud (which works with Basic Auth) will not catch this. Implement pluggable auth strategy upfront: BasicAuth for Nextcloud/Radicale, OAuth2 for Google, app-specific passwords for iCloud.

3. **OpenRouter free tier rate limits cause silent failures** — 20 req/min, 200/day; 2-3 concurrent voice sessions exhaust this quickly. Agent must handle 429 with verbal fallback ("give me a moment"), not silence. Budget for paid tier before any external users.

4. **LightRAG query latency degrades at scale without tuning** — Default config handles dev datasets; after 10k+ documents, queries go from ~2s to 15s+. Set 250ms HTTP timeout on agent-side LightRAG calls, use `local` retrieval mode as default (faster than `hybrid`), monitor P95 latency not average.

5. **Voice cloning is incompatible with Kokoro** — Kokoro has fixed pre-trained voices; it cannot clone from audio samples. Any voice cloning milestone requires a different TTS engine (F5-TTS). Conflating "voice selection" (Kokoro built-ins, easy) with "voice cloning" (different engine, latency tradeoffs, consent requirements) will cause architectural confusion.

## Implications for Roadmap

Based on research, the build order is driven by dependency chains and risk isolation. Infrastructure changes first (config-only, lowest risk), then the LLM tool foundation, then knowledge/calendar features that depend on it.

### Phase 1: Infrastructure Baseline
**Rationale:** LiveKit Cloud migration and livekit-agents upgrade are config/dependency changes with zero code risk. Must be done first to establish a stable, production-like environment for all subsequent testing. Removes the llama.cpp Docker service. Establishes OpenRouter as the LLM backend.
**Delivers:** Stable cloud-connected agent with capable LLM (70B vs local small model), reduced Docker compose complexity
**Addresses:** OpenRouter LLM wiring (P1), LiveKit Cloud migration (P2)
**Avoids:** Anti-Pattern 5 (removing llama.cpp before OpenRouter is verified) — implement toggle first, verify, then remove

### Phase 2: LightRAG Integration
**Rationale:** LightRAG is the foundation dependency for memory recall, document upload, and voice-commanded saving. Must be operational and latency-validated before building features on top of it. Pitfall data shows RAG latency is the most likely feature-killer if not addressed early.
**Delivers:** Knowledge graph service on Coolify, agent can query and insert, document upload UI in Next.js
**Addresses:** Cross-session memory recall (P1), document upload (P1), voice-commanded saving (P1)
**Avoids:** Pitfall 1 (RAG tool call latency) — implement `on_user_turn_completed` hook pattern from the start; Pitfall 2 (LightRAG scale degradation) — set timeouts and test with real document volume before shipping

### Phase 3: Calendar Integration
**Rationale:** Calendar is independent of LightRAG. After LightRAG is proven and latency is understood, calendar adds the second major tool category. Must address Google OAuth upfront, not as an afterthought.
**Delivers:** Voice calendar read and event creation via CalDAV (Nextcloud + Google + iCloud)
**Addresses:** Calendar read (P1), calendar event creation (P2)
**Avoids:** Pitfall 3 (Google CalDAV OAuth) — build pluggable auth strategy (Basic/OAuth/app-password) before any CalDAV code; Pitfall 5 (CalDAV provider inconsistencies) — test against all three providers

### Phase 4: TTS Voice Selection
**Rationale:** Kokoro built-in multi-voice support is low-effort (voice param already works). Implementing this as a distinct phase after core functionality is proven prevents scope creep from voice cloning confusion. Must clearly scope as "built-in voices only."
**Delivers:** Voice picker UI, configurable voice per session, Kokoro voicepack selection
**Addresses:** Multiple TTS voice options (P2)
**Avoids:** Pitfall 6 (voice cloning/Kokoro conflict) — scope this phase explicitly as Kokoro built-in voices; voice cloning is a separate future phase with a different TTS engine

### Phase 5: Voice Cloning (Future)
**Rationale:** Deferred because it requires evaluating and integrating a second TTS engine (F5-TTS or Coqui XTTS), adding latency tradeoffs (~300-800ms TTFB vs Kokoro's ~80ms), and implementing consent logging. Cannot be coupled with existing Kokoro pipeline without a `BaseTTS` abstraction layer.
**Delivers:** Async voice creation from reference audio sample; separate voice creation UI
**Addresses:** Voice cloning (P3)
**Uses:** F5-TTS (zero-shot cloning from ~5s reference); BaseTTS abstraction layer to keep agent code engine-agnostic

### Phase Ordering Rationale

- Infrastructure first because OpenRouter's 70B model is required for reliable function tool invocation — smaller local models miss tool calls. Unblocks realistic testing of all subsequent features.
- LightRAG second because memory is the most compelling differentiator and the highest-risk integration (latency). Proving it works at acceptable latency gates everything built on top of it.
- Calendar third because it has no LightRAG dependency but adds the second major tool category. Google OAuth complexity means it needs focused attention, not bundling with LightRAG work.
- TTS voice selection fourth because it is independent and low-risk; sequencing it after core features ensures polish doesn't ship before substance.
- Voice cloning deferred because it requires architecture decisions (TTS abstraction layer) that should not be made under feature pressure.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (LightRAG):** LightRAG HTTP API schema needs validation against a running instance before writing client code; Coolify deployment steps unverified — research-phase recommended
- **Phase 3 (CalDAV):** Google OAuth 2.0 flow with `google-auth` and refresh token handling needs step-by-step validation; iCloud app-specific password behavior needs end-to-end test — research-phase recommended
- **Phase 5 (Voice Cloning):** F5-TTS latency is hardware-dependent and must be measured locally before committing to inline vs offline generation strategy — research-phase required when this reaches planning

Phases with standard patterns (skip research-phase):
- **Phase 1 (Infrastructure):** LiveKit Cloud migration is documented as config-only; OpenRouter integration is verified via official LiveKit docs — standard implementation
- **Phase 4 (TTS Voice Selection):** Kokoro voice selection is already functional; UI pattern is straightforward — standard implementation

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core recommendations (OpenRouter, LiveKit Cloud, caldav, httpx) verified against official docs. LightRAG API shape confirmed via GitHub README but exact schema needs runtime validation. F5-TTS capabilities verified but latency is hardware-dependent. |
| Features | MEDIUM-HIGH | Table stakes and differentiators well-established via LiveKit official docs and competitive analysis. Voice cloning scope is MEDIUM due to rapidly-evolving open-source TTS landscape. |
| Architecture | HIGH | Build order derived directly from dependency analysis of existing codebase. All integration patterns verified against official docs. Component responsibilities clearly bounded. |
| Pitfalls | MEDIUM-HIGH | Top pitfalls (RAG latency, Google CalDAV OAuth) have HIGH-confidence sources. LightRAG production scale degradation is MEDIUM (single blog source + GitHub issues pattern). |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **LightRAG API schema at runtime:** The `/query` response field name (`response` vs `result`), exact request body for `/documents/text`, and authentication method need validation against a live LightRAG instance before writing the client. Reserve time for a spike during the LightRAG phase.
- **caldav async API methods:** The `caldav.aio` module exists but its maturity relative to `run_in_executor` is unclear. Validate at implementation time which approach is stable in caldav 2.2.6.
- **OpenRouter free tier vs paid tier decision point:** The roadmap should include an explicit decision gate — if more than one user will test the system, paid tier credits must be loaded before Phase 2 begins.
- **F5-TTS local latency:** The 300-800ms TTFB range is hardware-dependent. Phase 5 planning requires measuring actual latency on the target hardware before deciding between inline cloning (real-time) and offline voice creation (async pre-generation).

## Sources

### Primary (HIGH confidence)
- https://docs.livekit.io/agents/models/llm/plugins/openrouter/ — OpenRouter integration pattern
- https://docs.livekit.io/agents/build/tools/ — function_tool decorator, tool patterns
- https://docs.livekit.io/agents/build/external-data/ — on_user_turn_completed RAG pattern
- https://docs.livekit.io/intro/cloud/ — LiveKit Cloud migration portability
- https://pypi.org/project/caldav/ — caldav 2.2.6 release and async support
- https://developers.google.com/workspace/calendar/caldav/v2/auth — Google CalDAV OAuth requirement
- https://huggingface.co/hexgrad/Kokoro-82M — Kokoro voice capabilities and limitations
- https://github.com/livekit/agents/releases — livekit-agents version history

### Secondary (MEDIUM confidence)
- https://github.com/HKUDS/LightRAG/blob/main/lightrag/api/README.md — LightRAG REST API endpoints (partial content)
- https://pypi.org/project/lightrag-hku/ — lightrag-hku 1.4.9.11 active release
- https://openrouter.ai/docs/api/reference/limits — OpenRouter rate limits
- https://arxiv.org/html/2510.02044v1 — Tool-based RAG 2.3x latency overhead (peer-reviewed)
- https://developer.vonage.com/en/blog/reducing-rag-pipeline-latency-for-real-time-voice-conversations — RAG latency patterns for voice
- https://github.com/SWivid/F5-TTS — F5-TTS voice cloning capabilities
- https://github.com/remsky/Kokoro-FastAPI — Kokoro multi-voice support

### Tertiary (LOW confidence)
- https://dasroot.net/posts/2026/02/rag-latency-optimization-vector-database-caching-hybrid-search/ — LightRAG production scale degradation (single source; verify independently)
- https://vatsalshah.in/blog/voice-ai-agents-2026-guide — Voice AI agent patterns 2026 (single blog)

---
*Research completed: 2026-02-23*
*Ready for roadmap: yes*
