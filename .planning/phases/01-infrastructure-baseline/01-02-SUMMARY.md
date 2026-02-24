---
phase: 01-infrastructure-baseline
plan: 02
subsystem: infra
tags: [livekit-agents, error-handling, verbal-fallback, AgentSession, FallbackAdapter]

requires:
  - phase: 01-infrastructure-baseline
    plan: 01
    provides: AgentSession with FallbackAdapter LLM (OpenRouter + local llama_cpp)

provides:
  - AgentSession error event handler with verbal fallback via session.say()
  - Holding message spoken once per error episode (_holding_spoken flag)
  - Terminal error apology message
  - ERROR-level logging of all session errors with recoverable status and source

affects:
  - 01-infrastructure-baseline
  - 02-knowledge-layer

tech-stack:
  added: []
  patterns: [session.on('error') event handler pattern for AgentSession verbal fallback]

key-files:
  created: []
  modified:
    - livekit_agent/src/agent.py

key-decisions:
  - "Use session.on('error') decorator on AgentSession to subscribe to ErrorEvent"
  - "LLMError.recoverable field used to distinguish transient vs terminal errors; getattr with default True for non-LLM error types"
  - "Holding message spoken once per error episode via nonlocal _holding_spoken flag; reset on terminal error for next episode"
  - "Vague friendly messages only — no technical details exposed to user via speech"

patterns-established:
  - "Error handler: register with @session.on('error') before session.start(); use nonlocal flag to prevent repeated holding messages"

requirements-completed: [INFR-02]

duration: 5min
completed: 2026-02-23
---

# Phase 01 Plan 02: Verbal Error Fallback Summary

**AgentSession error handler speaks "Hang on a sec." once per transient error episode and "Sorry, I can't answer that right now." on terminal failure, with full ERROR-level logging**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-23T00:00:00Z
- **Completed:** 2026-02-23T00:05:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Inspected livekit-agents source to confirm ErrorEvent fields (error, source) and LLMError.recoverable field
- Registered on_session_error handler via @session.on("error") before session.start()
- Recoverable errors speak "Hang on a sec." only once per episode using _holding_spoken flag
- Unrecoverable errors speak "Sorry, I can't answer that right now." and reset flag for next episode
- All errors logged at ERROR level with recoverable status, source type, and full error object

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement verbal error fallback on session error events** - `cfacff0` (feat)

**Plan metadata:** (docs commit — to follow)

## Files Created/Modified
- `livekit_agent/src/agent.py` - Added error handler with _holding_spoken flag, session.on('error') registration, session.say() verbal notifications

## Decisions Made
- Used `getattr(error, "recoverable", True)` to safely handle any error type (not just LLMError/STTError/TTSError) — defaults to treating unknown errors as recoverable
- _holding_spoken flag is nonlocal to the my_agent() coroutine scope, bound per-session lifecycle
- Terminal (unrecoverable) errors reset the flag so a new error episode can speak the holding message again

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Agent now gives verbal feedback during LLM failures instead of going silent
- OpenRouter rate-limit errors (recoverable) will trigger "Hang on a sec." once; user stays in conversation
- Phase 2 (LightRAG knowledge layer) can proceed — error UX is in place

## Self-Check: PASSED
- livekit_agent/src/agent.py: FOUND
- 01-02-SUMMARY.md: FOUND
- commit cfacff0: FOUND

---
*Phase: 01-infrastructure-baseline*
*Completed: 2026-02-23*
