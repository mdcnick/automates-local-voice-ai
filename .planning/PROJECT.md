# Local Voice AI Assistant

## What This Is

A self-hostable voice AI assistant you talk to in your browser. It listens, thinks, and speaks back — using a hybrid local/cloud architecture. STT and TTS run locally for privacy and speed, while the LLM runs via OpenRouter for access to powerful models without expensive local GPU requirements. Long-term memory and knowledge retrieval are powered by LightRAG on Coolify. Designed to be self-hosted by others or run as a hosted service.

## Core Value

A voice assistant that actually remembers things, integrates with your life (calendar, notes), and sounds natural — running on your own infrastructure with minimal cloud dependency.

## Requirements

### Validated

- ✓ Browser-based voice UI with real-time audio streaming — existing
- ✓ WebRTC communication via LiveKit — existing
- ✓ Local STT via Nemotron with Whisper fallback — existing
- ✓ Local TTS via Kokoro — existing
- ✓ Voice Activity Detection via Silero — existing
- ✓ Docker Compose orchestration — existing
- ✓ Turn detection (multilingual) — existing

### Active

- [ ] LLM via OpenRouter (Llama 3.3 70B free tier, swappable models)
- [ ] LiveKit Cloud integration (replace self-hosted LiveKit server)
- [ ] Remove local llama_cpp Docker service
- [ ] Remove local LiveKit server Docker service
- [ ] LightRAG integration on Coolify for long-term knowledge retrieval
- [ ] Index personal notes and documents into LightRAG
- [ ] Index conversation history into LightRAG for cross-session recall
- [ ] Index domain-specific reference material into LightRAG
- [ ] Document upload via web UI for knowledge ingestion
- [ ] Voice-commanded knowledge saving ("Remember this...", "Save this note about...")
- [ ] Calendar integration via CalDAV (read events, create reminders)
- [ ] Session memory (context maintained within a conversation)
- [ ] Multiple TTS voice options users can select from
- [ ] More natural/expressive speech output
- [ ] Voice cloning support (custom voices)
- [ ] Self-hostable by others (clear setup, documented config)
- [ ] Potential hosted deployment model

### Out of Scope

- Local LLM inference — replaced by OpenRouter for cost and quality reasons
- Self-hosted LiveKit server — replaced by LiveKit Cloud for reliability
- Smart home control — not in v1, could add later
- Web search tool — not in v1, could add later
- Multi-user profiles with separate voice recognition — complexity too high for v1
- Mobile native apps — web-first approach

## Context

This is a brownfield project built on the LiveKit Agents Python SDK with a Next.js frontend. The existing architecture uses a modular pipeline (STT → LLM → TTS) with OpenAI-compatible API interfaces between services, making it straightforward to swap providers. The agent runs in Docker with services communicating over an internal network.

LightRAG will run as a separate service on Coolify (self-hosted PaaS), accessed by the agent over HTTP. This keeps the knowledge/retrieval layer decoupled from the voice pipeline.

The LiveKit Agents SDK supports function tools (decorated with `@function_tool()`), which is the mechanism for adding calendar access, RAG queries, and knowledge saving as callable tools the LLM can invoke during conversation.

Kokoro TTS already supports multiple voices (currently using `af_nova`). Voice cloning would require evaluating Kokoro's capabilities or adding an alternative TTS engine.

## Constraints

- **LLM Cost**: Using OpenRouter free tier (rate-limited: ~20 req/min, 200/day). May need paid tier for production/multi-user use at ~$0.10-0.30/M tokens.
- **STT/TTS Local**: Must run on user's hardware — need reasonable CPU/GPU requirements documented.
- **LightRAG Hosting**: Runs on Coolify, needs network accessibility from the agent container.
- **CalDAV**: Generic protocol — must work with Google Calendar, iCloud, Nextcloud, etc. without provider-specific code.
- **Self-hosting**: Setup must be reproducible via Docker Compose with clear env configuration.
- **Latency**: Voice AI is latency-sensitive. RAG lookups and calendar queries must not noticeably delay responses.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| OpenRouter for LLM | Access to 70B+ models without local GPU, pennies per conversation | — Pending |
| LiveKit Cloud over self-hosted | More reliable, less infra to maintain | — Pending |
| Keep STT/TTS local | Privacy for audio data, no per-request cost for speech | — Pending |
| LightRAG on Coolify | Decoupled knowledge layer, already have Coolify infra | — Pending |
| CalDAV for calendar | Provider-agnostic, works with most calendar services | — Pending |
| Session memory only (no persistent conversation state in agent) | LightRAG handles long-term recall, keeps agent stateless | — Pending |

---
*Last updated: 2026-02-23 after initialization*
