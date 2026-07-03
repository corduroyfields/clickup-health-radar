# ClickUp Health Radar — project instructions for Claude

AI engagement-health tool: ClickUp API → Python → Gemini on Vertex AI.
Built by Josh as interview prep (ClickUp Senior TAM, Strategic Services) and
as a portfolio artifact. The most important deliverable is `clickup-notes.md`
— honest friction points and observations, which become interview talking
points.

## Session start ritual (do this before any changes)
1. Read `PLAN.md` for the roadmap and current phase status.
2. Read the current phase file in `phases/` — including the "Handoff from
   previous phase" section at the top.
3. Read `clickup-notes.md` to know what's already been observed.
4. Run `git log --oneline -5` and `git status` to see where work stopped.

## Working agreement (how Josh wants to work)
- **Josh drives, Claude navigates.** Josh runs every terminal / gcloud / git
  command himself and pastes output back. Claude writes Python and explains
  it. Never run commands for him that he could run to learn.
- **Teach for a student, not an engineer.** Define every term on first use.
  Plain language, short sentences, always explain *why*. No "just do X."
- **Build to friction.** Build each piece only until it produces an authentic
  observation, note it in `clickup-notes.md`, move on. No polishing.
- **Check before changing:** read a file before editing it; verify current
  IDs/names against live APIs rather than assuming; before enabling any new
  GCP service, state expected cost and flag anything that could exceed ~$5.
- **Secrets:** ClickUp token lives in `.env` (git-ignored). Never print,
  `cat`, or commit it. Verify secrets by length or by using them, never by
  displaying them.
- **Guardrails:** no payment entry without stopping to ask; OAuth/approvals
  are surfaced to Josh, never worked around; throwaway test data only.

## Phase-end ritual
1. Fill in the "Handoff to next phase" section at the bottom of the current
   phase file (key learnings + decisions made).
2. Update the status table in `PLAN.md`.
3. Make sure new observations landed in `clickup-notes.md`.
4. Commit everything.

## Key facts (verify against live systems if anything fails)
- GCP project: `clickup-health-radar`, region `us-central1`, billing linked.
  APIs enabled: `aiplatform`, `secretmanager`. Model: `gemini-2.5-flash`.
- ClickUp workspace ("team") ID: `90141353314` (Enterprise trial,
  "Joshua White's Technical Assessment Workspace"). Space: "Client Accounts"
  with three Lists: Acme Corp Onboarding (troubled onboarding), Beta Inc
  Renewal (troubled renewal), Gamma LLC Steady State (healthy control).
  Re-running `seed_workspace.py` rebuilds the Space (idempotent; IDs change,
  radar discovers lists at runtime).
- Python via uv (3.12). Run things with `uv run python <file>`.
- Files: `main.py` (auth smoke test), `seed_workspace.py` (test data),
  `radar.py` (v1, free-text + shared plumbing), `radar2.py` (v2, structured
  output — the current best version), `clickup-notes.md` (the deliverable).
