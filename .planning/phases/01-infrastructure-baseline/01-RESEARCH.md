# Phase 1: Infrastructure Baseline - Research

**Researched:** 2026-02-23
**Domain:** LiveKit Agents OpenRouter integration, LLM fallback orchestration, Docker Compose service management
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Rate-limit fallback:**
- On rate limit: speak a casual, brief message ("Hang on a sec" style) and retry silently
- Retry window: 60 seconds with backoff before giving up
- If all retries fail: apologize briefly ("Sorry, I can't answer that right now") and drop the response — wait for next user input
- Try next model in fallback chain before doing wait-and-retry on same model

**Model selection:**
- Default model: Llama 3.3 70B (`meta-llama/llama-3.3-70b-instruct:free` on OpenRouter)
- Env var accepts comma-separated fallback chain (e.g. `LLM_MODEL=llama-3.3-70b,qwen-2.5-72b`)
- Fallback chain triggers on both rate limits and model unavailability
- Silent fallback — user is not told which model is responding

**Migration approach:**
- Remove llama.cpp service from default docker-compose.yml
- Keep local inference as a separate Docker container (compose profile) — not started by default
- Local fallback uses a smaller model (7B/8B class) that can run without GPU
- Local fallback activates automatically as last resort when entire OpenRouter chain fails
- No env var toggle needed — automatic last-resort behavior

**Voice behavior during errors:**
- Vague, friendly error message — no technical details spoken to user
- One generic message for all error types (keeps it simple and consistent)
- Assistant stays listening after error — ready for next input immediately
- Detailed errors logged to console/file for debugging

### Claude's Discretion

- Exact retry backoff strategy (exponential, linear, etc.)
- Specific error message wording
- Log format and rotation
- Which small local model to use for emergency fallback
- OpenRouter API integration patterns

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFR-01 | Agent connects to OpenRouter API for LLM inference instead of local llama_cpp | `openai.LLM.with_openrouter()` factory method is the standard integration path — no new package needed, uses existing `livekit-agents[openai]` plugin |
| INFR-02 | Agent handles OpenRouter rate limits gracefully with verbal fallback on 429 errors | `AgentSession` emits `error` event with `recoverable` field; `session.say()` can be called in the error handler to speak a fallback message before the session closes or retries |
| INFR-03 | llama_cpp Docker service removed from docker-compose.yml | Service is currently in the main compose file without a profile; move to a `profiles: ["local-llm"]` block so it is never started by default |
| INFR-04 | LLM model configurable via environment variable (default: Llama 3.3 70B free) | `openai.LLM.with_openrouter(model=os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free"))` — comma-split the env var to build the fallback chain at startup |
</phase_requirements>

---

## Summary

Phase 1 migrates the agent's LLM inference from local llama.cpp (served at `http://llama_cpp:11434/v1`) to OpenRouter. The livekit-agents OpenAI plugin already ships a `with_openrouter()` factory method that configures the correct base URL (`https://openrouter.ai/api/v1`) and authenticates with the `OPENROUTER_API_KEY` environment variable. No additional package installation is required beyond what is already in `pyproject.toml` (`livekit-agents[openai]~=1.3`).

The fallback behavior specified by the user (speak a brief holding message, try next model, retry with backoff, speak apology on total failure) cannot be handled by `openai.LLM.with_openrouter(fallback_models=[...])` alone because that mechanism handles provider-level switching but does not speak to the user. The verbal notification part requires hooking the `AgentSession` `error` event and calling `session.say()`. The model-chain retry loop (try next model → wait → give up) must be implemented as custom logic wrapped around the LLM, since `FallbackAdapter` does not expose a hook that fires before switching to signal the user.

The Docker Compose change is straightforward: remove the `llama_cpp` service block from the default service list and re-add it under `profiles: ["local-llm"]`. The `livekit_agent` service's `depends_on` entry for `llama_cpp` must also be removed. The local llama.cpp service then becomes the automatic last-resort LLM in the Python fallback chain when the entire OpenRouter chain is exhausted.

