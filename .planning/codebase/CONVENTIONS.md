# Coding Conventions

**Analysis Date:** 2026-02-23

## Naming Patterns

**Files:**
- Component files: PascalCase - `WelcomeView.tsx`, `ChatInput.tsx`, `AgentControlBar.tsx`
- Utility/helper files: camelCase - `utils.ts`, `useDebug.ts`
- Hook files: camelCase with `use` prefix - `useAgentErrors.tsx`, `useDebug.ts`, `useInputControls.ts`
- API route files: lowercase with hyphens - `connection-details/route.ts`
- Config files: camelCase - `app-config.ts`

**Functions:**
- React component names: PascalCase - `export function Button()`, `export const SessionView`
- Hook functions: camelCase with `use` prefix - `useAgentErrors()`, `useDebugMode()`, `useInputControls()`
- Utility functions: camelCase - `getAppConfig()`, `getSandboxTokenSource()`, `cn()`
- Handler functions: camelCase with `handle` prefix - `handleSubmit()`, `handleAudioDeviceChange()`, `handleToggleCamera()`
- Private/internal functions: camelCase - `createParticipantToken()`, `Fade()` (sub-components)

**Variables:**
- Component props: PascalCase suffixed with `Props` - `interface ChatInputProps`, `interface AppProps`
- State variables: camelCase - `const [message, setMessage]`, `const [isSending, setIsSending]`
- Constants: UPPER_SNAKE_CASE - `const IN_DEVELOPMENT`, `const API_KEY`, `const MOTION_PROPS`
- Private/local variables: camelCase - `const hdrs`, `const appConfig`

**Types:**
- Interfaces: PascalCase without prefix - `interface AppConfig`, `interface ConnectionDetails`, `interface UseInputControlsReturn`
- Type aliases: PascalCase - `type ConnectionDetails`, `type SandboxConfig`
- Enums: PascalCase (if used)
- Generic type parameters: Single uppercase letter - `<T>`, `<P>` in component typing

## Code Style

**Formatting:**
- Tool: Prettier 3.4.2
- Tab width: 2 spaces
- Print width: 100 characters
- Trailing commas: ES5 format
- Semicolons: Required (semi: true)
- Quotes: Single quotes for strings
- Line endings: Auto-detected

**Linting:**
- Tool: ESLint 9 with flat config (`eslint.config.mjs`)
- Extends: `next/core-web-vitals`, `next/typescript`, `plugin:import/recommended`, `prettier`
- Config file: `/home/nc773/Documents/automates-local-voice-ai/frontend/.eslintrc.json` (legacy) and `eslint.config.mjs` (flat config)
- Prettier integration: `plugin:prettier/recommended` enforces consistent formatting

**Format Check:**
```bash
pnpm format:check      # Check formatting without changes
pnpm format            # Auto-format all files
pnpm lint              # Run ESLint
```

## Import Organization

**Order (Prettier plugin: @trivago/prettier-plugin-sort-imports):**
1. React imports - `^react`
2. Next.js imports - `^next`, `^next/(.*)$`
3. Third-party modules - `<THIRD_PARTY_MODULES>`
4. Scoped packages - `^@[^/](.*)$`
5. Path aliases (@/) - `^@/(.*)$`
6. Relative imports - `^[./]`

**Examples from codebase:**

```typescript
// app/(app)/page.tsx - Shows correct import order
import { headers } from 'next/headers';
import { App } from '@/components/app/app';
import { getAppConfig } from '@/lib/utils';

// components/app/app.tsx - Shows React and Next imports first
import { useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import {
  RoomAudioRenderer,
  SessionProvider,
  StartAudio,
  useSession,
} from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/livekit/toaster';
```

**Path Aliases:**
- `@/*` maps to root of `/frontend/` directory
- Used consistently for imports across components, hooks, lib files

**Specifier sorting:** Alphabetical within each import group (importOrderSortSpecifiers: true)

## Error Handling

**Patterns:**
- Try-catch blocks for async operations: `try { ... } catch (error) { ... }`
- Type narrowing for error objects: `if (error instanceof Error) { ... }`
- Console error logging with context - errors include file location and operation description
- Error messages include context about what failed:
  - Example: `'ERROR: getAppConfig() - lib/utils.ts'` includes function and file path
  - Example: `'Error fetching connection details:'` describes the operation

**Examples from codebase:**

