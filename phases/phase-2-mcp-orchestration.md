# Phase 2 — Claude + the official ClickUp MCP server

Objective: connect Claude Code to ClickUp's official MCP server and drive
real workspace actions by natural language — then articulate the difference
between script-orchestrated AI (the Radar) and model-orchestrated AI (MCP).
This ports Josh's existing Miro-MCP experience to ClickUp.

Interview relevance: the architectural distinction (who decides which API
calls happen — your code, or the model) is THE current applied-AI divide,
and Josh will have built both sides.

## Handoff from previous phase (fill from phase 1 before starting)

- (carry forward phase 1's key learnings, especially anything about Brain's
  capabilities/gaps — MCP actions should probe the same territory)

## Hard requirements (read first)

- **Must run in an INTERACTIVE `claude` session**, launched from this project
  folder (`~/Projects/clickup-health-radar`) — the VS Code integrated
  terminal is fine. The OAuth flow cannot run in a non-interactive session.
- Use ClickUp's **official** server only: `https://mcp.clickup.com/mcp`.
  Not Composio or other third-party bridges — "I used ClickUp's own MCP
  server" is the stronger interview story.
- Josh performs the OAuth approval himself; Claude never works around auth.

## Preflight (Claude, before any changes)

- Confirm the session is interactive and in the project directory.
- Read `clickup-notes.md` and this file's handoff section.
- Verify the Space still exists (run `uv run python main.py` or ask Josh) —
  MCP experiments will act on the same test data.
- No destructive MCP actions (deletes, bulk edits) without Josh's explicit
  go-ahead per action.

## Steps

### 1. Connect (Josh, ~15 min)
- In the interactive session, run `/mcp` and add the ClickUp server
  (`https://mcp.clickup.com/mcp`), or from the shell:
  `claude mcp add --transport http clickup https://mcp.clickup.com/mcp`
  then `/mcp` to authenticate.
- Browser OAuth: Josh approves, watching WHAT scopes/permissions ClickUp
  requests (note them — that's governance material).

### 2. Three graduated experiments (Josh prompts, Claude-in-session executes)
Run these as natural-language requests, observing which MCP tools the model
chooses to call each time:
1. **Read:** "Summarize the open tasks in the Beta Inc Renewal list, most
   urgent first." → cross-check the answer against radar2's report.
2. **Write:** "Create a task in Acme Corp Onboarding: 'Send SSO escalation
   email to Acme exec sponsor', urgent priority, due in 2 days." → verify it
   appears in the ClickUp UI (and that the Radar picks it up on next run —
   it should raise Acme's risk picture).
3. **Judgment:** "Which of my three client accounts needs attention most
   urgently this week, and why?" → compare directly with the Radar's
   portfolio dashboard and with Brain's answer from phase 1.

### 3. Observe like an architect (Josh + Claude, throughout)
- Which tools did the model call, in what order? Did it ever call the wrong
  one or need correcting? How many round-trips for what radar2 does in one?
- Where's the boundary: what could MCP-Claude do that Brain couldn't, and
  vice versa? What could NEITHER do that the custom Radar could (schema,
  rubric, evidence enforcement)?
- Honest Miro comparison: one paragraph — how did ClickUp's MCP experience
  compare to the Miro MCP work (tool quality, auth, reliability, ergonomics)?

### 4. Capture (Claude)
- Write the script-vs-model orchestration comparison and the Miro paragraph
  into `clickup-notes.md`. Fill in the handoff section below.

## Friction to watch for
- OAuth hiccups, token/scope limits, rate limits.
- Tool-selection misses (model picks a wrong/suboptimal MCP tool) — these
  are gold for the "where agentic AI needs a human" talking point.
- Latency and cost of many small tool calls vs one scripted pipeline.

## Definition of done
- MCP connected via official server; all three experiments run.
- Task from experiment 2 visible in ClickUp UI.
- Comparison + Miro paragraph in `clickup-notes.md`.
- Handoff filled; PLAN.md updated; committed.

## Handoff to next phase (fill in at phase end)
- Key learnings:
- Decisions made:
- Open questions carried forward:
