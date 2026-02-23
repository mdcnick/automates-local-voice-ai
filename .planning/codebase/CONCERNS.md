# Codebase Concerns

**Analysis Date:** 2026-02-23

## Tech Debt

**Hardcoded localhost addresses in agent code:**
- Issue: Development URLs left in production agent code as commented-out alternatives
- Files: `livekit_agent/src/agent.py` (lines 86, 92, 98)
- Impact: Developers may accidentally uncomment these, breaking production configurations and creating debugging confusion
- Fix approach: Move all localhost URLs to a separate development configuration file or environment-based conditional logic

**Global model variable in Nemotron server:**
- Issue: `asr_model` is a global variable that could be None, leading to potential runtime errors
- Files: `inference/nemotron/server.py` (line 33)
- Impact: Model state is not properly isolated; concurrent requests may interfere with each other; type checking is weak
- Fix approach: Encapsulate model lifecycle in a class with proper initialization, dependency injection, or async context manager pattern

**Missing error context in exception handling:**
- Issue: `inference/nemotron/server.py` line 78 catches all exceptions with bare `except Exception:` and falls through to alternative loading
- Files: `inference/nemotron/server.py` (line 78)
- Impact: Failures are silently masked, making debugging difficult when audio format issues occur
- Fix approach: Log caught exceptions before fallback attempts; use specific exception types instead of bare catch-all

**Unused/redundant parameters in Nemotron API:**
- Issue: The `transcribe()` function accepts parameters (language, temperature, prompt) that are immediately discarded
- Files: `inference/nemotron/server.py` (line 251)
- Impact: API contract suggests features that don't work; confuses clients about capabilities
- Fix approach: Either implement these parameters or remove them from the function signature and OpenAI compatibility documentation

## Known Bugs

**Function return type mismatch in agent:**
- Symptoms: `multiply_numbers()` function is declared to return `dict[str, Any]` but returns a string
- Files: `livekit_agent/src/agent.py` (lines 38, 46)
- Trigger: Any invocation of the multiply_numbers function tool
- Workaround: Type checking is weak; the error is masked at runtime but violates the function contract

**Potential incorrect audio channel handling:**
- Symptoms: Audio processing may fail silently for certain multichannel formats
- Files: `inference/nemotron/server.py` (lines 83-84)
- Trigger: Upload audio with shape > 2 dimensions that doesn't fit the assumed channel-first layout
- Workaround: All uploaded audio must be stereo or mono; complex channel layouts are unsupported

## Security Considerations

**Hardcoded default credentials in Docker configuration:**
- Risk: Default LiveKit credentials (devkey/secret) are baked into Dockerfiles
- Files: `frontend/Dockerfile` (lines 13-16, 21-24), `docker-compose.yml` (lines 91-95, 124-125), `.env` (visible in repo)
- Current mitigation: These are documented as development-only, but are easily overlooked in production deployments
- Recommendations:
  - Never include default credentials in Dockerfiles; pass them only as build args or runtime secrets
  - Document security requirements prominently
  - Add validation to reject known default credentials at startup
  - Use secrets management (Docker Secrets, Kubernetes Secrets, Vault) for production

**No input validation on audio uploads:**
- Risk: `load_audio()` processes arbitrary file data without validating file type or size limits
- Files: `inference/nemotron/server.py` (lines 68-102)
- Current mitigation: Relies on soundfile/torchaudio to reject invalid formats
- Recommendations:
  - Add explicit max file size check before processing
  - Validate audio duration limits
  - Implement rate limiting on transcription endpoint

**Missing CORS validation in frontend API route:**
- Risk: `/api/connection-details` lacks CORS headers or origin validation
- Files: `frontend/app/api/connection-details/route.ts` (no CORS configuration visible)
- Current mitigation: NextAuth/LiveKit tokens provide some security, but endpoint is open to cross-origin requests
- Recommendations:
  - Add explicit CORS validation
  - Restrict token generation to verified origins
  - Implement rate limiting

**Environment variables exposed in build artifacts:**
- Risk: Default credentials are in `.env` file checked into git
- Files: `.env` (checked into repository)
- Current mitigation: `.env.example` exists separately
- Recommendations:
  - Remove `.env` from git history
  - Update `.gitignore` to prevent future commits
  - Use only `.env.example` with placeholder values in repo

## Performance Bottlenecks

**Streaming transcription implementation is CPU-bound:**
- Problem: `streaming_transcribe()` processes audio chunks sequentially in Python without parallelization
- Files: `inference/nemotron/server.py` (lines 129-225)
- Cause: Generator pattern forces single-threaded processing; large chunk sizes can cause perceived latency
- Improvement path:
  - Consider batch processing with overlapping windows
  - Offload preprocessing to GPU where available
  - Add configurable chunk and shift sizes via environment variables

