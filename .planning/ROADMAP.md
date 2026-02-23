# Roadmap: Local Voice AI Assistant

## Overview

This milestone extends an existing working voice AI (LiveKit + Nemotron STT + Kokoro TTS) with four new capabilities: cloud LLM routing via OpenRouter, persistent knowledge memory via LightRAG, calendar integration via CalDAV, and multi-voice TTS selection. Infrastructure changes come first to establish a stable, capable LLM foundation. Memory and calendar features layer on top. Voice selection ships last as polish once core functionality is proven.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Infrastructure Baseline** - Swap local llama.cpp for OpenRouter; establish cloud-connected agent with 70B LLM
- [ ] **Phase 2: LightRAG Knowledge** - Connect LightRAG on Coolify; agent retrieves and stores knowledge across sessions
- [ ] **Phase 3: Calendar Integration** - CalDAV integration for voice-driven calendar read and event creation
- [ ] **Phase 4: TTS Voice Selection** - Expose Kokoro built-in voices via UI; persist selection within session

## Phase Details

### Phase 1: Infrastructure Baseline
**Goal**: Agent runs on OpenRouter for LLM inference with local llama.cpp and its Docker service removed
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04
**Success Criteria** (what must be TRUE):
  1. User can have a conversation and the assistant responds using a 70B model via OpenRouter
  2. When OpenRouter rate limit is hit, the assistant speaks a verbal fallback instead of going silent
  3. The LLM model used is changeable via environment variable without code changes
  4. docker-compose.yml no longer contains a llama_cpp service; compose up starts cleanly without it
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — OpenRouter LLM wiring + Docker Compose migration
- [ ] 01-02-PLAN.md — Verbal error fallback for rate limits and failures

### Phase 2: LightRAG Knowledge
**Goal**: Agent queries and writes to LightRAG on Coolify so knowledge persists across conversations
**Depends on**: Phase 1
**Requirements**: KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05
**Success Criteria** (what must be TRUE):
  1. User can say "Remember that I prefer dark mode" and the agent confirms what was saved
  2. In a new conversation session, the agent recalls facts saved in a previous session
  3. RAG context is retrieved before the LLM responds (no tool-call round-trip delay noticeable to user)
  4. If LightRAG is unreachable, the agent continues responding without crashing or going silent
**Plans**: TBD

### Phase 3: Calendar Integration
**Goal**: User can ask about and create calendar events by voice using CalDAV with any major calendar provider
**Depends on**: Phase 2
**Requirements**: CAL-01, CAL-02, CAL-03, CAL-04
**Success Criteria** (what must be TRUE):
  1. User can ask "What's on my calendar today?" and hear upcoming events read back accurately
  2. User can say "Schedule a meeting with John on Friday at 2pm" and the event appears in their calendar
  3. CalDAV credentials are configured entirely via environment variables with no code changes per provider
  4. Integration works with at least Google Calendar, iCloud, and Nextcloud CalDAV endpoints
**Plans**: TBD

### Phase 4: TTS Voice Selection
**Goal**: User can choose from Kokoro's built-in voices and their selection persists through the session
**Depends on**: Phase 3
**Requirements**: VOIC-01, VOIC-02
**Success Criteria** (what must be TRUE):
  1. User can select a voice from a list of Kokoro built-in options in the browser UI
  2. After selecting a voice, all subsequent assistant speech uses that voice for the rest of the session
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Baseline | 1/2 | In Progress|  |
| 2. LightRAG Knowledge | 0/TBD | Not started | - |
| 3. Calendar Integration | 0/TBD | Not started | - |
| 4. TTS Voice Selection | 0/TBD | Not started | - |
