# Phase 1: Infrastructure Baseline - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Switch LLM inference from local llama.cpp to OpenRouter as the primary path. Remove llama.cpp from the default Docker Compose configuration. Implement graceful fallback behavior when OpenRouter is rate-limited or unavailable. Model must be configurable via environment variable.

</domain>

<decisions>
## Implementation Decisions

### Rate-limit fallback
- On rate limit: speak a casual, brief message ("Hang on a sec" style) and retry silently
- Retry window: 60 seconds with backoff before giving up
- If all retries fail: apologize briefly ("Sorry, I can't answer that right now") and drop the response — wait for next user input
- Try next model in fallback chain before doing wait-and-retry on same model

### Model selection
- Default model: Llama 3.3 70B (`meta-llama/llama-3.3-70b-instruct` or OpenRouter equivalent)
- Env var accepts comma-separated fallback chain (e.g. `LLM_MODEL=llama-3.3-70b,qwen-2.5-72b`)
- Fallback chain triggers on both rate limits and model unavailability
- Silent fallback — user is not told which model is responding

### Migration approach
- Remove llama.cpp service from default docker-compose.yml
- Keep local inference as a separate Docker container (compose profile) — not started by default
- Local fallback uses a smaller model (7B/8B class) that can run without GPU
- Local fallback activates automatically as last resort when entire OpenRouter chain fails
- No env var toggle needed — automatic last-resort behavior

### Voice behavior during errors
- Vague, friendly error message — no technical details spoken to user
- One generic message for all error types (keeps it simple and consistent)
- Assistant stays listening after error — ready for next input immediately
- Detailed errors logged to console/file for debugging

### Claude's Discretion
- Exact retry backoff strategy (exponential, linear, etc.)
- Specific error message wording
- Log format and rotation
- Which small local model to use for emergency fallback
- OpenRouter API integration patterns

</decisions>

<specifics>
## Specific Ideas

- Fallback chain order: try next model first on rate limit, then retry with backoff, then local as absolute last resort
- The spoken fallback should feel natural in conversation — brief pause acknowledgment, not robotic error handling
- Error logging should be useful for debugging without being noisy

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-infrastructure-baseline*
*Context gathered: 2026-02-23*
