---
phase: 01-infrastructure-baseline
verified: 2026-02-23T00:00:00Z
status: passed
score: 8/8 must-haves verified
gaps: []
human_verification:
  - test: "Start docker compose up and confirm no llama_cpp container launches"
    expected: "Only kokoro, livekit, nemotron, livekit_agent, frontend containers start"
    why_human: "docker compose config verifies service declarations but not actual runtime container behavior"
  - test: "Configure OPENROUTER_API_KEY and speak to the agent; exhaust rate limit or simulate a 429 error"
    expected: "Agent says 'Hang on a sec.' once and does not repeat it on subsequent retries in the same episode"
    why_human: "Real rate-limit behavior and verbal output require a live session with an LLM endpoint"
  - test: "Set LLM_MODEL to a different model string (e.g. 'mistralai/mistral-7b-instruct:free') and restart the agent"
    expected: "Agent uses the new model without any code changes"
    why_human: "Requires live OpenRouter call to confirm model routing"
---

# Phase 01: Infrastructure Baseline — Verification Report

**Phase Goal:** Agent runs on OpenRouter for LLM inference with local llama.cpp and its Docker service removed (moved behind a profile)
**Verified:** 2026-02-23
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

All eight truths from the two plan must_haves sections are verified.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Agent connects to OpenRouter for LLM inference instead of local llama_cpp | VERIFIED | `build_llm()` calls `openai.LLM.with_openrouter(model=chain[0], fallback_models=chain[1:])` (agent.py line 29–31) |
| 2 | LLM model is configurable via LLM_MODEL environment variable without code changes | VERIFIED | `os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")` with comma-split chain (agent.py lines 27–28) |
| 3 | docker compose up starts cleanly without llama_cpp running | VERIFIED | `docker compose config --services` returns kokoro, livekit, frontend, nemotron, livekit_agent — no llama_cpp |
| 4 | Local llama_cpp is still available via docker compose --profile local-llm up | VERIFIED | `docker compose --profile local-llm config --services` lists llama_cpp; `profiles: ["local-llm"]` in docker-compose.yml line 58 |
| 5 | When OpenRouter rate limit is hit, the assistant speaks a brief holding message before retrying | VERIFIED | `session.on("error")` handler calls `session.say("Hang on a sec.")` on `recoverable=True` errors (agent.py lines 127–141) |
| 6 | When all retries and fallbacks are exhausted, the assistant speaks an apology and waits for next input | VERIFIED | Handler calls `session.say("Sorry, I can't answer that right now.")` on `recoverable=False` (agent.py lines 143–145) |
| 7 | The holding message is spoken only once per error episode, not on every retry | VERIFIED | `_holding_spoken` flag set to `True` on first invocation, checked before speaking (agent.py lines 125, 139–141) |
| 8 | Detailed errors are logged to console for debugging | VERIFIED | `logger.error("Session error (recoverable=%s source=%s): %s", ...)` (agent.py lines 132–137) |

