# Architecture

**Analysis Date:** 2026-02-23

## Pattern Overview

**Overall:** Layered microservices with clear separation between frontend UI, realtime communication layer, and local AI inference pipeline.

**Key Characteristics:**
- Service-oriented architecture with Docker Compose orchestration
- Bidirectional WebRTC communication via LiveKit for low-latency audio streaming
- Modular AI inference pipeline: STT → LLM → TTS
- Frontend decoupled from agent (browser connects directly to LiveKit)
- All local inference services exposed via OpenAI-compatible APIs

## Layers

**Presentation Layer (Frontend):**
- Purpose: Browser-based UI for voice interaction with the agent
- Location: `frontend/` (Next.js + React)
- Contains: Next.js pages, components, hooks, configuration
- Depends on: LiveKit client SDK, application config
- Used by: Web browsers accessing the agent interface

**Communication Layer (LiveKit):**
- Purpose: WebRTC signaling server and media relay for real-time audio
- Location: `livekit/` (Docker service in compose)
- Contains: LiveKit server configuration
- Depends on: Nothing (standalone service)
- Used by: Frontend browser and livekit_agent service

**Agent Layer (Voice AI Agent):**
- Purpose: Orchestrates conversation flow and integrates inference services
- Location: `livekit_agent/src/agent.py`
- Contains: Agent class, session management, tool definitions
- Depends on: LiveKit Agents SDK, OpenAI-compatible plugin clients
- Used by: LiveKit to spawn sessions when users connect

**Inference Layer (Local Models):**
- Purpose: Speech processing and language understanding
- Location: `inference/` with subdirectories for each service
- Contains: STT (Nemotron/Whisper), LLM (llama.cpp), TTS (Kokoro), VAD (Silero)
- Depends on: PyTorch, HuggingFace transformers, model weights
- Used by: Agent service via OpenAI-compatible HTTP APIs

**API Integration Layer:**
- Purpose: Token generation and connection coordination
- Location: `frontend/app/api/connection-details/route.ts`
- Contains: JWT token generation, room creation logic
- Depends on: LiveKit server SDK for Node.js
- Used by: Frontend to bootstrap session

## Data Flow

**Session Initialization:**

1. User opens frontend in browser
2. Frontend calls `/api/connection-details` POST endpoint
3. Backend generates JWT token and room name, returns serverUrl + token
4. Frontend connects WebRTC to LiveKit using returned credentials
5. LiveKit signals to agent that new session started

**Voice Interaction Flow:**

1. User speaks into microphone → browser sends audio via WebRTC to LiveKit
2. LiveKit relays audio to livekit_agent service
3. Agent passes audio to Nemotron STT service (HTTP POST to `/v1/audio/transcriptions`)
4. STT returns transcript text
5. Agent passes transcript to llama.cpp LLM service (HTTP POST to `/v1/chat/completions`)
6. LLM returns response text
7. Agent passes response to Kokoro TTS service (HTTP POST to `/v1/audio/speech`)
8. TTS returns audio bytes
9. Agent sends audio back to LiveKit via WebRTC
10. LiveKit sends audio to browser → user hears response

**State Management:**

- Session state: Maintained in LiveKit room, not persisted
- Conversation context: Held in Agent memory during active session
- Configuration: Loaded at agent startup from environment variables and passed through app config
- Model weights: Cached on disk in `inference/*/models` directories, mounted as Docker volumes

## Key Abstractions

**Agent (Assistant class):**
- Purpose: Customizable voice assistant with tool support
- Examples: `livekit_agent/src/agent.py` defines `Assistant` class extending LiveKit `Agent`
- Pattern: Inherits from base Agent, defines system instructions, registers tools with `@function_tool()` decorator

**AgentSession:**
- Purpose: Manages STT/LLM/TTS pipeline for a single user conversation
- Pattern: Configured with pre-instantiated STT, LLM, TTS clients in `agent.py` lines 83-106
- Handles: Audio processing, turn detection, preemptive generation

**SessionProvider (Frontend):**
- Purpose: React context wrapper providing LiveKit session state to components
- Pattern: Wraps entire app in `App.tsx` to enable `useSessionContext()` hook access
- Scope: Global session state, audio tracks, participant info

**TokenSource:**
- Purpose: Abstracts token acquisition for different deployment models
- Pattern: Can be custom endpoint (sandbox), or API route (self-hosted)
- Implementation: `lib/utils.ts` defines `getSandboxTokenSource()` for configured deployments

## Entry Points

**Frontend:**
- Location: `frontend/app/layout.tsx` (root layout)
- Triggers: Browser navigation to http://localhost:3000
- Responsibilities: Sets up theme provider, global styles, server-side config loading

**Frontend App:**
- Location: `frontend/app/(app)/page.tsx` → `components/app/app.tsx`
- Triggers: After root layout renders
- Responsibilities: Initializes LiveKit session, provides token source, renders UI

**Agent:**
- Location: `livekit_agent/src/agent.py` lines 48-116
- Triggers: LiveKit detects new room + agent request
- Responsibilities: Loads models (VAD, STT config), creates session, starts listening

**API Connection Endpoint:**
- Location: `frontend/app/api/connection-details/route.ts`
- Triggers: Frontend POST request during session initialization
- Responsibilities: Generates JWT token, creates room name, validates credentials

## Error Handling

**Strategy:** Layered error containment with user-facing notifications

**Patterns:**

- **Frontend errors**: Caught in `useAgentErrors()` hook in `frontend/hooks/useAgentErrors.tsx`. When agent state becomes `'failed'`, displays toast with failure reasons
- **STT/LLM/TTS errors**: Raised as exceptions in agent, propagated to user via error toast. HTTP errors logged to stderr
- **Connection errors**: Handled by LiveKit SDK; caught in frontend with fallback error display and session termination
- **Token generation errors**: Caught in `/api/connection-details` route, returns 500 with error message

## Cross-Cutting Concerns

**Logging:**
- Agent: Uses Python `logging` module with formatted context fields (room name)
- Frontend: Console logging for development, errors logged to browser DevTools
- Inference services: Python loggers with INFO level, stdout/stderr captured by Docker

**Validation:**
- Frontend: Environment variables validated in `lib/utils.ts` (LIVEKIT_URL, API_KEY, API_SECRET required)
- Agent: Config environment variables checked at startup in `agent.py` lines 61-81
- API: Connection details route validates required env vars and request body

**Authentication:**
- Token-based: Frontend sends JWT to LiveKit, generated server-side with LiveKit SDK
- Inference services: Mostly local (no auth), optional OpenAI-compatible API key support in STT/LLM clients
- LiveKit API: Protected with API_KEY and API_SECRET in token generation

---

*Architecture analysis: 2026-02-23*
