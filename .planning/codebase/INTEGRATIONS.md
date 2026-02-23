# External Integrations

**Analysis Date:** 2026-02-23

## APIs & External Services

**LLM Services:**
- OpenAI API - Optional LLM provider (OpenAI GPT models)
  - SDK/Client: `livekit.plugins.openai`
  - Auth: `OPENAI_API_KEY` environment variable
  - Local Alternative: Llama.cpp server with Hugging Face models (Qwen, etc.)

**STT Services:**
- NVIDIA Nemotron (Default) - Speech-to-text streaming model
  - SDK/Client: OpenAI-compatible API wrapper in `inference/nemotron/server.py`
  - Auth: `STT_API_KEY` (no key needed for local deployment)
  - Base URL: `http://nemotron:8000/v1` (Docker) or `http://localhost:11435/v1` (local dev)
  - Model: `nvidia/nemotron-speech-streaming-en-0.6b`

- Whisper (Fallback) - OpenAI Whisper STT model
  - SDK/Client: Faster-whisper optimization wrapper
  - Auth: None (local deployment)
  - Base URL: `http://whisper:80/v1` (Docker) or `http://localhost:11437/v1`
  - Model: `Systran/faster-whisper-small`
  - Trigger: Via `STT_PROVIDER=whisper` environment variable

**TTS Services:**
- Kokoro - Local text-to-speech synthesis
  - SDK/Client: OpenAI-compatible API (kokoro-fastapi)
  - Auth: `api_key="no-key-needed"` for local deployment
  - Base URL: `http://kokoro:8880/v1`
  - Model: `kokoro` with voice `af_nova`
  - Image (CPU): `ghcr.io/remsky/kokoro-fastapi-cpu:latest`
  - Image (GPU): `ghcr.io/remsky/kokoro-fastapi-gpu:latest`

**Voice Activity & Turn Detection:**
- Silero VAD - Voice activity detection
  - Integration: `livekit.plugins.silero`
  - Loaded in `livekit_agent/src/agent.py` via `prewarm()` function
  - Models downloaded on first run with `uv run python src/agent.py download-files`

- LiveKit Turn Detector (Multilingual) - Speaker turn detection
  - Integration: `livekit.plugins.turn_detector.multilingual.MultilingualModel`
  - Usage: `livekit_agent/src/agent.py` line 103

**Noise Cancellation:**
- LiveKit Cloud Noise Cancellation
  - Plugin: `livekit-plugins-noise-cancellation 0.2`
  - Deployment: Available in LiveKit Cloud (requires LiveKit Cloud subscription)
  - Self-hosted: Requires plugin architecture (see LiveKit docs)

## Data Storage

**Databases:**
- Not used - Stateless agent design (state managed by LiveKit room)

**File Storage:**
- Hugging Face Model Hub - Model downloads and caching
  - Location: `/root/.cache/huggingface` in containers, `/models` for llama.cpp
  - Models downloaded on first run or pre-downloaded to volumes
  - Environment variables: `HF_HOME`, `XDG_CACHE_HOME`

**Caching:**
- Docker volumes for model caching:
  - `nemotron-cache:/root/.cache/huggingface` - Nemotron model cache
  - `whisper-data:/data` - Whisper model cache
  - `./inference/llama/models:/models` - Llama.cpp model mount

## Authentication & Identity

**Auth Provider:**
- Custom JWT-based (LiveKit native)
  - Implementation: `livekit-server-sdk` for token generation
  - Token generator: `frontend/app/api/connection-details/route.ts`
  - Token format: Access tokens with video grants and optional agent configuration
  - Token TTL: 15 minutes
  - Uses: `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

**Room Access:**
- LiveKit room-based access control
  - Room creation: On-demand per session (`voice_assistant_room_{random}`)
  - Participant identity: `voice_assistant_user_{random}`
  - Agent assignment: Via `RoomConfiguration` in token claims

## Monitoring & Observability

**Error Tracking:**
- Not detected

**Logs:**
- Console/stdout logging via Python logging module
  - Frontend: Browser console logs
  - Backend: Docker container logs accessible via `docker-compose logs`
  - Agent: Configured logger in `livekit_agent/src/agent.py`
  - Inference services: FastAPI server logs (Nemotron, Whisper)

**Health Checks:**
- LiveKit Server: Health check via HTTP GET `/` (port 7880)
- Nemotron STT: `curl -fsS http://localhost:8000/health | grep -q '"model_loaded":true'`
  - Interval: 10s, Timeout: 5s, Retries: 120, Start period: 20s
