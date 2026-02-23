# Pitfalls Research

**Domain:** Real-time voice AI assistant with RAG, cloud LLM, calendar integration, voice cloning
**Researched:** 2026-02-23
**Confidence:** MEDIUM (multiple sources verified; some LightRAG production specifics LOW)

---

## Critical Pitfalls

### Pitfall 1: RAG Tool Calls Add Unacceptable Latency to Voice Conversations

**What goes wrong:**
The agent invokes LightRAG as a `@function_tool()` during conversation. Each tool call requires: LLM decides to call tool → tool executes HTTP request to LightRAG → result returned → LLM generates final response. That is a minimum of two full LLM round-trips. Research shows tool-based retrieval increases first-token response time by 2.3x compared to direct context injection. At OpenRouter free-tier latency (~500-800ms per LLM call), that compounds to 1.5-2.5 seconds of pure overhead before the agent speaks.

**Why it happens:**
The natural instinct is to wire RAG as a tool because the LiveKit Agents SDK makes `@function_tool()` easy to use. It looks clean. It is also slow for real-time voice.

**How to avoid:**
Use `on_user_turn_completed` hook for RAG lookups instead of tool calls. This hook fires after STT transcribes the user's turn, before the LLM generates a response. Inject retrieved context directly into the chat context. LiveKit's official docs explicitly recommend this pattern: "This method can be highly performant as it avoids the extra round-trips involved in tool calls." Reserve `@function_tool()` only for write operations (saving to RAG, creating calendar events) where an explicit LLM decision is needed.

**Warning signs:**
- Agent response latency consistently above 1.5 seconds after adding RAG
- Users notice a perceptible "pause" before every response, not just novel queries
- LightRAG logs show queries happening after LLM has already started generating

**Phase to address:** OpenRouter + LightRAG integration phase

---

### Pitfall 2: LightRAG Query Latency Degrades Severely at Scale Without Tuning

**What goes wrong:**
LightRAG's default configuration is optimized for development, not production. After indexing 10,000+ documents, query latency degrades from ~2 seconds to 15+ seconds. In a voice agent where total tolerable pipeline latency is 800ms-1.5s, a 15-second RAG lookup breaks the entire experience.

**Why it happens:**
Default database configurations (particularly for Neo4j/vector store memory settings) are conservative. The graph traversal in LightRAG's dual-level retrieval (local + global graph) is expensive without proper indexing and memory allocation. Developers test with small document sets where defaults work fine, then deploy with real user data.

