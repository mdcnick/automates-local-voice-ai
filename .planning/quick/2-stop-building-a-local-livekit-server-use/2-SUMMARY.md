---
phase: quick
plan: 2
subsystem: infrastructure
tags: [livekit, docker-compose, cloud-migration]
key-files:
  modified:
    - docker-compose.yml
    - .env
decisions:
  - "Switched LiveKit from self-hosted (livekit/livekit-server) to LiveKit Cloud — user must supply wss:// URL and API credentials"
metrics:
  duration: ~5min
  completed: 2026-02-24
  tasks_completed: 2
  files_modified: 2
---

# Quick Task 2: Stop Building a Local LiveKit Server, Use LiveKit Cloud Summary

**One-liner:** Removed self-hosted livekit/livekit-server container from docker-compose; agent and frontend now connect to LiveKit Cloud via empty env var placeholders.

## What Was Done

Removed the local LiveKit server container from the docker-compose stack and replaced all hardcoded local connection defaults (ws://livekit:7880, devkey, secret) with empty env var references, forcing users to supply real LiveKit Cloud credentials.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Remove local LiveKit service, update livekit_agent and frontend env vars | c4810dd |
| 2 | Update .env with empty LiveKit Cloud credential placeholders | 934fb87 |

## Changes Made

### docker-compose.yml
- Removed `livekit` service block (image: livekit/livekit-server:latest, ports 7880/7881, --dev command)
- `livekit_agent`: removed `depends_on.livekit`, changed env var defaults from `ws://livekit:7880`/`devkey`/`secret` to empty `${VAR}`
- `frontend`: removed `depends_on.livekit`, replaced hardcoded `ws://localhost:7880`/`devkey`/`secret` with `${VAR}` references

### .env
- `LIVEKIT_URL` — cleared (was `http://livekit:7880`)
- `LIVEKIT_API_KEY` — cleared (was `devkey`)
- `LIVEKIT_API_SECRET` — cleared (was `secret`)
- `NEXT_PUBLIC_LIVEKIT_URL` — cleared (was `http://localhost:7880`)
- `DEEPGRAM_API_KEY` — cleared (was hardcoded key)
- Added comment: `# LiveKit Cloud credentials (get from https://cloud.livekit.io -> Settings -> Keys)`

## User Setup Required

To run after this change, the user must:
1. Sign up or log in at https://cloud.livekit.io
2. Go to Settings -> Keys -> Create new key
3. Fill in `.env`:
   ```
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=APIxxxxxxxx
   LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxx
   NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
   ```

## Deviations from Plan

None — plan executed exactly as written. The `livekit/Dockerfile` referenced in the plan did not exist in the repo (no local directory), so no file deletion was needed.

## Self-Check: PASSED

- docker-compose.yml: no `livekit/livekit-server` image, no `livekit:7880` references
- .env: `LIVEKIT_URL=` is an empty placeholder
- Commits c4810dd and 934fb87 exist in git log
