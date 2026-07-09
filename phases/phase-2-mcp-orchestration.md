# Phase 2 — Claude + the official ClickUp MCP server

Objective: connect Claude Code to ClickUp's official MCP server and drive
real workspace actions by natural language — then articulate the difference
between script-orchestrated AI (the Radar) and model-orchestrated AI (MCP).
This ports Josh's existing Miro-MCP experience to ClickUp.

Interview relevance: the architectural distinction (who decides which API
calls happen — your code, or the model) is THE current applied-AI divide,
and Josh will have built both sides.

## Handoff from previous phase (fill from phase 1 before starting)

Carried forward 2026-07-08 (full detail in `clickup-notes.md`, "Phase 1"
section, and in phase 1's handoff):

- **The comparison baseline now has THREE systems, not two:** radar2
  (schema-enforced, ours), Brain chat (freeform, scope = cursor position),
  and Sentinel Sam (agent, template-shaped output). MCP-Claude is the
  fourth column. The three-system table lives in `clickup-notes.md`.
- **The money result to test against:** on Gamma (healthy control), Brain
  chat said YELLOW, Sentinel Sam (template contains "don't invent
  problems") said clean GREEN, radar2 said GREEN + one manufactured risk.
  Experiment 3 ("which account needs attention?") should note where
  MCP-Claude lands on Gamma — its prompt is whatever WE type, so we hold
  the empty-risks lever this time.
- **Brain's data-position advantage:** it caught zero-assignees, which our
  assignee-blind export structurally couldn't. Watch whether MCP tools
  expose assignee data — MCP-Claude's "export" is whatever the tool
  responses contain, so the same silent-filter lesson applies to ClickUp's
  tool design instead of our code.
- **Control contrast to extend:** Sentinel Sam's instructions were readable
  but NOT editable; radar2's prompt is ours in git. MCP sits between:
  prompt is ours, but tool selection/ordering is the model's. That's the
  exact "who orchestrates" boundary this phase exists to demonstrate.
- **Governance thread to continue:** ClickUp agent governance was opt-out
  (live in 60s, controls post-hoc, memory ON by default). Note what the
  MCP OAuth screen asks for up front (scopes, workspace selection) —
  consent-BEFORE vs ClickUp's inspect-AFTER is a talking point.
- **Open questions worth probing via MCP if convenient:** Agents' in-app
  Activity log (real audit trail?); whether MCP exposes agent/Brain
  features at all or only core objects (tasks/lists/docs).
- **Data caveat for cross-checks:** dates keep drifting (every system
  graded on a different day → different overdue counts). When
  cross-checking experiment 1 against radar2, re-run radar2 the same day.

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
  - All three experiments ran (from the DESKTOP session, not the
    terminal — local-scope MCP config made the connection visible to
    every session in the project folder once Josh OAuth'd in the CLI).
  - Full findings in `clickup-notes.md` Phase 2 section. Headlines:
    OAuth consent is a workspace picker with zero scope disclosure
    (51 tools incl. delete granted invisibly); vendor tool-descriptions
    are a third orchestration author (they steered call plans, embedded
    ask-the-user governance, and once lied — "me" assignee rejected
    despite documented support; model self-healed in one round-trip);
    the model-orchestrated export boundary adapts per run (missed
    descriptions in exp 1, self-corrected in exp 3) — flexible AND
    unauditable; radar2 structurally can't answer ranking questions
    (no rank field in schema) while MCP-Claude and Brain both said
    "Beta first" conversationally.
  - Two asterisks now on radar2's reproducibility claim: the date is an
    input (Gamma flipped GREEN→YELLOW on clock alone), and severities
    jitter between same-day runs (schema guarantees shape, not
    judgment).
  - Echo-loop observed live: radar recommended escalation → MCP-Claude
    created the task (description written from the radar's own report)
    → radar's next run cited that task as evidence and recommended
    completing it. AI output became AI input in one cycle.
- Decisions made:
  - Used the official server (`mcp.clickup.com/mcp`) via CLI
    `claude mcp add`, local scope. CLI had to be installed first
    (native installer — desktop app ships no terminal command).
  - Experiment 2's task (86bauv9fq) left in place, assigned to Josh —
    it's now real workspace data and the radar already keys on it.
  - Kept every write behind explicit Josh approval (the platform's own
    tool descriptions ask for exactly this — validating the phase rule).
- Open questions carried forward:
  - Phase 3's Cloud Run/Scheduler plan should note the identity gap:
    MCP is per-user OAuth (acts-as-Josh); unattended pipelines still
    need the token+REST pattern — that's radar2's structural niche.
  - Agents' in-app Activity log still never inspected (carried from
    Phase 1).
  - Untried: MCP access to Docs/Chat/time-tracking tools; whether other
    MCP hosts (claude.ai connector version) expose the same 51 tools.