- Llama.cpp LLM: `curl -fsS http://localhost:11434/v1/models`
  - Interval: 10s, Timeout: 5s, Retries: 30
- LiveKit Agent: `curl -fsS http://localhost:8081/`
  - Interval: 5s, Timeout: 3s, Retries: 5, Start period: 10s

## CI/CD & Deployment

**Hosting:**
- Docker/Docker Compose (local and self-hosted)
- Supports deployment to Kubernetes via containerized services
- Optional: LiveKit Cloud (Sandbox API for configuration)

**CI Pipeline:**
- GitHub Actions workflow (`.github/workflows/`)
- Tests run via `pytest` on agent code
- Git-based artifact tracking (uv.lock, livekit.toml intentionally untracked in template)

**Environment Variables by Service:**
- Docker Compose loads from `.env` file in root directory
- Services receive configuration via environment variables and volumes

## Environment Configuration

**Required env vars (Core):**
- `LIVEKIT_URL` - WebSocket URL to LiveKit server (e.g., `ws://livekit:7880`)
- `LIVEKIT_API_KEY` - LiveKit API key for token generation
- `LIVEKIT_API_SECRET` - LiveKit API secret for token generation
- `NEXT_PUBLIC_LIVEKIT_URL` - Client-side LiveKit URL (e.g., `ws://localhost:7880`)

**Optional env vars (STT):**
- `STT_PROVIDER` - "nemotron" (default) or "whisper"
- `STT_BASE_URL` - Custom STT service URL
- `STT_MODEL` - Custom STT model name
- `STT_API_KEY` - API key if using external STT service

**Optional env vars (LLM):**
- `LLAMA_BASE_URL` - Llama.cpp server URL (default: `http://llama_cpp:11434/v1`)
- `LLAMA_MODEL` - Model name for llama.cpp (default: `qwen3-4b`)
- `LLAMA_HF_REPO` - Hugging Face repo for model download
- `LLAMA_CTX_SIZE` - Context window size (default: 16384)

**Optional env vars (GPU):**
- `NEMOTRON_BASE` - Docker base image (CPU vs GPU)
- `TORCH_INDEX_URL` - PyTorch wheel index URL for CPU/GPU versions
- `LLAMA_N_GPU_LAYERS` - GPU layers for llama.cpp (GPU-only, default: 35)

**Optional env vars (TTS):**
- `KOKORO_IMAGE` - Docker image for Kokoro service

**Optional env vars (Frontend):**
- `NEXT_PUBLIC_APP_CONFIG_ENDPOINT` - Remote config fetch endpoint
- `SANDBOX_ID` - LiveKit Cloud Sandbox identifier

**Secrets location:**
- Development: `.env` (local), `.env.local` (not committed)
- Production: Environment variables set by deployment platform
- No .env files committed to git (security best practice)

## Webhooks & Callbacks

**Incoming:**
- None detected - Stateless session model

**Outgoing:**
- None detected - All communication is bidirectional WebRTC via LiveKit

## External Model Repositories

**Hugging Face Hub:**
- Nemotron: `nvidia/nemotron-speech-streaming-en-0.6b`
- Whisper: `Systran/faster-whisper-small`
- Llama: `unsloth/Qwen3-4B-Instruct-2507-GGUF` (default, configurable)
- Auto-downloaded on container startup if not cached
- Cache location: `/root/.cache/huggingface` (Nemotron/Whisper), `/models` (Llama)

## Integration Flow

**Typical User Session:**

1. **Frontend → LiveKit Server**: User connects via WebSocket with JWT token from `connection-details` API
2. **Agent Discovery**: LiveKit routes agent via room config in token
3. **Agent → LLM**: Processes user speech via pipeline:
   - Speech captured by browser WebRTC
   - Sent to LiveKit server
   - Routed to agent process
4. **Agent → STT Service**: Transcribes audio (Nemotron or Whisper)
5. **Agent → LLM Service**: Generates response (Llama.cpp or OpenAI)
6. **Agent → TTS Service**: Synthesizes response (Kokoro)
7. **Agent → LiveKit Server**: Sends synthesized audio back to user
8. **WebRTC Flow**: All audio/video streams managed by LiveKit server

---

*Integration audit: 2026-02-23*
