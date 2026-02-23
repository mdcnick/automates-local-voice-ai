# Feature Research

**Domain:** Local self-hosted voice AI assistant with RAG memory, calendar integration, and advanced TTS
**Researched:** 2026-02-23
**Confidence:** MEDIUM (WebSearch + LiveKit official docs verified; LightRAG/Kokoro voice cloning from multiple sources)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| LLM tool calling (function tools) | Agents that can DO things are the baseline expectation in 2026; a voice assistant that can only chat is a toy | MEDIUM | LiveKit `@function_tool()` decorator is the established pattern; already supported by SDK |
| Cross-session memory recall | Users tell the assistant something once and expect it to remember; forgetting is the #1 complaint with AI assistants | MEDIUM | LightRAG handles this; agent calls LightRAG query on each turn |
| Calendar read ("What's on my calendar today?") | Any "assistant" that can't check a schedule is not an assistant | MEDIUM | python-caldav library; async support available; must handle Google, iCloud, Nextcloud |
| Document upload for knowledge ingestion | Users expect to feed the assistant their own material (notes, PDFs, references) | MEDIUM | Web UI file upload → LightRAG insert; background processing required |
| Session memory (within a conversation) | Losing context mid-conversation is disorienting; users consider this broken | LOW | LiveKit session context + LLM context window; no persistence needed |
| Multiple TTS voice options | Users want to pick a voice they don't find annoying; single-voice = feels unfinished | LOW | Kokoro natively supports multiple voicepacks; `af_nova` is current default; voice list endpoint + UI picker |
| Sub-second or near-sub-second response latency | Sub-second latency is now table stakes in 2025/2026; anything over 2-3s feels broken | HIGH | Critical: RAG lookup and calendar queries must not add noticeable delay; use `on_user_turn_completed` hook for pre-emptive RAG |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Voice-commanded knowledge saving ("Remember this...") | Natural language capture of knowledge without UI friction — unique to voice-native workflows | MEDIUM | Intent detection + LightRAG insert; needs reliable trigger phrase recognition without false positives |
| Calendar event creation by voice | Few self-hostable assistants close the loop from "remind me" to actual calendar entry | MEDIUM | python-caldav write; requires iCalendar format generation; natural language date parsing needed |
| Fully local STT/TTS with cloud LLM | Privacy for audio + access to powerful models; unique combination vs pure cloud or pure local | HIGH (already built) | Already exists; this is the core architecture advantage |
| LightRAG graph-based retrieval | Better relationship understanding between facts vs flat vector search; recall of connected information is qualitatively better | HIGH (integration work) | LightRAG uses knowledge graph + vector hybrid; more powerful than naive embedding search |
| Self-hostable by others (Docker Compose) | Most voice AI assistants are SaaS-only; self-hosting is a real differentiator for privacy-conscious users | MEDIUM | Docker Compose orchestration already exists; needs env var documentation and setup guide |
| Hybrid retrieval mode (RAG via tool call vs pre-emptive) | Pre-emptive RAG on every turn is wasteful; tool-call RAG adds a round-trip; hybrid adapts based on query type | HIGH | LiveKit supports both patterns; `on_user_turn_completed` for pre-emptive, `@function_tool` for explicit lookup |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| True voice cloning from audio sample | "Use my voice" sounds compelling; users want personalization | Kokoro does NOT support native voice cloning from audio input; community workarounds (kvoicewalk) are low quality and unstable; adds significant complexity and inference cost for marginal benefit | Offer Kokoro's built-in voice blending and multi-voicepack selection instead; label voices with descriptive names |
| Web search tool | Users want the assistant to "look things up" | Adds external API dependency, latency, and hallucination risk from retrieved web content; scope creep away from personal knowledge focus | Explicitly out of scope per PROJECT.md; recommend users index curated sources into LightRAG instead |
| Multi-user profiles with separate voice recognition | Seems logical for household use | Voice diarization/speaker identification is a hard ML problem; separate auth/profile state for voice is complex; rate limits on free LLM tier make multi-user impractical | Single-user focus for v1; multi-user is a v2+ architectural decision |
| Persistent conversation history in agent | Users want to reference "what we talked about last week" | Storing full conversation transcripts in agent state is expensive and causes context bloat; LightRAG already handles long-term recall via indexed summaries | Use LightRAG to index conversation summaries, not raw transcripts; keep agent stateless per PROJECT.md |
| Smart home control (lights, locks, etc.) | Natural extension of "assistant" concept | Requires device-specific integrations, auth flows per vendor, safety considerations; entirely different domain from knowledge/calendar | Explicitly out of scope per PROJECT.md; Home Assistant already solves this separately |
| Real-time transcription display | Users want to see what the assistant heard | Adds UI complexity; creates anxiety when transcription is imperfect mid-sentence; does not improve assistant quality | Show transcription only for completed turns (post-VAD); do not show streaming partial transcripts |

