---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - livekit_agent/pyproject.toml
  - livekit_agent/src/agent.py
  - docker-compose.yml
  - .env
  - .env.local
  - livekit_agent/.env.example
autonomous: true
requirements: []
must_haves:
  truths:
    - "Agent uses Deepgram cloud STT instead of local Nemotron"
    - "Nemotron service is no longer required to start the stack"
    - "Agent starts and connects without errors"
  artifacts:
    - path: "livekit_agent/src/agent.py"
      provides: "Deepgram STT integration"
      contains: "deepgram"
    - path: "livekit_agent/pyproject.toml"
      provides: "Deepgram plugin dependency"
      contains: "deepgram"
  key_links:
    - from: "livekit_agent/src/agent.py"
      to: "Deepgram cloud API"
      via: "livekit-plugins-deepgram STT plugin"
      pattern: "deepgram\\.STT"
---

<objective>
Replace the local Nemotron STT service with Deepgram cloud STT.

Purpose: Nemotron requires significant local resources; Deepgram is a cloud STT with low latency and high accuracy.
Output: Agent uses Deepgram for speech-to-text, Nemotron service removed from default compose.
</objective>

<execution_context>
@/home/nc773/.claude/get-shit-done/workflows/execute-plan.md
@/home/nc773/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@livekit_agent/src/agent.py
@livekit_agent/pyproject.toml
@docker-compose.yml
@.env
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add Deepgram plugin and wire STT in agent</name>
  <files>livekit_agent/pyproject.toml, livekit_agent/src/agent.py</files>
  <action>
1. In pyproject.toml, add `livekit-plugins-deepgram~=1.3` to dependencies (alongside the existing livekit-agents line).

2. In agent.py:
   - Add import: `from livekit.plugins import deepgram` (alongside existing imports)
   - Replace the STT construction in my_agent(). Instead of the openai.STT with nemotron/whisper branching, use:
     ```python
     stt = deepgram.STT(
         model=os.getenv("DEEPGRAM_STT_MODEL", "nova-3"),
         language=os.getenv("DEEPGRAM_LANGUAGE", "en"),
     )
     ```
     The Deepgram plugin reads `DEEPGRAM_API_KEY` from env automatically.
   - Remove the entire stt_provider/stt_base_url/stt_model/stt_api_key block (lines 82-98 approximately).
   - Update the logger.info to log Deepgram model instead of STT provider/base_url.
   - Pass `stt=stt` to AgentSession (replacing the openai.STT(...) call).

3. Run `cd /home/nc773/Documents/automates-local-voice-ai/livekit_agent && uv sync` to install the new dependency.
4. Run `cd /home/nc773/Documents/automates-local-voice-ai/livekit_agent && uv run ruff check src/ && uv run ruff format src/` to lint.
  </action>
  <verify>
    <automated>cd /home/nc773/Documents/automates-local-voice-ai/livekit_agent && uv run python -c "from livekit.plugins import deepgram; print('deepgram plugin OK')" && uv run ruff check src/</automated>
  </verify>
  <done>agent.py uses deepgram.STT, plugin installed, code passes lint</done>
</task>

<task type="auto">
  <name>Task 2: Update Docker Compose and env files for Deepgram</name>
  <files>docker-compose.yml, .env, .env.local, livekit_agent/.env.example</files>
  <action>
1. In docker-compose.yml:
   - Move the `nemotron` service to a profile (like whisper): add `profiles: ["nemotron"]` so it does not start by default.
   - Remove the `nemotron-cache` volume from the top-level volumes section (or keep it for optional use).
   - In livekit_agent service `depends_on`, remove the nemotron dependency.
   - Add `DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY:-}` to livekit_agent environment section.

2. In .env:
   - Remove or comment out the STT_PROVIDER, STT_BASE_URL, STT_MODEL, STT_API_KEY lines.
   - Remove or comment out the NEMOTRON_MODEL_NAME, NEMOTRON_MODEL_ID lines.
   - Add: `DEEPGRAM_API_KEY=` (empty, user must fill in).
   - Add: `DEEPGRAM_STT_MODEL=nova-3`

3. In .env.local:
   - Remove `STT_PROVIDER=nemotron` line.
   - Add `DEEPGRAM_API_KEY=` placeholder (user fills this in with their key).

4. In livekit_agent/.env.example:
   - Replace STT_PROVIDER/STT_BASE_URL/STT_MODEL/STT_API_KEY with:
     ```
     # Deepgram STT
     DEEPGRAM_API_KEY=
     DEEPGRAM_STT_MODEL=nova-3
     ```
  </action>
  <verify>
    <automated>cd /home/nc773/Documents/automates-local-voice-ai && docker compose config --services 2>&1 | grep -v nemotron && echo "nemotron not in default services: OK"</automated>
    <manual>Verify .env.local has DEEPGRAM_API_KEY placeholder</manual>
  </verify>
  <done>Nemotron moved to optional profile, Deepgram env vars in place, livekit_agent no longer depends on nemotron</done>
</task>

</tasks>

<verification>
- `uv run python -c "from livekit.plugins import deepgram; print('OK')"` succeeds
- `docker compose config --services` does not list nemotron (it is behind a profile)
- agent.py imports and uses deepgram.STT
- No references to nemotron remain in agent.py
</verification>

<success_criteria>
- Deepgram STT replaces Nemotron as default STT provider
- Nemotron still available via `--profile nemotron` but not started by default
- Agent code is clean, linted, and uses the official livekit-plugins-deepgram package
- User only needs to set DEEPGRAM_API_KEY to get started
</success_criteria>

<output>
After completion, create `.planning/quick/1-lets-change-nemotron-and-use-deepgram/1-SUMMARY.md`
</output>