**Model initialization happens at container startup, blocking requests:**
- Problem: First request to `/v1/audio/transcriptions` waits for full VAD and STT model loading
- Files: `inference/nemotron/server.py` (lines 50-56), `docker-compose.yml` (lines 33-38)
- Cause: Models are loaded synchronously during app startup in lifespan handler
- Improvement path:
  - Add explicit model prewarming endpoint that reports detailed progress
  - Implement lazy loading with proper initialization detection
  - Expose model loading progress metrics

**No connection pooling for inter-service communication:**
- Problem: Each agent session makes fresh connections to llama_cpp, nemotron, and kokoro
- Files: `livekit_agent/src/agent.py` (lines 84-102)
- Cause: LiveKit Agents creates new OpenAI clients per session
- Improvement path:
  - Implement HTTP connection pooling at the agent level
  - Use persistent connections with keepalive
  - Add connection metrics and monitoring

**Synchronous file I/O in audio loading:**
- Problem: `load_audio()` uses blocking tempfile operations that could block other requests
- Files: `inference/nemotron/server.py` (lines 72-86)
- Cause: FastAPI routes are async but call blocking I/O operations synchronously
- Improvement path:
  - Use `aiofiles` for async file operations
  - Stream audio directly without temporary files where possible
  - Add timeout guards on file operations

## Fragile Areas

**Audio format detection and fallback chain:**
- Files: `inference/nemotron/server.py` (lines 77-86)
- Why fragile: Silent fallback from soundfile to torchaudio obscures which codec is actually being used; if both fail, the error is ambiguous
- Safe modification: Add explicit logging for each codec attempt; test with variety of audio formats before changing
- Test coverage: No test cases for audio loading; missing coverage for WAV, OGG, FLAC, MP3 variants

**Agent-to-service dependencies (hardcoded URLs):**
- Files: `livekit_agent/src/agent.py` (lines 61-74, 84-102)
- Why fragile: Environment variable names are not validated; typos or missing vars silently fall back to defaults; no schema validation
- Safe modification: Create a configuration dataclass with validation, add required env var checks at startup
- Test coverage: Only smoke tests exist; no tests for environment variable handling or service discovery

**Nemotron streaming hypothesis extraction:**
- Files: `inference/nemotron/server.py` (lines 201-215)
- Why fragile: Multiple fallback paths for extracting hypothesis text; assumes specific attribute names and types; if model output changes, streaming breaks silently
- Safe modification: Add detailed debug logging for each extraction attempt; wrap hypothesis objects in a typed adapter
- Test coverage: No unit tests for streaming_transcribe() or hypothesis extraction logic

**Token generation in connection-details endpoint:**
- Files: `frontend/app/api/connection-details/route.ts` (lines 41-45, 66-90)
- Why fragile: Room and participant names use random numbers without uniqueness guarantees; no collision detection
- Safe modification: Switch to UUID v4 or timestamp-based naming; add database lookup to verify room doesn't already exist
- Test coverage: No tests for concurrent token generation or collision scenarios

## Scaling Limits

**Single-threaded Python agent per container:**
- Current capacity: 1 concurrent RTC session per `livekit_agent` container
- Limit: As conversation complexity increases (longer contexts, more function calls), latency grows linearly; no horizontal scaling by default
- Scaling path:
  - Deploy multiple agent replicas using Kubernetes or Docker Swarm
  - Add load balancing in LiveKit configuration
  - Consider async task offloading for long-running operations

**Model memory usage unbounded in Nemotron container:**
- Current capacity: Single ~600MB model loaded at all times
- Limit: Larger models (1B-7B parameters) would exhaust typical GPU VRAM (8-16GB); CPU fallback is very slow
- Scaling path:
  - Implement model quantization (int8, int4) to reduce memory
  - Use model serving framework (vLLM, TensorRT) for batching and optimization
  - Add memory monitoring and request queuing

**Audio transcription latency scales with audio duration:**
- Current capacity: Real-time for typical turn-taking (1-5 seconds of audio)
- Limit: Transcribing 60+ seconds of audio causes significant latency; no streaming response until full processing
- Scaling path:
  - Implement true streaming with incremental hypothesis updates (already partially done but could be optimized)
  - Add audio chunking at stream ingestion to process overlapping windows
  - Consider using faster models for lower latency vs. accuracy tradeoff

**LLM context window fixed at 16384 tokens:**
- Current capacity: `LLAMA_CTX_SIZE=16384` (docker-compose.yml line 69)
- Limit: Long conversations exceed context; model cannot see full conversation history
- Scaling path:
  - Increase context size (requires larger model and more VRAM)
  - Implement context summarization or rolling window
  - Add explicit conversation history management in agent