## Feature Dependencies

```
[Session memory]
    └──required by──> [Cross-session memory recall]
                          └──requires──> [LightRAG integration]
                                             └──requires──> [OpenRouter LLM via function tools]

[Document upload]
    └──feeds into──> [LightRAG integration]

[Voice-commanded knowledge saving]
    └──requires──> [LightRAG integration]
    └──requires──> [Intent detection in LLM tool layer]

[Calendar read]
    └──requires──> [CalDAV client (python-caldav)]
    └──requires──> [LLM function tool: get_calendar_events]

[Calendar event creation]
    └──requires──> [Calendar read] (same CalDAV setup)
    └──requires──> [Natural language date/time parsing]

[Multiple TTS voices]
    └──independent──> (Kokoro already supports voicepacks; UI selection only)

[Voice cloning] ──conflicts with──> [Multiple TTS voices]
    (Kokoro cannot do both; adding alternative TTS engine breaks existing pipeline)

[Pre-emptive RAG (on_user_turn_completed)]
    └──enhances──> [Response latency]
    └──competes with──> [Tool-call RAG] (choose one pattern per query type)
```

### Dependency Notes

- **LightRAG integration is the foundation**: Document upload, voice-commanded saving, and cross-session recall all depend on LightRAG being operational and network-accessible from the agent container.
- **Calendar read must precede calendar write**: CalDAV setup, auth, and error handling need to be proven for reads before writes add complexity.
- **RAG latency must be solved before enabling**: If LightRAG lookup adds >500ms, it degrades the core voice experience. Use LiveKit's `on_user_turn_completed` hook for pre-emptive RAG to hide latency rather than adding tool-call round-trips.
- **Voice cloning conflicts with existing TTS pipeline**: Kokoro cannot clone voices from audio samples natively. Any voice cloning would require replacing or augmenting Kokoro with a different engine (F5-TTS, Chatterbox), which risks breaking existing TTS behavior. Defer until multi-voice selection is validated.

## MVP Definition

### Launch With (v1 — this milestone)

Minimum viable product for the features milestone — what makes the assistant genuinely useful beyond basic conversation.

- [ ] **LightRAG integration** — Foundation for all memory and knowledge features; without it the assistant forgets everything
- [ ] **Cross-session memory recall** — The single most important difference from a chatbot; users must feel the assistant "knows them"
- [ ] **Document upload via web UI** — Users need a way to seed the knowledge base; voice alone is too slow for bulk knowledge
- [ ] **Voice-commanded knowledge saving** — The natural voice-first interaction for capturing new information on the fly
- [ ] **Calendar read via CalDAV** — "What's on my schedule?" is the most common assistant use case; validates tool calling pattern
- [ ] **OpenRouter LLM + function tool wiring** — Required infrastructure for all tool-use features; replaces local llama_cpp

### Add After Validation (v1.x)

Features to add once core is working and RAG latency is measured.

