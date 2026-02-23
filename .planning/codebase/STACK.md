# Technology Stack

**Analysis Date:** 2026-02-23

## Languages

**Primary:**
- Python 3.9+ - Voice AI agent backend built with LiveKit Agents framework
- TypeScript 5 - React-based web frontend
- JavaScript - Build tooling and runtime

**Secondary:**
- Bash - Docker build scripts and entrypoints

## Runtime

**Environment:**
- Node.js (LTS) - Frontend development and Next.js runtime
- Python 3.9+ - Agent and inference services
- Docker/Docker Compose - Local development and containerized deployment

**Package Manager:**
- pnpm 9.15.9 - Frontend dependencies (`frontend/package.json`)
- uv - Python package manager for agent (`livekit_agent/pyproject.toml`)
- pip - Python for inference services (`inference/*/requirements.txt`)

## Frameworks

**Core:**
- Next.js 15.5.7 - React frontend framework with built-in API routes
- LiveKit Agents 1.3 - Python SDK for building voice AI agents
- FastAPI - Backend server for inference services (STT/TTS)

**Real-time Communication:**
- LiveKit Server - WebRTC server and session management
- livekit-client 2.15.15 - Client-side WebRTC communication
- livekit-server-sdk 2.13.2 - Server-side token generation and room management

**Voice AI Components:**
- OpenAI-compatible plugin (livekit.plugins.openai) - Unified STT/LLM/TTS interface
- Silero VAD - Voice Activity Detection for turn-taking
- Turn Detector (multilingual) - Contextually-aware speaker detection
- Noise cancellation plugin - Background noise removal

**Testing:**
- pytest - Python test runner
- pytest-asyncio - Async test support for Python

**Build/Dev:**
- Turbopack - Next.js build compiler
- ESLint 9 - Code linting
- Prettier 3.4.2 - Code formatting
- Tailwind CSS 4 - Utility-first CSS framework
- Ruff - Python formatter and linter
- PostCSS 4 - CSS processing

## Key Dependencies

**Critical:**
- livekit-agents[silero,turn-detector,openai] 1.3 - Core agent SDK with VAD and turn detection
- livekit-plugins-noise-cancellation 0.2 - Cloud-based noise cancellation
- torch - PyTorch for model inference (CPU/CUDA/MPS)
- NVIDIA NeMo - ASR model wrapper for Nemotron STT (`inference/nemotron/`)
- faster-whisper - OpenAI Whisper alternative for STT fallback (`inference/whisper/`)
- fastapi - STT server framework
- uvicorn - ASGI server for FastAPI services

**Frontend UI:**
- @livekit/components-react 2.9.15 - LiveKit UI components
- react 19.0.0 - UI library
- react-dom 19.0.0 - React DOM rendering
- sonner 2.0.7 - Toast notifications
- motion 12.16.0 - Animation library
- @phosphor-icons/react 2.1.8 - Icon library
- @radix-ui/* - Headless UI components (select, toggle, slot)
- class-variance-authority 0.7.1 - Variant management

**Utilities:**
- livekit-server-sdk 2.13.2 - JWT token generation
- jose 6.0.12 - JWT handling
- python-dotenv - Environment variable loading
- soundfile - Audio file I/O
- numpy - Numerical computing
- torchaudio - Audio processing

## Configuration

**Environment:**
- `.env` files - Local development configuration
- Environment variables by service:
  - LiveKit: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
  - STT: `STT_PROVIDER` (nemotron|whisper), `STT_BASE_URL`, `STT_MODEL`, `STT_API_KEY`
  - LLM: `LLAMA_BASE_URL`, `LLAMA_MODEL`, `LLAMA_HF_REPO`, `LLAMA_CTX_SIZE`
  - Nemotron: `NEMOTRON_MODEL_NAME`, `NEMOTRON_MODEL_ID`
  - Frontend: `NEXT_PUBLIC_LIVEKIT_URL`, `NEXT_PUBLIC_APP_CONFIG_ENDPOINT`

**Build:**
- `docker-compose.yml` - Multi-container orchestration for local development
- `docker-compose.gpu.yml` - GPU-enabled variant with CUDA support
- `docker-compose.macos.yml` - macOS-specific configuration
- Dockerfiles in `inference/*/Dockerfile` - Containerized inference services

**Frontend Configuration:**
- `app-config.ts` - App-level UI configuration (theming, features)
- `tsconfig.json` - TypeScript configuration

**Backend Configuration:**
- `pyproject.toml` (livekit_agent) - Python project metadata and dependencies
- Ruff formatter configuration in `pyproject.toml`

## Platform Requirements

**Development:**
- Docker and Docker Compose 2.0+
- Node.js 18+ (for Next.js 15)
- Python 3.9+
- 8GB+ RAM (16GB+ recommended for GPU inference)
- GPU optional but recommended (NVIDIA CUDA 12.4+ for GPU acceleration)

**Production:**
- Docker/Kubernetes container orchestration
- LiveKit Cloud or self-hosted LiveKit server
- GPU hardware strongly recommended for real-time STT/TTS/LLM inference
- Model storage: Hugging Face cache volume mounted in containers

**GPU Support:**
- NVIDIA CUDA 12.4.1 - GPU compute backend
- cuDNN - CUDA deep learning library
- PyTorch with CUDA wheels - GPU-accelerated torch operations
- Apple MPS support via MPS fallback flag for M-series Macs

---

*Stack analysis: 2026-02-23*