**Primary recommendation:** Use `openai.LLM.with_openrouter()` as the primary LLM; build a custom `LLMChain` wrapper (or use `llm.FallbackAdapter`) around OpenRouter primary + OpenRouter fallbacks + local llama_cpp, and hook `session.on("error")` to speak the user-facing verbal messages.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `livekit-agents[openai]` | ~1.3 (current in pyproject.toml) | OpenRouter and OpenAI-compatible LLM integration | `openai.LLM.with_openrouter()` factory method is the documented LiveKit path for OpenRouter |
| `python-dotenv` | already present | Load `OPENROUTER_API_KEY` from `.env.local` | Already in use; consistent with existing env var pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `livekit.agents.llm.FallbackAdapter` | bundled with livekit-agents | Automatic failover across LLM instances | Use for the OpenRouter → local llama.cpp chain; handles switching on `APIError` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `openai.LLM.with_openrouter()` | `openai.LLM(base_url="https://openrouter.ai/api/v1")` | `with_openrouter()` is the documented path and sets correct headers; manual `base_url` works but is undocumented and may miss headers |
| Custom retry wrapper | `openai.LLM.with_openrouter(fallback_models=[...])` | Built-in `fallback_models` handles model switching silently but cannot trigger `session.say()`; custom wrapper needed to speak the verbal holding message |

**Installation:** No new packages needed. `livekit-agents[openai]~=1.3` already includes everything required.

---

## Architecture Patterns

### Recommended Project Structure

The agent code lives entirely in `livekit_agent/src/agent.py` (single-file design per AGENTS.md). This phase does not require new files — all changes are in `agent.py` and `docker-compose.yml`.

```
livekit_agent/src/
└── agent.py    # LLM config, fallback logic, error event handler — all here
docker-compose.yml  # Remove llama_cpp from default; add to profiles: ["local-llm"]
```

### Pattern 1: OpenRouter via `with_openrouter()`

**What:** Factory method on `openai.LLM` that sets base URL and auth for OpenRouter.

**When to use:** Always — this is the documented integration path.

**Example:**
```python
# Source: https://docs.livekit.io/agents/models/llm/plugins/openrouter/
from livekit.plugins import openai as oai

llm = oai.LLM.with_openrouter(
    model="meta-llama/llama-3.3-70b-instruct:free",
)
```

Authentication is automatic from `OPENROUTER_API_KEY` environment variable.

### Pattern 2: Model fallback chain from environment variable

**What:** Parse `LLM_MODEL` env var (comma-separated) at startup to build the OpenRouter fallback list.

**When to use:** Required by INFR-04 — model must be configurable without code changes.

**Example:**
```python
import os
from livekit.plugins import openai as oai

raw_models = os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
model_chain = [m.strip() for m in raw_models.split(",")]
primary_model = model_chain[0]
fallback_models = model_chain[1:] if len(model_chain) > 1 else []

llm = oai.LLM.with_openrouter(
    model=primary_model,
    fallback_models=fallback_models,
)
```

### Pattern 3: Verbal error fallback via session error event

**What:** Subscribe to `AgentSession` error event; call `session.say()` to speak to user before session logic continues.

**When to use:** Required for INFR-02 — when OpenRouter returns 429 or all models exhausted.

**Example (conceptual — exact event API must be verified against livekit-agents 1.3 source):**
```python
# Source: https://docs.livekit.io/agents/build/events/
@session.on("error")
def on_session_error(error_event):
    if not error_event.recoverable:
        # All retries exhausted — apologize and wait for next input
        session.say("Sorry, I can't answer that right now.")
    else:
        # Transient error — speak holding message while retrying
        session.say("Hang on a sec.")
```

**Important:** The `recoverable` field on the error event distinguishes transient errors (system will retry) from terminal failures (no more retries). The verbal holding message should only fire once per error episode, not once per retry attempt. This requires state tracking (e.g., a flag that is set when the first holding message is spoken and cleared on success or terminal failure).

### Pattern 4: Local llama.cpp as last-resort via FallbackAdapter

**What:** Wrap OpenRouter LLM + local llama.cpp LLM in `FallbackAdapter`; local activates automatically when OpenRouter chain is exhausted.

**When to use:** When entire OpenRouter model chain fails after retries.

