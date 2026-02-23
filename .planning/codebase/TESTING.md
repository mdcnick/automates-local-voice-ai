# Testing Patterns

**Analysis Date:** 2026-02-23

## Test Framework

**Runner:**
- Not configured - No testing framework detected in project

**Assertion Library:**
- Not applicable

**Test Infrastructure:**
- No Jest, Vitest, or other test runner installed
- No test scripts in `package.json`
- No test configuration files detected

**Current State:**
- Project has no automated testing setup
- `package.json` scripts: `dev`, `build`, `start`, `lint`, `format`, `format:check`
- No test-related dependencies in either `dependencies` or `devDependencies`

**Run Commands (Not Applicable):**
```bash
# No test commands configured
# Manual testing required for all features
```

## Test File Organization

**Location:**
- No test files present in codebase
- No `__tests__`, `.test.ts`, or `.spec.ts` files found

**Naming Convention:**
- No established naming pattern (no tests exist)
- Standard convention would likely be `[filename].test.ts` or `[filename].spec.ts`

**Structure:**
- No test directory structure established
- Suggested structure would mirror source structure:
  - `components/__tests__/` or `components/[component].test.tsx`
  - `hooks/__tests__/` or `hooks/[hook].test.ts`
  - `lib/__tests__/` or `lib/[module].test.ts`

## Test Structure

**Suite Organization:**
- Not applicable - no test framework in place

**Example of What Could Be Tested (from codebase):**

Component test example (if Jest/Vitest were configured):
```typescript
// Would test components/app/welcome-view.tsx
describe('WelcomeView', () => {
  it('renders welcome text and button', () => {
    // Test implementation
  });

  it('calls onStartCall when button is clicked', () => {
    // Test implementation
  });
});
```

Hook test example (if React Testing Library were configured):
```typescript
// Would test hooks/useAgentErrors.tsx
describe('useAgentErrors', () => {
  it('shows toast alert when agent fails', () => {
    // Test implementation
  });

  it('ends session after displaying errors', () => {
    // Test implementation
  });
});
```

**Patterns (Suggested Structure):**
- Setup: Jest/Vitest would need configuration
- Teardown: Standard test cleanup (unmounting, clearing mocks)
- Assertion: Assertion library would need selection (Jest built-in or Vitest)

## Mocking

**Framework:**
- Not configured - No mocking library in use

**Current Implementation Patterns in Code:**
The codebase uses dependency injection and context providers that would naturally support mocking:

```typescript
// From app.tsx - SessionProvider wraps the app
// Mocking would inject mock session via provider

// From hooks/useAgentErrors.tsx - Uses LiveKit context
// Mocking would provide mock agent state

// From lib/utils.ts - Uses process.env for configuration
// Environment variables can be mocked in tests
```

**What Would Need Mocking:**
- LiveKit services: `useSession()`, `useAgent()`, `useSessionContext()`
- API calls: `fetch()` for connection-details endpoint
- Environment variables: `process.env.NEXT_PUBLIC_*` variables
- Next.js features: `next/headers`, `next/navigation`

**Mock Implementation Example (if configured):**
```typescript
// Example mock for fetch in lib/utils.ts tests
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ /* mock config */ }),
  })
);

// Example mock for LiveKit context
const mockSession = {
  isConnected: true,
  end: jest.fn(),
};

// Example mock for environment variables
process.env.NEXT_PUBLIC_LIVEKIT_URL = 'ws://test:7880';
```

**What NOT to Mock (Based on Codebase Patterns):**
- React hooks: Use actual hooks, test behavior through component output
- Utility functions: Test in isolation, don't mock
- User interactions: Test actual click/form submission behavior
- Component rendering: Test actual rendered output, not implementation details

## Fixtures and Factories

**Test Data:**
- No fixtures currently exist
- Would be needed for:
  - AppConfig objects for component testing
  - LiveKit session data
  - Message/transcript data
  - User input data

