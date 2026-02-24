# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** A voice assistant that remembers things, integrates with your life, and sounds natural — running on your own infrastructure.
**Current focus:** Phase 1 — Infrastructure Baseline

## Current Position

Phase: 1 of 4 (Infrastructure Baseline)
Plan: 2 of TBD in current phase
Status: In progress
Last activity: 2026-02-24 - Completed quick task 2: stop building a local livekit server, use livekit cloud instead

Progress: [█░░░░░░░░░] 10%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-infrastructure-baseline P01 | 2min | 2 tasks | 2 files |
| Phase 01-infrastructure-baseline P02 | 5min | 1 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- OpenRouter for LLM: access to 70B+ models without local GPU — CONFIRMED (01-01)
- LiveKit Cloud over self-hosted: more reliable, less infra — deferred to v2
- LightRAG on Coolify: decoupled knowledge layer — pending confirmation
- [Phase 01-infrastructure-baseline]: session.on('error') pattern for AgentSession verbal fallback — speaks once on recoverable errors, apology on terminal failures

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: LightRAG HTTP API schema needs validation against a live instance before writing client code (exact response field names unconfirmed)
- Phase 3: Google CalDAV requires OAuth 2.0 (not Basic Auth as of March 2025) — pluggable auth strategy needed upfront
- Phase 1: OpenRouter free tier (200 req/day) will be exhausted quickly with more than one concurrent tester — decide on paid tier before Phase 2

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | lets change nemotron and use deepgram | 2026-02-24 | 7ead9d3 | [1-lets-change-nemotron-and-use-deepgram](./quick/1-lets-change-nemotron-and-use-deepgram/) |
| 2 | stop building a local livekit server, use cloud | 2026-02-24 | 934fb87 | [2-stop-building-a-local-livekit-server-use](./quick/2-stop-building-a-local-livekit-server-use/) |
| 3 | fix frontend still connecting to localhost | 2026-02-23 | 848bdc6 | [3-fix-frontend-still-connecting-to-localho](./quick/3-fix-frontend-still-connecting-to-localho/) |

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed quick-2 (LiveKit Cloud migration)
Resume file: None
