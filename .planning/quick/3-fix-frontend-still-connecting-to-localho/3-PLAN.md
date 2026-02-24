---
phase: quick-3
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/Dockerfile
  - frontend/.env.example
  - livekit_agent/.env.example
autonomous: true
requirements: []
must_haves:
  truths:
    - "Frontend Dockerfile does not contain any localhost:7880 or devkey/secret hardcoded values"
    - "Frontend reads LIVEKIT_URL and credentials from environment variables at runtime"
    - ".env.example files show LiveKit Cloud placeholder patterns, not localhost"
  artifacts:
    - path: "frontend/Dockerfile"
      provides: "Build and runtime stages using ARG/ENV from docker-compose"
      contains: "NEXT_PUBLIC_LIVEKIT_URL"
    - path: "frontend/.env.example"
      provides: "Cloud-oriented placeholder"
      contains: "wss://"
    - path: "livekit_agent/.env.example"
      provides: "Cloud-oriented placeholder"
      contains: "wss://"
  key_links:
    - from: "docker-compose.yml"
      to: "frontend/Dockerfile"
      via: "environment variables passed at runtime"
      pattern: "NEXT_PUBLIC_LIVEKIT_URL"
---

<objective>
Remove all hardcoded localhost:7880 and devkey/secret references from the frontend Dockerfile and .env.example files, completing the LiveKit Cloud migration started in quick-2.

Purpose: The frontend Docker image currently bakes in localhost:7880 at build time, so even with correct .env values, the Next.js build embeds the wrong NEXT_PUBLIC_LIVEKIT_URL.
Output: Dockerfile uses build args from environment; .env.example files show cloud placeholders.
</objective>

<execution_context>
@/home/nc773/.claude/get-shit-done/workflows/execute-plan.md
@/home/nc773/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@frontend/Dockerfile
@frontend/.env.example
@livekit_agent/.env.example
@docker-compose.yml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix frontend Dockerfile to use build args instead of hardcoded values</name>
  <files>frontend/Dockerfile</files>
  <action>
    In the build stage:
    - Replace hardcoded ENV lines with ARG declarations: ARG LIVEKIT_URL, ARG LIVEKIT_API_KEY, ARG LIVEKIT_API_SECRET, ARG NEXT_PUBLIC_LIVEKIT_URL
    - Set ENV from ARG so Next.js picks them up at build time: ENV LIVEKIT_URL=$LIVEKIT_URL etc.
    - Use empty string defaults for ARGs (forcing docker-compose to supply them)

    In the runner stage:
    - Remove the hardcoded ENV block entirely. The runtime container gets env vars from docker-compose.yml `environment:` block, not from Dockerfile defaults.
    - Keep ENV NODE_ENV=production.

    The result should look like:
    ```
    FROM base AS build
    RUN corepack enable
    COPY --from=deps /app/node_modules ./node_modules
    COPY . .
    ARG LIVEKIT_URL=""
    ARG LIVEKIT_API_KEY=""
    ARG LIVEKIT_API_SECRET=""
    ARG NEXT_PUBLIC_LIVEKIT_URL=""
    ENV LIVEKIT_URL=$LIVEKIT_URL \
        LIVEKIT_API_KEY=$LIVEKIT_API_KEY \
        LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET \
        NEXT_PUBLIC_LIVEKIT_URL=$NEXT_PUBLIC_LIVEKIT_URL
    RUN pnpm run build
    ```

    For the runner stage, just keep NODE_ENV=production and no LiveKit env defaults.
  </action>
  <verify>
    <automated>cd /home/nc773/Documents/automates-local-voice-ai && ! grep -q "localhost:7880\|livekit:7880\|devkey\|LIVEKIT_API_SECRET=secret" frontend/Dockerfile && grep -q "ARG NEXT_PUBLIC_LIVEKIT_URL" frontend/Dockerfile && echo "PASS" || echo "FAIL"</automated>
  </verify>
  <done>Dockerfile has no hardcoded localhost:7880, devkey, or secret values. Build stage uses ARGs; runner stage inherits env from docker-compose.</done>
</task>

<task type="auto">
  <name>Task 2: Update .env.example files with cloud placeholders</name>
  <files>frontend/.env.example, livekit_agent/.env.example</files>
  <action>
    frontend/.env.example:
    - Change LIVEKIT_URL to: LIVEKIT_URL=wss://your-project.livekit.cloud
    - Change LIVEKIT_API_KEY to: LIVEKIT_API_KEY=
    - Change LIVEKIT_API_SECRET to: LIVEKIT_API_SECRET=
    - Change NEXT_PUBLIC_LIVEKIT_URL to: NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
    - Update the comment from "connect to the LiveKit server" to "connect to LiveKit Cloud"

    livekit_agent/.env.example:
    - Change LIVEKIT_URL to: LIVEKIT_URL=wss://your-project.livekit.cloud
    - Change LIVEKIT_API_KEY to: LIVEKIT_API_KEY=
    - Change LIVEKIT_API_SECRET to: LIVEKIT_API_SECRET=
  </action>
  <verify>
    <automated>cd /home/nc773/Documents/automates-local-voice-ai && ! grep -q "localhost:7880\|livekit:7880\|devkey\|=secret" frontend/.env.example livekit_agent/.env.example && grep -q "wss://" frontend/.env.example && grep -q "wss://" livekit_agent/.env.example && echo "PASS" || echo "FAIL"</automated>
  </verify>
  <done>Both .env.example files show LiveKit Cloud wss:// placeholders with no localhost references.</done>
</task>

</tasks>

<verification>
- `grep -rn "localhost:7880\|livekit:7880" frontend/ livekit_agent/.env.example` returns no matches
- `grep -rn "devkey" frontend/ livekit_agent/.env.example` returns no matches
- frontend/Dockerfile uses ARG for all LiveKit variables
</verification>

<success_criteria>
- Zero hardcoded localhost:7880 or devkey/secret in frontend/Dockerfile and .env.example files
- Dockerfile build stage uses ARG+ENV pattern for LiveKit variables
- Dockerfile runner stage has no LiveKit env defaults (relies on docker-compose)
- .env.example files show wss://your-project.livekit.cloud pattern
</success_criteria>

<output>
After completion, create `.planning/quick/3-fix-frontend-still-connecting-to-localho/3-SUMMARY.md`
</output>
