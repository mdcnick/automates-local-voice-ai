---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - docker-compose.yml
  - .env
  - livekit/Dockerfile
autonomous: true
requirements: []
must_haves:
  truths:
    - "Local livekit server container is removed from docker-compose"
    - "Agent and frontend connect to LiveKit Cloud instead of local server"
    - "User provides LiveKit Cloud credentials via .env"
  artifacts:
    - path: "docker-compose.yml"
      provides: "No livekit service, agent/frontend use cloud URL"
    - path: ".env"
      provides: "LiveKit Cloud env var placeholders"
  key_links:
    - from: "livekit_agent service"
      to: "LiveKit Cloud"
      via: "LIVEKIT_URL env var (wss://...)"
    - from: "frontend service"
      to: "LiveKit Cloud"
      via: "NEXT_PUBLIC_LIVEKIT_URL env var (wss://...)"
user_setup:
  - service: livekit-cloud
    why: "LiveKit Cloud replaces local server"
    env_vars:
      - name: LIVEKIT_URL
        source: "LiveKit Cloud dashboard -> Settings -> Keys"
      - name: LIVEKIT_API_KEY
        source: "LiveKit Cloud dashboard -> Settings -> Keys"
      - name: LIVEKIT_API_SECRET
        source: "LiveKit Cloud dashboard -> Settings -> Keys"
---

<objective>
Remove the self-hosted LiveKit server from docker-compose and switch all services to use LiveKit Cloud.

Purpose: Simplify infrastructure -- no need to run a local LiveKit server when LiveKit Cloud is more reliable and handles scaling.
Output: Updated docker-compose.yml and .env pointing to LiveKit Cloud.
</objective>

<execution_context>
@/home/nc773/.claude/get-shit-done/workflows/execute-plan.md
@/home/nc773/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@docker-compose.yml
@.env
@frontend/app/api/connection-details/route.ts
@livekit_agent/src/agent.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove local LiveKit server and update docker-compose</name>
  <files>docker-compose.yml</files>
  <action>
1. Remove the entire `livekit` service block (image: livekit/livekit-server, ports 7880/7881, --dev command).
2. Remove `livekit/Dockerfile` if it only served the local server (check contents first).
3. In `livekit_agent` service:
   - Remove the `depends_on.livekit` entry (keep `depends_on.kokoro`).
   - Change LIVEKIT_URL default from `ws://livekit:7880` to empty string (force user to set it): `LIVEKIT_URL=${LIVEKIT_URL}`.
   - Same for LIVEKIT_HOST.
   - Change LIVEKIT_API_KEY default from `devkey` to empty: `LIVEKIT_API_KEY=${LIVEKIT_API_KEY}`.
   - Change LIVEKIT_API_SECRET default from `secret` to empty: `LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}`.
4. In `frontend` service:
   - Remove `depends_on.livekit` entirely.
   - Change environment to use variables without hardcoded defaults:
     - `NEXT_PUBLIC_LIVEKIT_URL=${NEXT_PUBLIC_LIVEKIT_URL}` (this is the public wss:// URL)
     - `LIVEKIT_URL=${LIVEKIT_URL}` (server-side, same cloud URL)
     - `LIVEKIT_API_KEY=${LIVEKIT_API_KEY}`
     - `LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}`
  </action>
  <verify>
    <automated>cd /home/nc773/Documents/automates-local-voice-ai && grep -c "livekit/livekit-server" docker-compose.yml | grep -q "^0$" && echo "PASS: no local livekit server" || echo "FAIL"</automated>
  </verify>
  <done>No local livekit service in docker-compose. Agent and frontend reference env vars for LiveKit Cloud.</done>
</task>

<task type="auto">
  <name>Task 2: Update .env with LiveKit Cloud placeholders</name>
  <files>.env</files>
  <action>
1. Update .env file:
   - Change `LIVEKIT_URL=http://livekit:7880` to `LIVEKIT_URL=` (empty, user fills in wss://... from cloud dashboard).
   - Change `LIVEKIT_API_KEY=devkey` to `LIVEKIT_API_KEY=` (empty placeholder).
   - Change `LIVEKIT_API_SECRET=secret` to `LIVEKIT_API_SECRET=` (empty placeholder).
   - Change `NEXT_PUBLIC_LIVEKIT_URL=http://localhost:7880` to `NEXT_PUBLIC_LIVEKIT_URL=` (empty placeholder).
   - Add comments above each: `# LiveKit Cloud credentials (get from https://cloud.livekit.io)`

Note: Do NOT commit actual credentials. Leave empty for user to fill in.
  </action>
  <verify>
    <automated>cd /home/nc773/Documents/automates-local-voice-ai && grep "LIVEKIT_URL=" .env | head -1 | grep -qv "livekit:7880" && echo "PASS" || echo "FAIL"</automated>
  </verify>
  <done>.env has empty LiveKit Cloud placeholders with helpful comments. No hardcoded local URLs.</done>
</task>

</tasks>

<verification>
- `grep -r "livekit:7880" docker-compose.yml .env` returns nothing
- `grep "livekit/livekit-server" docker-compose.yml` returns nothing
- docker-compose.yml still has livekit_agent and frontend services
- .env has empty LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET placeholders
</verification>

<success_criteria>
- Local LiveKit server fully removed from docker-compose
- All services reference LiveKit Cloud via env vars
- User can fill in .env with their LiveKit Cloud credentials and run
</success_criteria>

<output>
After completion, create `.planning/quick/2-stop-building-a-local-livekit-server-use/2-SUMMARY.md`
</output>
