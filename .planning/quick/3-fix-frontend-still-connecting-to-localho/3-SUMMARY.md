---
phase: quick-3
plan: 01
subsystem: frontend
tags: [livekit, docker, env, cloud-migration]
key-files:
  modified:
    - frontend/Dockerfile
    - frontend/.env.example
    - livekit_agent/.env.example
decisions:
  - Use ARG+ENV pattern in Dockerfile build stage so NEXT_PUBLIC_LIVEKIT_URL is baked in from docker-compose at build time, not hardcoded
  - Runner stage inherits env from docker-compose at runtime, no Dockerfile defaults needed
metrics:
  duration: 3min
  completed: 2026-02-23
  tasks: 2
  files: 3
---

# Quick Task 3: Fix Frontend Still Connecting to Localhost - Summary

**One-liner:** Removed all hardcoded localhost:7880/devkey/secret values from frontend Dockerfile and .env.example files; Dockerfile now uses ARG/ENV build args so NEXT_PUBLIC_LIVEKIT_URL bakes in from docker-compose at build time.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix frontend Dockerfile to use build args | a704b0a | frontend/Dockerfile |
| 2 | Update .env.example files with cloud placeholders | 848bdc6 | frontend/.env.example, livekit_agent/.env.example |

## What Was Done

**Task 1 - Dockerfile:** The build stage previously hardcoded `LIVEKIT_URL=http://livekit:7880`, `LIVEKIT_API_KEY=devkey`, `LIVEKIT_API_SECRET=secret`, and `NEXT_PUBLIC_LIVEKIT_URL=http://localhost:7880`. These were replaced with `ARG` declarations followed by `ENV` assignments so docker-compose can pass the real LiveKit Cloud values at build time. The runner stage had its entire hardcoded LiveKit ENV block removed — it now inherits values from the docker-compose `environment:` block at runtime.

**Task 2 - .env.example files:** Both `frontend/.env.example` and `livekit_agent/.env.example` previously showed localhost/devkey/secret as example values, which was misleading. They now show `wss://your-project.livekit.cloud` as the URL pattern and empty API key/secret fields.

## Verification

- `grep -rn "localhost:7880\|livekit:7880" frontend/ livekit_agent/.env.example` — no matches
- `grep -rn "devkey" frontend/ livekit_agent/.env.example` — no matches
- `frontend/Dockerfile` has `ARG NEXT_PUBLIC_LIVEKIT_URL` in build stage
- Both `.env.example` files contain `wss://`

## Deviations from Plan

None - plan executed exactly as written.
