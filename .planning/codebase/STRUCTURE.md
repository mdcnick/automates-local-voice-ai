# Codebase Structure

**Analysis Date:** 2026-02-23

## Directory Layout

```
automates-local-voice-ai/
├── frontend/                      # Next.js React web UI
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx            # Root layout with theme setup
│   │   ├── (app)/                # Main app route group
│   │   │   ├── page.tsx          # Main page (server component)
│   │   │   └── layout.tsx        # App layout wrapper
│   │   └── api/                  # API routes (server-side)
│   │       └── connection-details/route.ts  # Token generation endpoint
│   ├── components/               # React components
│   │   ├── app/                 # Application-specific components
│   │   │   ├── app.tsx          # Main App component (SessionProvider wrapper)
│   │   │   ├── view-controller.tsx  # Manages welcome/session views
│   │   │   ├── session-view.tsx     # Active session UI layout
│   │   │   ├── welcome-view.tsx     # Pre-connection welcome screen
│   │   │   ├── chat-transcript.tsx  # Message display
│   │   │   ├── tile-layout.tsx      # Video grid layout
│   │   │   ├── theme-provider.tsx   # Theme context
│   │   │   └── theme-toggle.tsx     # Dark/light mode toggle
│   │   └── livekit/              # LiveKit-specific UI components
│   │       ├── agent-control-bar/   # Mic/camera/chat controls
│   │       ├── scroll-area/         # Custom scrollable container
│   │       ├── button.tsx           # Styled button
│   │       ├── chat-entry.tsx       # Individual chat message
│   │       ├── alert.tsx            # Alert display
│   │       ├── alert-toast.tsx      # Toast notifications
│   │       └── toaster.tsx          # Toast container
│   ├── hooks/                    # React custom hooks
│   │   ├── useAgentErrors.tsx    # Error handling hook
│   │   └── useDebug.ts           # Debug mode hook
│   ├── lib/                      # Utilities and helpers
│   │   └── utils.ts              # cn(), getAppConfig(), getSandboxTokenSource()
│   ├── styles/                   # Global CSS
│   │   └── globals.css           # Tailwind + custom variables
│   ├── fonts/                    # Custom fonts
│   ├── public/                   # Static assets (images, icons)
│   ├── app-config.ts             # AppConfig interface and defaults
│   ├── package.json              # Frontend dependencies (Next.js, React, LiveKit)
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tailwind.config.js        # Tailwind CSS setup
│   └── .eslintrc.json            # ESLint rules
│
├── livekit_agent/                # Python LiveKit Agents service
│   ├── src/
│   │   ├── agent.py              # Main agent entrypoint (session handler)
│   │   └── __init__.py           # Package marker
│   ├── tests/                    # Test directory (optional, for unit tests)
│   ├── pyproject.toml            # Python dependencies and project config
│   ├── Dockerfile                # Docker build for agent service
│   ├── .env.example              # Example environment variables
│   ├── README.md                 # Agent-specific documentation
│   ├── AGENTS.md                 # Claude Agent guidance document
│   ├── CLAUDE.md                 # References AGENTS.md
│   └── uv.lock                   # Locked dependency versions (uv package manager)
│
├── inference/                    # Local AI model services
│   ├── nemotron/                 # NVIDIA Nemotron Speech-to-Text
│   │   ├── server.py             # FastAPI STT server (OpenAI-compatible)
│   │   ├── Dockerfile            # Docker build
│   │   └── README.md             # Service documentation
│   ├── whisper/                  # Whisper STT (optional fallback)
│   │   ├── Dockerfile            # VoxBox + Whisper container
│   │   └── README.md             # Configuration guide
│   ├── llama/                    # llama.cpp LLM inference
│   │   ├── models/               # Mounted volume for cached models
│   │   └── README.md             # Setup and model selection
│   └── kokoro/                   # Kokoro Text-to-Speech
│       ├── Dockerfile            # Docker build
│       └── README.md             # TTS configuration
│
├── livekit/                      # LiveKit server configuration
│   └── (LiveKit server config files)
│
├── docker-compose.yml            # Main service orchestration
├── docker-compose.gpu.yml        # GPU-enabled variant
├── .env                          # Docker Compose environment variables
├── .env.example                  # Example env template
├── README.md                     # Project overview and getting started
└── .planning/                    # GSD planning documents (this directory)
    └── codebase/                 # Codebase analysis docs
```

## Directory Purposes