- [ ] **Calendar event creation by voice** — After read is proven, write is a natural next step; needs date parsing validation
- [ ] **Multiple TTS voice picker** — Quality of life improvement; Kokoro voicepacks are already available; low-effort UI addition
- [ ] **LiveKit Cloud migration** — Reliability improvement; can be done independently of feature work

### Future Consideration (v2+)

Features to defer until v1 is validated.

- [ ] **Voice cloning** — Requires significant TTS engine research and likely replacing Kokoro; defer until multi-voice selection proves insufficient
- [ ] **Multi-user profiles** — Architectural change; rate limits and auth complexity make this a v2 concern
- [ ] **Hosted deployment model** — Infrastructure and billing complexity; validate self-host model first

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| OpenRouter LLM + function tool wiring | HIGH | MEDIUM | P1 |
| LightRAG integration | HIGH | HIGH | P1 |
| Cross-session memory recall | HIGH | MEDIUM | P1 |
| Document upload via web UI | HIGH | MEDIUM | P1 |
| Calendar read via CalDAV | HIGH | MEDIUM | P1 |
| Voice-commanded knowledge saving | HIGH | MEDIUM | P1 |
| RAG latency optimization | HIGH | MEDIUM | P1 — must solve before shipping |
| Calendar event creation | MEDIUM | MEDIUM | P2 |
| Multiple TTS voice options | MEDIUM | LOW | P2 |
| LiveKit Cloud migration | LOW (infra) | LOW | P2 |
| Voice cloning | MEDIUM | HIGH | P3 |
| Multi-user profiles | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for this milestone launch
- P2: Should have, add when P1 features are validated
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Siri/Google Assistant | ChatGPT Voice | Our Approach |
|---------|----------------------|---------------|--------------|
| Memory across sessions | Limited/inconsistent | Opt-in memory feature | LightRAG graph-based; always-on |
| Calendar access | Native OS integration | None / tool plugin | CalDAV (provider-agnostic) |
| Document knowledge base | None | ChatGPT file uploads (cloud) | LightRAG on self-hosted infra |
| Voice-commanded saving | None | None | @function_tool intent detection |
| Privacy (audio) | Cloud processed | Cloud processed | STT/TTS local; only LLM is cloud |
| Self-hosting | Not possible | Not possible | Full Docker Compose self-host |
| Voice selection | Limited | Not exposed | Kokoro voicepack picker |
| Voice cloning | Not available | Not available | Not in v1; evaluate post-launch |

## Sources

- [LiveKit tool definition docs](https://docs.livekit.io/agents/build/tools/) — HIGH confidence (official docs)
- [LiveKit external data and RAG docs](https://docs.livekit.io/agents/build/external-data/) — HIGH confidence (official docs)
- [LiveKit RAG delay handling recipe](https://docs.livekit.io/recipes/rag-delay/) — HIGH confidence (official docs)
- [LightRAG GitHub (HKUDS/LightRAG)](https://github.com/HKUDS/LightRAG) — HIGH confidence (official repo)
- [python-caldav PyPI](https://pypi.org/project/caldav/) — HIGH confidence (official)
- [Kokoro TTS Hugging Face](https://huggingface.co/spaces/hexgrad/Kokoro-TTS) — MEDIUM confidence
- [KVoiceWalk (voice cloning workaround)](https://github.com/RobViren/kvoicewalk) — MEDIUM confidence (community project; quality unverified)
- [AssemblyAI voice AI stack 2026](https://www.assemblyai.com/blog/the-voice-ai-stack-for-building-agents) — MEDIUM confidence
- [ElevenLabs RAG engineering (50% faster)](https://elevenlabs.io/blog/engineering-rag) — MEDIUM confidence
- [Voice AI agents 2026 practical guide](https://vatsalshah.in/blog/voice-ai-agents-2026-guide) — LOW confidence (single blog source)

---
*Feature research for: Local self-hosted voice AI assistant*
*Researched: 2026-02-23*