```typescript
// lib/utils.ts - Demonstrates proper error handling pattern
try {
  if (!sandboxId) {
    throw new Error('Sandbox ID is required');
  }
  const response = await fetch(CONFIG_ENDPOINT, {...});
  if (response.ok) {
    const remoteConfig: SandboxConfig = await response.json();
    // ... process config
    return config;
  } else {
    console.error(
      `ERROR: querying config endpoint failed with status ${response.status}: ${response.statusText}`
    );
  }
} catch (error) {
  console.error('ERROR: getAppConfig() - lib/utils.ts', error);
}
return APP_CONFIG_DEFAULTS;

// chat-input.tsx - Try-catch for async operations
const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  try {
    setIsSending(true);
    await onSend(message);
    setMessage('');
  } catch (error) {
    console.error(error);
  } finally {
    setIsSending(false);
  }
};

// route.ts - Type narrowing for error handling
catch (error) {
  if (error instanceof Error) {
    console.error(error);
    return new NextResponse(error.message, { status: 500 });
  }
}
```

## Logging

**Framework:** `console` object (no centralized logging library)

**Methods used:**
- `console.error()` - For errors and warnings

**Patterns:**
- Errors logged with context about the operation: `console.error('ERROR: operation - file.ts', error)`
- Short contextual messages: `console.error(error)` for caught exceptions
- Errors include HTTP status and descriptions when applicable
- No debug logging in regular code (debug features use `useDebugMode` hook for development)

**Example:**
```typescript
// Descriptive error logging
console.error(
  `ERROR: querying config endpoint failed with status ${response.status}: ${response.statusText}`
);
console.error('ERROR: getAppConfig() - lib/utils.ts', error);
```

## Comments

**When to Comment:**
- Technical decisions that aren't immediately obvious - shown in `lib/utils.ts` with React cache behavior explanation
- Warnings about limitations or caveats - example: `@note React will invalidate the cache for all memoized functions for each server request`
- Non-standard TypeScript suppression reasoning - `// @ts-expect-error I'm not sure quite how to appease TypeScript...`
- Implementation notes for non-obvious logic

**JSDoc/TSDoc:**
- Used for public utility functions
- Includes parameter descriptions and return types
- Example from `lib/utils.ts`:

```typescript
/**
 * Get the app configuration
 * @param headers - The headers of the request
 * @returns The app configuration
 *
 * @note React will invalidate the cache for all memoized functions for each server request.
 * https://react.dev/reference/react/cache#caveats
 */
export const getAppConfig = cache(async (headers: Headers): Promise<AppConfig> => {
```

**Suppression Comments:**
- `@ts-expect-error` used with explanation: `// @ts-expect-error this is a global variable`
- TypeScript strict mode enabled, suppressions are rare and documented

## Function Design

**Size:**
- Functions typically 1-50 lines
- Component functions may be 50-150 lines when rendering logic is included
- Long functions broken into sub-components (like `Fade` component inside `SessionView`)

**Parameters:**
- Destructured props in components - `({ appConfig }: AppProps)`
- Destructured options objects in utility functions - `(options: { logLevel?: LogLevel; enabled?: boolean } = {})`
- Optional parameters with default values - `isAgentAvailable = false`, `onSend = async () => {}`
- Type-safe parameters with explicit interfaces

**Return Values:**
- React components return JSX (never null in render)
- Utility functions return typed values (Promise<T>, T, etc)
- Functions always return on success path, use early returns for error cases
- Error functions throw with `new Error('descriptive message')`

**Example function patterns:**

```typescript
// Utility function with typed parameters and return
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Async function with error handling
export async function POST(req: Request) {
  try {
    // validation and processing
    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

// Component with props destructuring
export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
```

## Module Design

**Exports:**
- Named exports for components and utilities - `export function App()`, `export const SessionView`
- Single default export rarely used (except in Next.js route handlers)
- Interface/type exports grouped at top - `export interface AppConfig`
- Re-exports used in barrel patterns (component directories would use `index.ts` if organized that way)

**Example export patterns:**

```typescript
// app-config.ts - Type then constant export
export interface AppConfig { ... }
export const APP_CONFIG_DEFAULTS: AppConfig = { ... }

// lib/utils.ts - Named exports for utilities
export const CONFIG_ENDPOINT = ...
export const SANDBOX_ID = ...
export interface SandboxConfig { ... }
export function cn(...inputs: ClassValue[]) { ... }
export const getAppConfig = cache(async (...) => { ... })
```

**Barrel Files:**
- Not extensively used in current structure
- Components are imported directly with their full paths (`@/components/app/app`)
- Potential for barrel files in deeply nested component directories

**Separation of Concerns:**
- API logic in `/app/api/` - `route.ts` for connection-details endpoint
- Components in `/components/` - UI logic and rendering
- Utilities in `/lib/` - Shared functions (config, styling, token generation)
- Hooks in `/hooks/` - Custom React hooks
- App configuration in root-level files - `app-config.ts`

---

*Convention analysis: 2026-02-23*