## Dependencies at Risk

**LiveKit Agents SDK is fast-evolving:**
- Risk: Major version updates likely to break compatibility; frequent breaking changes reported in ecosystem
- Impact: Agent code may break after dependency updates; `livekit-agents~=1.3` allows breaking updates
- Migration plan:
  - Pin exact versions in production (use `==` instead of `~=`)
  - Maintain AGENTS.md documentation for upgrade paths
  - Test thoroughly before upgrading major versions

**NVIDIA Nemotron model availability uncertain:**
- Risk: Model may be deprecated or removed from HuggingFace; no long-term support guarantees
- Impact: If model becomes unavailable, the STT pipeline breaks completely; no automatic fallback
- Migration plan:
  - Keep Whisper fallback profile tested and ready to switch
  - Monitor Hugging Face model repository for deprecation notices
  - Maintain local model cache or mirror

**PyTorch and CUDA compatibility chain:**
- Risk: PyTorch, CUDA, and individual model implementations have complex compatibility requirements
- Impact: GPU builds may fail on certain hardware; CPU/MPS fallbacks add complexity and debugging burden
- Migration plan:
  - Document exact CUDA/driver versions known to work
  - Maintain CI testing for CPU, GPU, and MPS code paths
  - Use Docker base images with pre-validated PyTorch builds

## Missing Critical Features

**No logging aggregation or monitoring:**
- Problem: Logs are written to stdout in containers; no centralized logging, metrics, or alerting
- Blocks: Cannot diagnose production issues or detect silent failures
- Impact: Latency and error patterns are invisible; debugging requires container logs

**No health check for inter-service communication:**
- Problem: Services check their own health (`/health` endpoints) but don't verify downstream dependencies
- Blocks: Services can report "healthy" while dependent services are down
- Impact: Agent starts and fails immediately when nemotron or llama_cpp become unavailable

**No rate limiting or quota enforcement:**
- Problem: No protection against transcription or token generation abuse
- Blocks: Single user could exhaust model resources or cause denial of service
- Impact: Shared infrastructure is vulnerable to resource exhaustion

**No conversation persistence or history:**
- Problem: Agent creates new session for each room connection; conversation history is ephemeral
- Blocks: Multi-turn experiences with persistent state are impossible
- Impact: Each reconnection loses all context

**No function tool result validation:**
- Problem: `multiply_numbers()` returns a string but is typed as `dict[str, Any]`; no schema validation for tool outputs
- Blocks: LLM cannot reliably parse function results; may hallucinate or misinterpret output
- Impact: Complex workflows with multiple function calls are unreliable

## Test Coverage Gaps

**No tests for audio format handling:**
- What's not tested: WAV, OGG, MP3, FLAC, stereo vs mono, various sample rates, corrupted files
- Files: `inference/nemotron/server.py` (lines 68-102)
- Risk: Audio loading failures go undetected until production; fallback chain masks real issues
- Priority: High - audio is the core input to the system

**No integration tests for agent-to-service communication:**
- What's not tested: What happens when llama_cpp is slow/unavailable, nemotron errors, kokoro disconnects
- Files: `livekit_agent/src/agent.py`
- Risk: Agent crashes silently or hangs indefinitely on service failures
- Priority: High - service availability directly affects reliability

**No end-to-end tests for streaming transcription:**
- What's not tested: Streaming transcription with realistic audio sequences, interrupt/resume behavior, partial hypothesis accuracy
- Files: `inference/nemotron/server.py` (lines 129-225)
- Risk: Streaming implementation may be broken and nobody knows until deployed
- Priority: Medium - impacts real-time experience but fallback to direct transcription exists

**No tests for token generation collision handling:**
- What's not tested: Race conditions in room/participant ID generation, concurrent token requests
- Files: `frontend/app/api/connection-details/route.ts`
- Risk: Multiple users could get same room ID; sessions collide or fail to establish
- Priority: Medium - unlikely but would be critical when it happens

**No load/stress tests:**
- What's not tested: How system performs with multiple concurrent sessions, large audio files, long transcription times
- Files: Entire pipeline
- Risk: Performance degradation and resource exhaustion are invisible until deployment
- Priority: Medium - important for production readiness but can be added incrementally

**No test coverage for error conditions in agent:**
- What's not tested: What happens when LLM times out, STT returns empty string, TTS fails, connection drops
- Files: `livekit_agent/src/agent.py` (lines 83-111)
- Risk: Agent behavior in failure scenarios is unpredictable
- Priority: Low - LiveKit SDK handles some, but explicit error handling would improve reliability

---

*Concerns audit: 2026-02-23*
