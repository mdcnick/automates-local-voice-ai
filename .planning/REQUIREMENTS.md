# Requirements: Local Voice AI Assistant

**Defined:** 2026-02-23
**Core Value:** A voice assistant that remembers things, integrates with your life, and sounds natural — running on your own infrastructure.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Infrastructure

- [x] **INFR-01**: Agent connects to OpenRouter API for LLM inference instead of local llama_cpp
- [x] **INFR-02**: Agent handles OpenRouter rate limits gracefully with verbal fallback on 429 errors
- [x] **INFR-03**: llama_cpp Docker service removed from docker-compose.yml
- [x] **INFR-04**: LLM model configurable via environment variable (default: Llama 3.3 70B free)

### Knowledge & Memory

- [ ] **KNOW-01**: Agent queries LightRAG on Coolify for relevant context each conversation turn
- [ ] **KNOW-02**: RAG lookup uses latency-optimized pattern (pre-emptive via on_user_turn_completed, not tool call round-trip)
- [ ] **KNOW-03**: User can say "Remember this..." to save knowledge to LightRAG
- [ ] **KNOW-04**: Agent confirms what was saved after voice-commanded knowledge saving
- [ ] **KNOW-05**: Cross-session recall works (information saved in one session retrievable in another)

### Calendar

- [ ] **CAL-01**: User can ask "What's on my calendar?" and get events read back via CalDAV
- [ ] **CAL-02**: User can create calendar events by voice ("Remind me to..." / "Schedule a meeting...")
- [ ] **CAL-03**: CalDAV works with any provider (Google, iCloud, Nextcloud) via standard protocol
- [ ] **CAL-04**: Calendar credentials configurable via environment variables

### Voice

- [ ] **VOIC-01**: User can select from Kokoro's built-in voice options
- [ ] **VOIC-02**: Voice selection persists within a session

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Infrastructure

- **INFR-05**: LiveKit Cloud migration (replace self-hosted LiveKit server)
- **INFR-06**: Hosted deployment model for non-self-hosting users

### Knowledge & Memory

- **KNOW-06**: Document upload via web UI for knowledge ingestion into LightRAG
- **KNOW-07**: Conversation history indexed into LightRAG for deeper cross-session recall

### Voice

- **VOIC-03**: Voice cloning support via F5-TTS or equivalent engine
- **VOIC-04**: More natural/expressive speech output beyond Kokoro defaults

### Users

- **USER-01**: Multi-user profiles with separate knowledge contexts
- **USER-02**: Self-hosting setup documentation and guide

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web search tool | Adds external API dependency, latency, hallucination risk; users should index curated sources into LightRAG instead |
| Smart home control | Entirely different domain; Home Assistant already solves this |
| Mobile native apps | Web-first approach; mobile is v2+ |
| Real-time transcription display | Adds UI complexity; creates anxiety with imperfect mid-sentence transcription |
| Persistent raw conversation storage | LightRAG indexes summaries; storing full transcripts causes context bloat |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 1 | Complete |
| INFR-03 | Phase 1 | Complete |
| INFR-04 | Phase 1 | Complete |
| KNOW-01 | Phase 2 | Pending |
| KNOW-02 | Phase 2 | Pending |
| KNOW-03 | Phase 2 | Pending |
| KNOW-04 | Phase 2 | Pending |
| KNOW-05 | Phase 2 | Pending |
| CAL-01 | Phase 3 | Pending |
| CAL-02 | Phase 3 | Pending |
| CAL-03 | Phase 3 | Pending |
| CAL-04 | Phase 3 | Pending |
| VOIC-01 | Phase 4 | Pending |
| VOIC-02 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 after roadmap creation*
