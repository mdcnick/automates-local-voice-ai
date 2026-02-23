---
phase: 01-infrastructure-baseline
plan: 01
subsystem: infra
tags: [openrouter, llama_cpp, docker-compose, livekit-agents, FallbackAdapter]

requires: []
provides:
  - OpenRouter as primary LLM provider in agent.py via with_openrouter()
  - LLM_MODEL env var for model selection with comma-separated fallback chain
  - FallbackAdapter wrapping OpenRouter + local llama_cpp as last resort
  - docker-compose.yml with llama_cpp behind local-llm profile
affects:
  - 01-infrastructure-baseline
  - 02-knowledge-layer
  - 03-calendar-integration

tech-stack:
  added: [openrouter (via livekit.plugins.openai with_openrouter), livekit.agents.llm.FallbackAdapter]
  patterns: [FallbackAdapter chain for LLM resilience, profile-gated heavy services in docker-compose]

key-files:
  created: []
  modified:
    - docker-compose.yml
    - livekit_agent/src/agent.py

key-decisions:
  - "OpenRouter is the primary LLM provider — cloud-based access to 70B+ models without local GPU"
  - "Local llama_cpp kept as emergency fallback via FallbackAdapter, accessible via --profile local-llm"
  - "LLM_MODEL env var supports comma-separated model chain for multi-hop fallback at runtime"

patterns-established:
  - "LLM selection: build_llm() factory reads LLM_MODEL env var, splits on comma for fallback chain"
  - "Docker Compose profiles: heavy optional services (llama_cpp) behind profiles to keep default stack lean"

requirements-completed: [INFR-01, INFR-03, INFR-04]

duration: 2min
completed: 2026-02-23
---

# Phase 01 Plan 01: LLM Migration to OpenRouter with FallbackAdapter Summary

**OpenRouter replaces local llama.cpp as primary LLM via with_openrouter() and FallbackAdapter, with llama_cpp profiled out of default docker compose up**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-23T23:56:07Z
- **Completed:** 2026-02-23T23:57:21Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- docker-compose.yml: llama_cpp service behind `local-llm` profile, removed from livekit_agent depends_on
- livekit_agent environment now receives OPENROUTER_API_KEY and LLM_MODEL
- agent.py: build_llm() factory constructs FallbackAdapter([openrouter_llm, local_llm]) with model chain from LLM_MODEL env var
- Old llama_model/llama_base_url/llama_api_key variables removed from my_agent()

## Task Commits

Each task was committed atomically:

1. **Task 1: Move llama_cpp to Docker Compose profile and update depends_on** - `f23b3d9` (feat)
2. **Task 2: Wire OpenRouter LLM with FallbackAdapter to local llama_cpp** - `92fd341` (feat)

**Plan metadata:** (docs commit — to follow)

## Files Created/Modified
- `docker-compose.yml` - llama_cpp behind local-llm profile; OPENROUTER_API_KEY and LLM_MODEL added to livekit_agent env
- `livekit_agent/src/agent.py` - build_llm() with OpenRouter + FallbackAdapter; old llama vars removed

## Decisions Made
- OpenRouter selected as primary LLM (cloud, 70B+ models, no local GPU required)
- FallbackAdapter keeps local llama_cpp as last resort for offline resilience
- LLM_MODEL supports comma-separated model chain: first model is primary, rest are OpenRouter fallback_models, local llama_cpp is always last

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unsorted ruff import block**
- **Found during:** Task 2 (Wire OpenRouter LLM)
- **Issue:** ruff I001 — import block not sorted (FallbackAdapter import position)
- **Fix:** Ran `ruff check --fix` and `ruff format` to auto-sort and reformat
- **Files modified:** livekit_agent/src/agent.py
- **Verification:** `ruff check` and `ruff format --check` both pass clean
- **Committed in:** 92fd341 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 lint/format)
**Impact on plan:** Trivial auto-fix, no scope change.

## Issues Encountered
None beyond the import ordering lint error above.

## User Setup Required
**External service requires manual configuration.**

Set `OPENROUTER_API_KEY` in your `.env.local` file:
- Get key at: https://openrouter.ai/keys
- Variable: `OPENROUTER_API_KEY=<your key>`

Without this key, OpenRouter calls will fail and the agent will fall back to local llama_cpp (if running via `--profile local-llm`).

## Next Phase Readiness
- Agent is ready to use OpenRouter once OPENROUTER_API_KEY is set in environment
- `docker compose up` starts cleanly without llama_cpp
- `docker compose --profile local-llm up` includes llama_cpp for offline/fallback use
- Phase 2 (LightRAG knowledge layer) can proceed — LLM infrastructure is stable

---
*Phase: 01-infrastructure-baseline*
*Completed: 2026-02-23*