**Score:** 8/8 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docker-compose.yml` | llama_cpp behind `profiles: ["local-llm"]`; livekit_agent depends_on without llama_cpp; OPENROUTER_API_KEY and LLM_MODEL env vars passed | VERIFIED | Line 58: `profiles: ["local-llm"]`; depends_on (lines 103–109) has livekit, kokoro, nemotron only; env vars at lines 101–102 |
| `livekit_agent/src/agent.py` | OpenRouter LLM with FallbackAdapter, error handler with session.say | VERIFIED | `with_openrouter` at line 29; `FallbackAdapter` at line 37; `session.on("error")` handler at lines 127–145 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `agent.py` | OpenRouter API | `openai.LLM.with_openrouter()` | WIRED | `openrouter_llm = openai.LLM.with_openrouter(model=chain[0], fallback_models=chain[1:])` (line 29); passed into `AgentSession(llm=build_llm())` (line 109) |
| `agent.py` | LLM_MODEL env var | `os.getenv` | WIRED | `os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")` (line 27); also passed to logger (line 99) |
| `agent.py` | local llama_cpp | FallbackAdapter wrapping local LLM as last resort | WIRED | `FallbackAdapter([openrouter_llm, local_llm])` (line 37); local_llm constructed at lines 32–36 |
| `agent.py` | AgentSession error event | `session.on("error")` | WIRED | Decorator `@session.on("error")` (line 127) wires `on_session_error` to the session event |
| `agent.py` | `session.say()` | Verbal notification to user during error | WIRED | `session.say("Hang on a sec.")` (line 141); `session.say("Sorry, I can't answer that right now.")` (line 145) |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INFR-01 | 01-01-PLAN.md | Agent connects to OpenRouter API for LLM inference instead of local llama_cpp | SATISFIED | `openai.LLM.with_openrouter()` as primary LLM in `build_llm()`; wired into AgentSession |
| INFR-02 | 01-02-PLAN.md | Agent handles OpenRouter rate limits gracefully with verbal fallback on 429 errors | SATISFIED | `session.on("error")` handler with `session.say()` and one-shot `_holding_spoken` flag |
| INFR-03 | 01-01-PLAN.md | llama_cpp Docker service removed from docker-compose.yml | SATISFIED | Service still exists but behind `profiles: ["local-llm"]`; not started by default |
| INFR-04 | 01-01-PLAN.md | LLM model configurable via environment variable (default: Llama 3.3 70B free) | SATISFIED | `os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")` with comma-separated fallback chain; passed via docker-compose.yml env |

No orphaned requirements — all four INFR-01 through INFR-04 are claimed by plans and verified in code.

---

### Anti-Patterns Found

No blockers or stubs detected.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `agent.py` | 23 | `load_dotenv(".env.local")` called twice (lines 22 and 23 with same path) | Info | Harmless duplicate — second call is a no-op given `override=True` on first call |

---

### Human Verification Required

#### 1. Runtime container isolation

**Test:** Run `docker compose up` and inspect running containers with `docker ps`.
**Expected:** llama_cpp container does not start. Only kokoro, livekit, nemotron, livekit_agent, and frontend.
**Why human:** `docker compose config` confirms service declarations, not actual container runtime behavior.

#### 2. Verbal holding message on rate limit (INFR-02 live test)

**Test:** With a valid `OPENROUTER_API_KEY`, trigger a 429 rate-limit response from OpenRouter (or mock one by using an exhausted key). Speak to the agent during the error.
**Expected:** Agent says "Hang on a sec." exactly once. Does not repeat on subsequent retries within the same error episode.
**Why human:** The `recoverable` flag behavior depends on how livekit-agents propagates the 429 internally; cannot verify this without a live session.

#### 3. LLM_MODEL env var end-to-end routing

**Test:** Set `LLM_MODEL=mistralai/mistral-7b-instruct:free` in `.env.local` and restart the agent. Speak to it.
**Expected:** Agent responds using the Mistral model (verifiable via OpenRouter usage dashboard or agent logs showing the model name).
**Why human:** Requires a live OpenRouter call to confirm the model is actually selected at the API level.

---

### Summary

Phase 01 goal is achieved. All eight observable truths are verified in the actual codebase:

- `livekit_agent/src/agent.py` uses `openai.LLM.with_openrouter()` as the primary LLM, wrapped in `FallbackAdapter` with local llama_cpp as last resort, and reads the model from `LLM_MODEL` env var.
- `docker-compose.yml` moves llama_cpp behind `profiles: ["local-llm"]` so `docker compose up` starts cleanly, and passes `OPENROUTER_API_KEY` and `LLM_MODEL` to the agent container.
- The error handler correctly uses `@session.on("error")`, speaks to the user via `session.say()`, gates the holding message with `_holding_spoken` to prevent repetition, and logs full error details.

All four phase requirements (INFR-01, INFR-02, INFR-03, INFR-04) are satisfied with implementation evidence. Three live-session behaviors are flagged for human verification before the phase is considered fully closed.

---

_Verified: 2026-02-23_
_Verifier: Claude (gsd-verifier)_