**How to avoid:**
- Tune vector database memory settings before production (3-5x performance improvement documented)
- Set strict timeouts on LightRAG HTTP requests (250ms max) in the agent; fall back to LLM-only response if exceeded
- Monitor LightRAG query P95 latency, not just average — averages hide tail latency spikes
- Start with the `mix` retrieval mode (LightRAG's hybrid local+global) only for complex queries; use `local` mode as default for faster lookups

**Warning signs:**
- RAG query P95 latency >500ms during early testing
- Latency spikes correlating with document count increases
- Memory pressure on Coolify host running LightRAG

**Phase to address:** LightRAG integration phase (before document ingestion scales up)

---

### Pitfall 3: Google Calendar Requires OAuth 2.0 — Basic Auth Is Broken

**What goes wrong:**
The `caldav` Python library supports Basic Auth, which works fine for Nextcloud/Radicale. For Google Calendar, Basic Auth has been fully deprecated since March 14, 2025. Any attempt to use username/password authentication with Google CalDAV returns HTTP 401 with no useful error message.

**Why it happens:**
The CalDAV protocol supports multiple auth methods. Developers test locally with Nextcloud (Basic Auth works fine) and discover Google incompatibility in production. The error message looks like a credentials problem, not an auth method problem, leading to extended debugging.

**How to avoid:**
- Implement authentication as a pluggable strategy: `BasicAuthCalDAV` for Nextcloud/Radicale, `OAuthCalDAV` for Google
- For Google: use OAuth 2.0 with `google-auth` library; store refresh tokens securely
- For iCloud: use app-specific passwords (not main Apple ID password); iCloud does NOT support standard OAuth
- Document clearly in setup which auth method to use per provider

**Warning signs:**
- 401 errors specifically with Google Calendar endpoints
- Nextcloud working fine but Google failing with same credentials
- Error logs showing `401 Unauthorized` without a `WWW-Authenticate: Bearer` challenge

**Phase to address:** CalDAV integration phase

---

### Pitfall 4: OpenRouter Free Tier Rate Limits Break Multi-Turn Voice Conversations

**What goes wrong:**
Free tier is capped at 20 requests per minute and 50 requests per day (no prior purchases) or 200/day (with prior credits). A voice conversation with RAG lookups can burn 5-10 LLM calls in a single extended session. Multiple users simultaneously will exhaust the daily quota mid-day. When limits are hit, the agent gets 429 errors and goes silent — the user hears nothing, with no explanation.

**Why it happens:**
Rate limits are per-account, not per-user. Developers test alone and never hit limits. Production with even 2-3 concurrent users hits limits within hours.

**How to avoid:**
- Implement exponential backoff with user-facing verbal fallback: "I'm having trouble thinking right now, give me a moment"
- Add request counting/monitoring with alerts before hitting daily limits
- Design for model fallback: if Llama 3.3 70B free tier hits limits, fall back to a smaller paid model
- Budget for OpenRouter paid tier ($0.10-0.30/M tokens) before launching to external users
- Never rely on free tier for production with multiple users

**Warning signs:**
- 429 responses from OpenRouter in logs
- Daily quota exhausted before end of day during testing with 2+ simultaneous sessions
- Agent silences with no error displayed to user

**Phase to address:** OpenRouter migration phase (build error handling before adding users)

---

### Pitfall 5: CalDAV Server Inconsistencies Across Providers Break Generic Code

**What goes wrong:**
The CalDAV RFC has many optional components and ambiguous sections. What works with Nextcloud may silently fail or return empty results with Google or iCloud. Specific known issues:
- Google: requires specifying `event=True` or `todo=True` in search queries; omitting returns nothing
- Nextcloud (v22+): forbids recreating a calendar item with the ID of a previously deleted item
- iCloud: does not support PATCH — must use full PUT for updates
- Events with slashes in their iCal UID cause errors on some servers
- Google's `principal` discovery fails in some client implementations

**Why it happens:**
Developers test against one CalDAV server (usually the one they personally use) and assume the protocol is uniform. Edge cases only surface when users report broken calendar integration.

**How to avoid:**
- Test against all three major targets during development: Nextcloud, Google Calendar, iCloud
- Always pass `event=True` when searching for events (never omit)
- Use the `caldav` Python library (actively maintained, v0.x+ has server compat fixes)
- Implement provider detection and conditional code paths where necessary
- Never use PATCH; always use PUT for updates

**Warning signs:**
- Empty results on calendar queries despite events existing
- Exception on calendar item creation/update for specific users
- Errors mentioning "UID" or "object not found" on updates

**Phase to address:** CalDAV integration phase

---

### Pitfall 6: Voice Cloning Requires a Different TTS Engine — Kokoro Does Not Support It

**What goes wrong:**
The project roadmap lists "voice cloning support" as a feature. Kokoro-82M does not support voice cloning. It has a fixed set of built-in voices (e.g., `af_nova`). Adding voice cloning requires either switching TTS engines (e.g., Coqui XTTS, F5-TTS, Cheetah) or running a second TTS service in parallel. This is a significant architecture change if not planned early.

**Why it happens:**
Kokoro's quality and simplicity makes it the right default TTS. Voice cloning is often listed as a future feature without evaluating whether the chosen engine supports it.

**How to avoid:**
- Scope voice cloning as a distinct phase that may require a parallel TTS engine
- Evaluate F5-TTS or Coqui XTTS as voice cloning candidates — both are open-source and Docker-deployable
- Design the TTS layer as an interface (`BaseTTS`) so swapping engines doesn't require rewriting agent code
- Make "multiple voice options" (from Kokoro's built-in voices) a separate deliverable from true "voice cloning"
- For voice cloning: require explicit consent and consent-logging before cloning any voice

**Warning signs:**
- Attempting to use Kokoro for custom voice training
- Voice cloning planned in the same phase as basic TTS voice selection
- No abstraction layer between agent code and specific TTS library calls

**Phase to address:** TTS enhancement phase (plan for this before writing TTS integration code)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| RAG as tool call instead of `on_user_turn_completed` | Simpler code | 2x+ latency penalty on every response | Never for read-only lookups |
| Hardcode OpenRouter model name | Simpler config | Can't switch models without code change | MVP only — add model config before first external user |
| Single CalDAV auth method (Basic only) | Less code | Google/iCloud users can't connect | Never — build auth strategy abstraction upfront |
| Load all user data in agent entrypoint | Simple to implement | Blocks agent startup; "unready" agent shown to user | Never — use prewarm + metadata pattern |
| No timeout on LightRAG HTTP calls | Simpler code | Slow LightRAG query stalls entire voice response | Never — always set timeouts |
| Trust LightRAG `local` retrieval mode for all queries | Fewer query params | Poor recall on multi-hop or global questions | Acceptable for MVP if documented as known limitation |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LiveKit Cloud | Using self-hosted API URL/key after migration | Update `LIVEKIT_URL` env var to `*.livekit.cloud` endpoint; agent code is identical |
| LiveKit Cloud | Expecting agent to appear instantly | Agent workers must be running and connected to LiveKit Cloud before rooms are created |
| OpenRouter | Using model ID without `:free` suffix for free tier | Free models use `meta-llama/llama-3.3-70b-instruct:free` — omitting `:free` charges credits |
| OpenRouter | Not handling 402 (negative balance) error | Negative balance blocks all requests including free models; handle 402 separately from 429 |
| LightRAG on Coolify | Accessing LightRAG from agent via `localhost` | Agent and LightRAG are on different hosts; use Coolify's external URL with HTTPS |
| LightRAG | Ignoring document processing time in UX | Large document ingestion is async; UI must show processing state, not assume instant availability |
| CalDAV (Google) | Using Basic Auth post-March 2025 | OAuth 2.0 required; implement `google-auth` with refresh token flow |
| CalDAV (iCloud) | Using Apple ID password directly | Use app-specific password from appleid.apple.com; main password will be rejected |
| Docker | Agent container calling Coolify LightRAG via internal Docker network | LightRAG is on a different host (Coolify); use external HTTPS URL, not Docker network names |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| RAG on every turn via tool call | Every response takes 1.5-2.5s minimum | Use `on_user_turn_completed` hook for context injection | Immediately — even at 1 user |
| LightRAG without query timeout | Occasional 15-30s silences in conversation | Set 250ms HTTP timeout; verbal fallback on timeout | After 5,000+ indexed documents |
| No connection pooling to LightRAG | Connection overhead adds 50-100ms per request | Use `httpx.AsyncClient` with connection pool (reuse across turns) | At any real usage |
| Injecting full RAG document chunks into context | Token bloat causes slower LLM generation + cost increase | Summarize retrieved chunks before injection; limit to top-2 results | After context window fills (~3 long turns with large chunks) |
| OpenRouter streaming not used | Increased TTS start latency | Use `stream=True` for all LLM calls; pipe tokens to TTS as they arrive | At every request |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing CalDAV credentials (OAuth tokens, app passwords) in Docker env vars unencrypted | Credential leak via Docker inspect or log files | Use Docker secrets or encrypted env store; never log credential values |
| No voice consent verification for voice cloning | Cloning someone's voice without consent; legal liability | Require explicit opt-in; log consent with timestamp and voice sample hash |
| Exposing LightRAG API endpoint without authentication | Anyone can query or inject into the knowledge graph | LightRAG should be network-restricted on Coolify; add API key auth if exposing publicly |
| Trusting RAG-retrieved content as safe prompt input | Prompt injection via malicious documents indexed into LightRAG | Sanitize retrieved content before injecting into system prompt; limit injection scope |
| Logging full conversation transcripts including personal data | PII retention risk | Log only session IDs and error events; never log full transcripts without explicit consent |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent failure when OpenRouter rate-limited | User thinks agent is broken or ignoring them | Speak a fallback: "I need a moment to think" while retrying |
| No progress signal during calendar event creation | User repeats the request thinking it wasn't heard | Acknowledge verbally: "Let me add that to your calendar" before the tool executes |
| RAG returning irrelevant results without fallback | Agent confidently gives wrong information from context | Include relevance score threshold; if below threshold, don't inject context |
| Voice selection UI showing cloning option before it's implemented | User frustration when cloning doesn't work | Ship multi-voice selection (Kokoro built-ins) first; add cloning as separate visible feature later |
| No feedback when document upload is processing | User thinks upload failed; uploads again | Show async processing state with estimated time |

---

## "Looks Done But Isn't" Checklist

- [ ] **OpenRouter integration:** Often missing retry/backoff for 429/402 errors — verify agent handles rate limit silences gracefully, not with a crash
- [ ] **LiveKit Cloud migration:** Often missing agent worker deployment update — verify agent is configured with Cloud URL/keys, not self-hosted vars
- [ ] **LightRAG RAG:** Often missing timeout handling — verify a slow LightRAG query does not block the voice response indefinitely
- [ ] **CalDAV Google:** Often missing OAuth token refresh — verify access tokens refresh automatically; they expire in 1 hour
- [ ] **CalDAV iCloud:** Often missing app-specific password docs — verify setup docs tell users exactly where to generate the app-specific password
- [ ] **Voice cloning:** Often confused with "voice selection" — verify the roadmap distinguishes Kokoro built-in voices (easy, now) from true cloning (hard, later, different engine)
- [ ] **Document ingestion:** Often missing ingestion status feedback — verify UI shows processing state after upload, not just a success flash
- [ ] **LightRAG production:** Often missing query latency monitoring — verify P95 latency alerts are in place before real document volume grows

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| RAG wired as tool call (latency) | LOW | Move lookup to `on_user_turn_completed` hook; no architecture change needed |
| LightRAG latency degradation | MEDIUM | Tune DB memory settings; add timeout + fallback; may require Coolify resource upgrade |
| Google CalDAV Basic Auth broken | MEDIUM | Implement OAuth 2.0 flow; requires user re-authorization |
| Free tier rate limits exhausted | LOW | Add OpenRouter credits ($5-10 gets substantial headroom); update error handling |
| Voice cloning added to Kokoro (not supported) | HIGH | Requires adding second TTS engine, new Docker service, updated audio pipeline routing |
| LightRAG exposed without auth | HIGH | Restrict network access immediately; audit what was queried/injected during exposure |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| RAG tool call latency | LightRAG integration | Measure P95 response latency with RAG enabled; must be <800ms total |
| LightRAG query degradation at scale | LightRAG integration | Load test with 1,000+ documents before releasing document ingestion UI |
| Google CalDAV OAuth required | CalDAV integration | Test against Google Calendar with OAuth flow end-to-end before shipping |
| OpenRouter rate limit silences | OpenRouter migration | Simulate 429 response; verify agent speaks fallback, does not crash |
| CalDAV provider inconsistencies | CalDAV integration | Run integration test suite against Nextcloud + Google + iCloud |
| Voice cloning needs different TTS engine | TTS enhancement phase | Confirm Kokoro scope (built-in voices only) before writing TTS abstraction layer |
| LightRAG no timeout | LightRAG integration | Verify HTTP client has explicit timeout; verify fallback behavior in conversation |
| CalDAV credential security | CalDAV integration | Audit Docker env vars; verify tokens not logged |

---

## Sources

- LiveKit Agents external data docs: https://docs.livekit.io/agents/logic/external-data/ (HIGH confidence — official docs)
- LiveKit function tools docs: https://docs.livekit.io/agents/logic/tools/ (HIGH confidence — official docs)
- OpenRouter rate limits: https://openrouter.ai/docs/api/reference/limits (MEDIUM confidence — official docs, some values templated)
- Vonage: Reducing RAG Pipeline Latency for Real-Time Voice Conversations: https://developer.vonage.com/en/blog/reducing-rag-pipeline-latency-for-real-time-voice-conversations (MEDIUM — engineering blog, verified patterns)
- Stream RAG latency research (2.3x overhead for tool-based retrieval): https://arxiv.org/html/2510.02044v1 (MEDIUM — peer-reviewed)
- LightRAG production latency degradation: https://dasroot.net/posts/2026/02/rag-latency-optimization-vector-database-caching-hybrid-search/ (LOW — single source, verify independently)
- LightRAG GitHub: https://github.com/HKUDS/LightRAG (HIGH confidence — official)
- python-caldav library docs: https://caldav.readthedocs.io/latest/about.html (HIGH confidence — official)
- Google CalDAV OAuth requirement (March 2025): https://developers.google.com/workspace/calendar/caldav/v2/auth (HIGH confidence — official Google)
- iCloud CalDAV app-specific passwords: https://www.aurinko.io/blog/caldav-apple-calendar-integration/ (MEDIUM — verified against Apple docs pattern)
- Kokoro-82M model card: https://huggingface.co/hexgrad/Kokoro-82M (HIGH confidence — official model card confirms no voice cloning support)
- Voice cloning ethics: https://milvus.io/ai-quick-reference/what-are-the-ethical-implications-of-voice-cloning-in-tts (MEDIUM)

---
*Pitfalls research for: Local Voice AI Assistant — milestone adding OpenRouter, LiveKit Cloud, LightRAG, CalDAV, voice cloning*
*Researched: 2026-02-23*
