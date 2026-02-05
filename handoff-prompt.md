# Handoff Prompt

**Purpose**: Transfer context to another coding agent with zero information loss.

---

## Handoff Tool Definition

```json
{
  "name": "handoff",
  "description": "Create a comprehensive context summary for handoff to another coding agent. Generate a detailed summary of the current session, capturing all technical details, decisions, and progress. The receiving agent will rely solely on this summary to continue the work.",
  "input_schema": {
    "type": "object",
    "properties": {
      "context": {
        "type": "string",
        "description": "Complete handoff context following the structured format below."
      }
    },
    "required": ["context"]
  }
}
```

---

## Handoff Context Format

When generating handoff context, structure it EXACTLY as follows:

### 1. Current Work
Describe what was being worked on. Be specific about the most recent actions and state. Include:
- The overall goal/task
- What phase the work is in (research, planning, implementation, debugging, etc.)
- The most recent actions taken

### 2. Key Technical Concepts
List all relevant technical context:
- Technologies and frameworks in use
- Coding conventions and patterns established
- Architectural decisions made and their rationale
- Constraints or requirements to respect

### 3. Relevant Files and Code
Enumerate files examined, modified, or created. For each:
- File path and purpose
- Key code sections with snippets where they add clarity
- State of changes (modified, created, needs modification)

Format:
```
- `path/to/file.ts`: [purpose]
  - [key details]
  - Relevant snippet:
    ```typescript
    // code here
    ```
```

### 4. Problem Solving
Document the problem-solving journey:
- Issues identified and how they were resolved
- Ongoing troubleshooting (what's been tried, what hasn't)
- Blockers encountered and workarounds applied

### 5. Pending Tasks and Next Steps
**CRITICAL**: This section requires VERBATIM QUOTES from the conversation.

For each pending task:
- Task description
- Direct quote from conversation: `"[exact user request or discussion verbatim]"`
- Specific next steps to complete
- Any decisions still needed from user

### 6. Files to Load (Optional)
List files the receiving agent should read immediately:
```
- path/to/critical-file.ts
- path/to/config.json
```

---

## Instructions for Generating Handoff

1. **Be Comprehensive**: The receiving agent has NO prior context. Everything needed must be in this summary.

2. **Use Verbatim Quotes**: For user requests and decisions, quote exactly. This prevents information loss and misinterpretation.

3. **Show Only What Matters**: Include code snippets that add clarity, but don't dump entire files. Focus on changes and key sections.

4. **Be Unambiguous**: The receiving agent will rely solely on your summary. Avoid ambiguous language. Be explicit about:
   - What was done vs. what needs to be done
   - What is confirmed vs. what is assumed
   - What is working vs. what is broken

5. **Capture Technical Decisions**: Include not just what was decided, but WHY. Rationale prevents the receiving agent from reconsidering settled decisions.

6. **Order Matters**: Recent work and next steps are most critical. Prioritize accordingly.

---

## Example Handoff

```markdown
# Handoff Context

## 1. Current Work
Adding user authentication to a Next.js application. Currently in implementation phase - basic JWT auth is working, now implementing refresh token rotation.

## 2. Key Technical Concepts
- **Stack**: Next.js 14, TypeScript, Prisma, PostgreSQL
- **Auth Pattern**: JWT with httpOnly cookies, refresh token rotation
- **Conventions**:
  - API routes in `app/api/`
  - Auth utilities in `lib/auth/`
  - All tokens use RS256 signing
- **Decision**: Using cookies over localStorage for XSS protection (user approved)

## 3. Relevant Files and Code
- `lib/auth/jwt.ts`: Token generation and verification
  - Tokens expire in 15 minutes
  - Refresh tokens expire in 7 days
  ```typescript
  export const generateTokens = (userId: string) => {
    const accessToken = jwt.sign({ userId }, privateKey, { expiresIn: '15m' });
    const refreshToken = jwt.sign({ userId, type: 'refresh' }, privateKey, { expiresIn: '7d' });
    return { accessToken, refreshToken };
  };
  ```

- `app/api/auth/refresh/route.ts`: Refresh endpoint (IN PROGRESS)
  - Currently returns new access token
  - NEEDS: Refresh token rotation logic

- `prisma/schema.prisma`: User model complete, RefreshToken model added

## 4. Problem Solving
- **Resolved**: Cookie not being set - fixed by adding `sameSite: 'lax'`
- **In Progress**: Refresh token rotation - need to invalidate old token on use
- **Tried**: Storing refresh tokens in memory (rejected - doesn't persist across restarts)

## 5. Pending Tasks and Next Steps
1. **Complete refresh token rotation**
   - User request: `"make sure when a refresh token is used, it gets invalidated and a new one is issued"`
   - Next: Add database call to invalidate old refresh token in `refresh/route.ts`

2. **Add logout endpoint**
   - User request: `"we'll also need a logout that clears all tokens"`
   - Next: Create `app/api/auth/logout/route.ts` that invalidates all user refresh tokens

3. **Test the full flow**
   - User request: `"once refresh is working, let's test the full login -> refresh -> logout flow"`

## 6. Files to Load
- lib/auth/jwt.ts
- app/api/auth/refresh/route.ts
- prisma/schema.prisma
```


---

## Anti-Patterns to Avoid

❌ **Don't summarize user requests** - Quote them exactly
❌ **Don't include entire files** - Only relevant snippets
❌ **Don't assume the receiver knows anything** - Be explicit
❌ **Don't skip the "why"** - Include rationale for decisions
❌ **Don't bury next steps** - Make them prominent and clear
❌ **Don't forget file paths** - Always include full paths

---

## When to Generate Handoff

Use this handoff format when:
- Starting a new conversation/thread with another agent
- Context window is filling up and work needs to continue
- Switching between different AI assistants
- Pausing work to resume later
- Delegating part of a task to a specialized agent