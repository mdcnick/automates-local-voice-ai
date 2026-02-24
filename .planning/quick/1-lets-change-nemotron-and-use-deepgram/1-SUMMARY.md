---
phase: quick
plan: 1
subsystem: livekit_agent/stt
tags: [stt, deepgram, nemotron, docker-compose]
dependency_graph:
  requires: []
  provides: [deepgram-stt-integration]
  affects: [livekit_agent, docker-compose]
tech_stack:
  added: [livekit-plugins-deepgram~=1.3]
  patterns: [cloud-stt-via-livekit-plugin]
key_files:
  created: []
  modified:
    - livekit_agent/src/agent.py
    - livekit_agent/pyproject.toml
    - livekit_agent/uv.lock
    - docker-compose.yml
    - .env
    - livekit_agent/.env.example
decisions:
  - Deepgram nova-3 as default STT model — low latency, high accuracy, no local GPU needed
  - Nemotron kept as optional profile (--profile nemotron) rather than removed entirely
metrics:
  duration: 91s
  completed: 2026-02-23
  tasks_completed: 2
  files_modified: 6
---

# Quick Task 1: Replace Nemotron STT with Deepgram cloud STT

**One-liner:** Swapped local Nemotron speech-to-text for Deepgram cloud STT using livekit-plugins-deepgram with nova-3 model.

## What Was Done

### Task 1: Add Deepgram plugin and wire STT in agent

Added `livekit-plugins-deepgram~=1.3` to `pyproject.toml` dependencies and ran `uv sync` to install. In `agent.py`, imported `deepgram` from `livekit.plugins` and replaced the entire `STT_PROVIDER`/nemotron-branching block with a clean `deepgram.STT()` call reading `DEEPGRAM_STT_MODEL` and `DEEPGRAM_LANGUAGE` from env. Ruff lint passes cleanly.

**Commit:** 33e42ee

### Task 2: Update Docker Compose and env files for Deepgram

Added `profiles: ["nemotron"]` to the nemotron service so it no longer starts by default. Removed `nemotron` from `livekit_agent.depends_on`. Added `DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY:-}` to `livekit_agent` environment block. Replaced `STT_PROVIDER`/`STT_*`/`NEMOTRON_*` vars in `.env` with `DEEPGRAM_API_KEY=` and `DEEPGRAM_STT_MODEL=nova-3`. Updated `.env.example` to show Deepgram vars.

**Commit:** 63b1f56

## Verification

- `uv run python -c "from livekit.plugins import deepgram; print('deepgram plugin OK')"` — passes
- `docker compose config --services` lists: livekit, frontend, kokoro, livekit_agent (no nemotron) — passes
- `uv run ruff check src/` — all checks passed
- `agent.py` uses `deepgram.STT()`, no nemotron references remain

## Deviations from Plan

None — plan executed exactly as written.

## Next Steps for User

Set `DEEPGRAM_API_KEY` in `.env.local` (or the production secrets store) before starting the stack. Get an API key from https://console.deepgram.com.

To run Nemotron locally if needed: `docker compose --profile nemotron up`

## Self-Check: PASSED

- livekit_agent/src/agent.py — modified, uses deepgram.STT
- livekit_agent/pyproject.toml — modified, contains livekit-plugins-deepgram
- docker-compose.yml — modified, nemotron has profiles: [nemotron]
- .env — modified, DEEPGRAM_API_KEY present
- livekit_agent/.env.example — modified, Deepgram vars present
- Commit 33e42ee — FOUND
- Commit 63b1f56 — FOUND
