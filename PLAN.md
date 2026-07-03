# Project plan — ClickUp Health Radar

Goal: genuine hands-on experience with agentic AI around ClickUp, producing
(1) interview talking points in `clickup-notes.md`, (2) a portfolio artifact,
(3) GCP/AI-API skills breadth. Interview is the deadline that matters:
**Phases 1 and 2 before the interview; Phase 3 can continue after.**

Governing rule: build to friction. Each piece is done when it has produced
an authentic observation, not when it's polished.

## Status

| Phase | Scope | Status |
|---|---|---|
| 0–2 (done) | GCP setup, seeded workspace, radar v1 free-text, radar v2 structured output, calibration control | ✅ Complete |
| 1 | ClickUp-native AI: Brain + Super Agents on the same data | 🔜 In progress (Josh's browser homework assigned) |
| 2 | Claude + official ClickUp MCP server; orchestration comparison | ⬜ Not started |
| 3 | GCP productionization (Secret Manager, Cloud Run, Scheduler, BigQuery) + final capture/retro | ⬜ Not started |

## Phase files (detailed actions live there)

- `phases/phase-1-clickup-brain.md` — their AI vs. our Radar, head-to-head
- `phases/phase-2-mcp-orchestration.md` — model-orchestrated vs script-orchestrated
- `phases/phase-3-gcp-productionize-and-wrap.md` — optional GCP modules + retro

Each phase file contains: preflight checks for Claude, step-by-step actions
split "Josh does" / "Claude does", friction to watch for, definition of done,
and a handoff section filled in at phase end.

## The three-way comparison this project exists to produce

| | Radar (built) | ClickUp Brain (Phase 1) | Claude via MCP (Phase 2) |
|---|---|---|---|
| Who orchestrates | Our Python script | ClickUp's platform | The model itself |
| Where AI runs | Vertex AI (our GCP) | ClickUp's stack | Claude |
| Control | Full (prompt, schema, rubric) | Their knobs | Prompt-level |
| The question | — | What do we gain/lose vs roll-your-own? | What changes when the model picks the API calls? |