**Example:**
```python
from livekit.agents.llm import FallbackAdapter
from livekit.plugins import openai as oai

openrouter_llm = oai.LLM.with_openrouter(
    model="meta-llama/llama-3.3-70b-instruct:free",
    fallback_models=["qwen/qwen-2.5-72b-instruct:free"],
)

local_llm = oai.LLM(
    base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://llama_cpp:11434/v1"),
    model=os.getenv("LOCAL_LLM_MODEL", "llama-3.2-3b"),
    api_key="no-key-needed",
)

llm = FallbackAdapter([openrouter_llm, local_llm])
```

### Pattern 5: Docker Compose profile for local llama.cpp

**What:** Move `llama_cpp` service behind `profiles: ["local-llm"]` so it never starts by default.

**When to use:** Required for INFR-03.

```yaml
# docker-compose.yml
llama_cpp:
  profiles: ["local-llm"]   # <-- add this line
  image: ghcr.io/ggml-org/llama.cpp:server
  # ... rest of config unchanged
```

Remove from `livekit_agent.depends_on`:
```yaml
livekit_agent:
  depends_on:
    livekit:
      condition: service_started
    kokoro:
      condition: service_started
    nemotron:
      condition: service_healthy
    # llama_cpp entry removed
```

### Anti-Patterns to Avoid

- **Hardcoding the OpenRouter base URL manually:** Use `with_openrouter()` instead. The factory method may set required HTTP headers (e.g., `HTTP-Referer`, `X-Title`) beyond just the URL.
- **Using `openai.LLM.with_openrouter(fallback_models=[...])` as the only fallback mechanism:** This handles model switching but does not speak to the user. It is a silent technical fallback, not a verbal user-facing one.
- **Speaking the holding message on every retry attempt:** The message should fire once when the error is first detected, not once per internal retry tick.
- **Leaving `depends_on: llama_cpp` in livekit_agent:** After profiling llama_cpp, `docker compose up` will fail if livekit_agent still declares it as a dependency.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OpenRouter authentication | Custom header injection, manual base_url | `openai.LLM.with_openrouter()` | Factory method handles auth headers correctly and may evolve with LiveKit's OpenRouter support |
| LLM provider switching on failure | Custom try/except loop around LLM calls | `FallbackAdapter` | Handles unhealthy provider tracking, timeouts, retry intervals |
| OpenRouter model fallback at the API level | Manual model-cycling code | `with_openrouter(fallback_models=[...])` | Native OpenRouter routing; works server-side without extra round trips |

**Key insight:** The distinction between OpenRouter-level model fallback (silent, built-in) and application-level verbal notification (requires custom event handler) is the central design challenge of this phase. The right approach layers both: use `with_openrouter(fallback_models=[...])` for silent model cycling, and use the session error event for verbal user communication when needed.

---

## Common Pitfalls

### Pitfall 1: Free Tier Rate Limits Are Lower Than Expected

**What goes wrong:** OpenRouter free tier is currently 50 requests/day (reduced from 200 in 2025). In active development or with two testers, this is exhausted quickly — within an hour.

**Why it happens:** The rate limit changed in 2025. STATE.md references the old 200 req/day figure.

**How to avoid:** Purchase $10 credits to unlock 1,000 req/day. Use the `:free` suffix on model IDs only in development. For any sustained testing, use a paid account with credit.

**Warning signs:** 429 errors appearing after a short development session.

### Pitfall 2: `depends_on: llama_cpp` Left in livekit_agent After Profiling

**What goes wrong:** `docker compose up` fails because `livekit_agent` waits for `llama_cpp` which is now behind a profile and not started.

**Why it happens:** Docker Compose silently skips profiled services but honors `depends_on` references — resulting in startup failure.

**How to avoid:** Remove the `llama_cpp` entry from `livekit_agent.depends_on` at the same time as adding the profile.

**Warning signs:** `compose up` hangs or errors with "service not found" or similar.

### Pitfall 3: Speaking Holding Message on Every Retry Tick

**What goes wrong:** User hears "Hang on a sec" multiple times during a single rate-limit episode with exponential backoff.