**frontend/**
- Purpose: React/Next.js web application for voice interaction
- Contains: Pages, components, hooks, configuration, styles
- Key files: `app.tsx` (main component), `route.ts` (token API), `app-config.ts` (UI config)

**livekit_agent/**
- Purpose: Python service implementing the voice agent logic
- Contains: Agent entrypoint, environment configuration, dependencies
- Key files: `src/agent.py` (session orchestration)

**inference/**
- Purpose: Containerized AI services (STT, LLM, TTS)
- Contains: Separate Docker services for each model type
- Key directories: `nemotron/` (default STT), `llama/` (LLM), `kokoro/` (TTS), `whisper/` (fallback STT)

## Key File Locations

**Entry Points:**

- `frontend/app/layout.tsx`: Root HTML layout, theme setup
- `frontend/app/(app)/page.tsx`: Main page (loads app config, renders App component)
- `livekit_agent/src/agent.py`: Agent session handler (imported by LiveKit runtime)

**Configuration:**

- `frontend/app-config.ts`: UI configuration interface and defaults
- `frontend/lib/utils.ts`: Token source, app config fetching, utility functions
- `livekit_agent/src/agent.py`: Environment variable loading, service configuration

**Core Logic:**

- `frontend/components/app/app.tsx`: SessionProvider setup, token source initialization
- `frontend/components/app/view-controller.tsx`: View state management (welcome → session)
- `frontend/components/app/session-view.tsx`: Active conversation UI layout
- `livekit_agent/src/agent.py`: Agent class definition, STT/LLM/TTS pipeline setup

**Testing:**

- `livekit_agent/tests/`: Test files for agent behavior
- Frontend tests: Not present (can be added)

## Naming Conventions

**Files:**

- React components: `PascalCase.tsx` (e.g., `SessionView.tsx`)
- Utility modules: `camelCase.ts` (e.g., `utils.ts`)
- Next.js routes: `route.ts`, `page.tsx`, `layout.tsx`
- Python files: `snake_case.py` (e.g., `agent.py`, `server.py`)

**Directories:**

- React component groups: lowercase, kebab-case or descriptive plural (e.g., `components/livekit/`, `components/app/`)
- Services/features: lowercase, plural (e.g., `hooks/`, `inference/`)
- Docker service subdirs: lowercase, match service name (e.g., `inference/nemotron/`)

**TypeScript/JavaScript:**

- Interfaces: `PascalCase` (e.g., `AppConfig`, `SessionViewProps`)
- Functions: `camelCase` (e.g., `getAppConfig()`, `cn()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `TARGET_SAMPLE_RATE`)
- React hooks: `useCamelCase` (e.g., `useSessionContext()`)

**Python:**

- Classes: `PascalCase` (e.g., `Assistant`, `AgentServer`)
- Functions/methods: `snake_case` (e.g., `load_model()`, `transcribe()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MODEL_NAME`, `TARGET_SAMPLE_RATE`)

## Where to Add New Code

**New Voice Agent Features:**

- Primary code: `livekit_agent/src/agent.py` (add tools, modify instructions)
- New tools: Define as methods with `@function_tool()` decorator in `Assistant` class
- Tests: `livekit_agent/tests/test_*.py` (use pytest)

**New Frontend Components:**

- Application UI components: `frontend/components/app/` (requires React/TSX knowledge)
- LiveKit-specific UI: `frontend/components/livekit/` (for control bars, buttons, chat)
- Hooks: `frontend/hooks/use*.tsx` (custom React hooks)

**New Inference Services:**

- Add directory: `inference/new_service/` with Dockerfile
- OpenAI-compatible endpoint: Implement `/v1/*` routes
- Update `docker-compose.yml` to add service definition
- Update `livekit_agent/src/agent.py` to configure client

**Configuration:**

- Frontend UI config: Update `frontend/app-config.ts` interface and defaults
- Environment variables: Add to `.env.example` and document in README.md
- Agent config: Update `.env.example` in `livekit_agent/` directory

**API Routes:**

- New endpoint: Add file `frontend/app/api/[feature]/route.ts`
- Token generation: Modify `frontend/app/api/connection-details/route.ts`

## Special Directories

**frontend/public/:**
- Purpose: Static assets served by Next.js
- Generated: No
- Committed: Yes
- Contents: Images, icons, logos

**inference/llama/models/:**
- Purpose: Cached model weights for llama.cpp
- Generated: Yes (downloaded on first run from HuggingFace)
- Committed: No (mounted as Docker volume)
- Size: 10GB+ depending on model

**inference/nemotron-cache/ (Docker volume):**
- Purpose: HuggingFace model cache for Nemotron
- Generated: Yes (model weight download)
- Committed: No (Docker volume)

**livekit_agent/tests/:**
- Purpose: pytest test suite for agent
- Generated: No
- Committed: Yes

**frontend/.github/workflows/:**
- Purpose: CI/CD pipeline definitions
- Generated: No
- Committed: Yes

## Import Patterns

**Frontend (TypeScript/React):**

- Absolute imports using `@/` alias pointing to frontend root
- Example: `import { App } from '@/components/app/app'`
- Configured in `tsconfig.json` with path mapping

**Agent (Python):**

- Relative imports for local modules: `from . import module`
- External packages: `from livekit.agents import Agent, AgentSession`
- Environment config: `from dotenv import load_dotenv`

---

*Structure analysis: 2026-02-23*