**Example Fixture (if implemented):**
```typescript
// Would go in shared test utilities
export const mockAppConfig: AppConfig = {
  pageTitle: 'Test Agent',
  pageDescription: 'Test description',
  companyName: 'Test Company',
  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,
  logo: '/test-logo.svg',
  startButtonText: 'Start',
};

export const mockMessage = {
  from: { isLocal: true },
  text: 'Test message',
};
```

**Location:**
- Would typically be in `__tests__/fixtures/` or `__tests__/mocks/`
- Could also be in individual `[component].test.tsx` files if tests are co-located

## Coverage

**Requirements:**
- No coverage requirements enforced
- No coverage reporting configured
- No coverage thresholds in place

**View Coverage:**
- Not applicable - no test framework configured

## Test Types

**Unit Tests:**
- Would test individual functions and components in isolation
- Examples from codebase to test:
  - `lib/utils.ts`: `cn()`, `getAppConfig()`, `getSandboxTokenSource()`
  - Components: `Button`, `ChatInput`, `WelcomeView` rendering
  - Hooks: `useAgentErrors()`, `useDebugMode()`, `useInputControls()`

**Integration Tests:**
- Would test multiple components working together
- Examples from codebase:
  - App connection flow: SessionProvider → SessionView → AgentControlBar
  - Chat interaction: ChatInput → message sending → transcript update
  - Device selection: device change → preference persistence

**E2E Tests:**
- Not detected - No E2E framework configured
- Would likely test:
  - Complete user flow from page load to agent connection
  - Audio/video initialization
  - Chat message sending and receiving
  - Device switching

## Common Patterns

**Async Testing:**
- Current code uses async/await extensively
- Would need async test support from framework

**Example async pattern in codebase to test:**
```typescript
// From chat-input.tsx
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
```

**Async test pattern would be:**
```typescript
// Example with Jest/RTL (not currently in use)
it('sends message and clears input on submit', async () => {
  const onSend = jest.fn().mockResolvedValue(undefined);
  render(<ChatInput onSend={onSend} chatOpen={true} />);

  const input = screen.getByPlaceholderText('Type something...');
  fireEvent.change(input, { target: { value: 'hello' } });
  fireEvent.submit(screen.getByRole('button'));

  await waitFor(() => {
    expect(onSend).toHaveBeenCalledWith('hello');
    expect(input).toHaveValue('');
  });
});
```

**Error Testing:**
- Current code demonstrates error handling patterns with try-catch

**Example error handling to test (from lib/utils.ts):**
```typescript
try {
  if (!sandboxId) {
    throw new Error('Sandbox ID is required');
  }
  // ... fetch logic
} catch (error) {
  console.error('ERROR: getAppConfig() - lib/utils.ts', error);
}
```

**Error test pattern would be:**
```typescript
// Example test for error scenarios
it('returns default config on fetch error', async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

  const result = await getAppConfig(mockHeaders);

  expect(result).toEqual(APP_CONFIG_DEFAULTS);
});

it('throws when Sandbox ID is missing', async () => {
  process.env.NEXT_PUBLIC_APP_CONFIG_ENDPOINT = 'http://test';
  const headers = new Headers();

  await expect(getAppConfig(headers)).rejects.toThrow('Sandbox ID is required');
});
```

## Testing Recommendations

**Priority Areas to Test (Based on Risk):**
1. **Critical path**: `app/api/connection-details/route.ts` - Creates auth tokens, system will fail if broken
2. **State management**: `lib/utils.ts` - Config loading is used by all pages
3. **User interaction**: `components/livekit/agent-control-bar/chat-input.tsx` - Main user interface
4. **Error recovery**: `hooks/useAgentErrors.tsx` - Error handling affects user experience

**Suggested Setup:**
1. Install testing framework: Jest or Vitest (both support Next.js)
2. Install React testing library and required mocks
3. Create `jest.config.js` or `vitest.config.ts`
4. Add test scripts to `package.json`
5. Create `__tests__` directory structure
6. Start with unit tests for utilities and hooks

**Example Setup Commands (Not Currently Valid):**
```bash
pnpm add -D jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
# Then configure jest.config.js and add test scripts
```

---

*Testing analysis: 2026-02-23*