**Why it happens:** Naively calling `session.say()` inside the error handler without tracking whether the message was already spoken.

**How to avoid:** Use a boolean flag per request lifecycle. Set it to `True` after first holding message is spoken; only speak if `False`. Clear flag on success or terminal failure.

**Warning signs:** User complains of repeated identical messages.

### Pitfall 4: FallbackAdapter Metrics Not Emitted

**What goes wrong:** `LLMMetrics` events are not emitted when `FallbackAdapter` is active (known issue #2269).

**Why it happens:** FallbackAdapter wraps LLM but does not forward metrics events from the underlying provider.

**How to avoid:** Do not rely on metrics events for monitoring in this phase. Log errors explicitly in the error handler. Treat metrics as a future improvement.

**Warning signs:** No LLM latency metrics in logs despite active conversations.

### Pitfall 5: `FallbackAdapter` vs `with_openrouter(fallback_models=[...])` Confusion

**What goes wrong:** Using both mechanisms redundantly, or using only `with_openrouter(fallback_models=[...])` and expecting verbal fallback behavior.

**Why it happens:** Both mechanisms exist for different purposes. `with_openrouter(fallback_models=[...])` is server-side OpenRouter routing. `FallbackAdapter` is application-side Python-level failover (e.g., to local llama.cpp). They are complementary, not alternatives.

**How to avoid:** Understand the layering: `with_openrouter(fallback_models=[...])` → try other OpenRouter models silently → `FallbackAdapter` → try local llama.cpp → session error event → speak apology.

---

## Code Examples

Verified patterns from official sources:

### OpenRouter basic setup
```python
# Source: https://docs.livekit.io/agents/models/llm/plugins/openrouter/
from livekit.plugins import openai

llm = openai.LLM.with_openrouter(
    model="meta-llama/llama-3.3-70b-instruct:free",
    fallback_models=["qwen/qwen-2.5-72b-instruct:free"],
)
```

### Environment variable from .env / .env.local
```bash
# .env.local
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free,qwen/qwen-2.5-72b-instruct:free
```

### Full agent.py LLM initialization (synthesized from research)
```python
import os
from livekit.agents.llm import FallbackAdapter
from livekit.plugins import openai as oai

def build_llm():
    raw_models = os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    model_chain = [m.strip() for m in raw_models.split(",")]

    openrouter_llm = oai.LLM.with_openrouter(
        model=model_chain[0],
        fallback_models=model_chain[1:],
    )

    local_llm = oai.LLM(
        base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://llama_cpp:11434/v1"),
        model=os.getenv("LOCAL_LLM_MODEL", "llama-3.2-3b"),
        api_key="no-key-needed",
    )

    return FallbackAdapter([openrouter_llm, local_llm])
```

### Error event handler with verbal fallback
```python
# Source: https://docs.livekit.io/agents/build/events/
# NOTE: Exact event API must be verified against livekit-agents 1.3 source before implementing
_holding_message_spoken = False

@session.on("error")
def on_error(error_event):
    global _holding_message_spoken
    if error_event.recoverable:
        if not _holding_message_spoken:
            session.say("Hang on a sec.")
            _holding_message_spoken = True
    else:
        session.say("Sorry, I can't answer that right now.")
        _holding_message_spoken = False
```

### Docker Compose — moving llama_cpp to profile
```yaml
llama_cpp:
  profiles: ["local-llm"]    # only starts with: docker compose --profile local-llm up
  image: ghcr.io/ggml-org/llama.cpp:server
  command:
    - --host
    - 0.0.0.0
    - --port
    - "11434"
    - --hf-repo
    - "${LLAMA_HF_REPO:-unsloth/Qwen3-4B-Instruct-2507-GGUF}"
    - --alias
    - "${LLAMA_MODEL_ALIAS:-qwen3-4b}"
    - --ctx-size
    - "${LLAMA_CTX_SIZE:-16384}"
  # ... rest unchanged
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `openai.LLM(base_url="http://llama_cpp:11434/v1")` | `openai.LLM.with_openrouter()` | livekit-agents added OpenRouter support (2024-2025) | Native factory method handles auth; no manual header configuration needed |
| 200 req/day free tier | 50 req/day free tier | 2025 (OpenRouter policy change) | Must use paid account ($10 credit → 1000 req/day) for sustained development |
| `VoicePipelineAgent` | `AgentSession` | livekit-agents v1.x | STATE.md and agent.py already use the new `AgentSession` API — no migration needed |

**Deprecated/outdated:**
- `llama_cpp` service running without a profile: being removed in this phase
- `LLAMA_MODEL`, `LLAMA_BASE_URL`, `LLAMA_API_KEY` env vars: will be replaced by `LLM_MODEL`, `OPENROUTER_API_KEY`, and `LOCAL_LLM_BASE_URL`/`LOCAL_LLM_MODEL` for clarity

---

## Open Questions

1. **Exact session error event API in livekit-agents 1.3**
   - What we know: `AgentSession` emits an error event with a `recoverable` field; `session.say()` is callable from the handler
   - What's unclear: The precise event name, handler signature, and whether `session.say()` is available as an awaitable or sync call in that context
   - Recommendation: Read `livekit-agents` source at `livekit/agents/voice/agent.py` (or equivalent) before implementing the error handler — takes 5 minutes and prevents wrong-API assumptions

2. **Whether `with_openrouter(fallback_models=[...])` fires an error event when it switches models**
   - What we know: The FallbackAdapter fires error events when switching; the `with_openrouter` fallback_models parameter is a different (server-side) mechanism
   - What's unclear: Whether a 429 on the primary model with fallback_models available results in an application-level error event or is silently swallowed
   - Recommendation: Test empirically with a rate-limited primary model before relying on the error event for verbal notification

3. **Which small 7B/8B model for local fallback**
   - What we know: Existing llama_cpp service uses `unsloth/Qwen3-4B-Instruct-2507-GGUF`; this is already a 4B model suitable for CPU
   - What's unclear: Whether Qwen3-4B is an acceptable emergency fallback or whether a different model (e.g., Llama 3.2 3B) would be better
   - Recommendation: Keep the existing `LLAMA_HF_REPO` and model alias defaults for the local service since they are already tested in this codebase; Claude's discretion per CONTEXT.md

---

## Sources

### Primary (HIGH confidence)
- https://docs.livekit.io/agents/models/llm/plugins/openrouter/ — `with_openrouter()` factory method, `fallback_models` parameter, env var name (`OPENROUTER_API_KEY`), installation
- https://docs.livekit.io/agents/build/events/ — AgentSession error events, `recoverable` field, `session.say()` usage pattern for error responses
- https://docs.livekit.io/reference/python/livekit/agents/llm/fallback_adapter.html — FallbackAdapter constructor parameters, switching behavior
- https://openrouter.ai/docs/api/reference/errors-and-debugging — 429 error response format
- Codebase read: `livekit_agent/src/agent.py` — current LLM wiring, env var names, plugin usage
- Codebase read: `docker-compose.yml` — current llama_cpp service definition and livekit_agent depends_on

### Secondary (MEDIUM confidence)
- https://github.com/livekit/agents/blob/main/livekit-plugins/livekit-plugins-openai/livekit/plugins/openai/llm.py — `max_retries=0` default, no built-in 429 handling at the plugin level
- https://github.com/livekit/agents/issues/2132 — AgentSession session closure behavior on unrecoverable errors; PR #2345 fix
- WebSearch: OpenRouter free tier now 50 req/day (was 200) — confirmed by multiple sources including openrouter.ai/docs

### Tertiary (LOW confidence)
- WebSearch: FallbackAdapter does not emit LLMMetrics (issue #2269) — single GitHub issue, unverified in current livekit-agents 1.3

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `with_openrouter()` is documented on official LiveKit docs with code examples
- Architecture: MEDIUM-HIGH — error event pattern confirmed in official docs; exact 1.3 handler signature needs source verification
- Pitfalls: MEDIUM — rate limit change confirmed via multiple sources; FallbackAdapter/depends_on pitfall is logical deduction from documented behavior

**Research date:** 2026-02-23
**Valid until:** 2026-03-23 (30 days — stable APIs, but OpenRouter free tier limits change frequently)
