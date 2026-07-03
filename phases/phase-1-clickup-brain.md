# Phase 1 — ClickUp-native AI (Brain + Super Agents)

Objective: run ClickUp's own AI against the exact same three accounts the
Radar analyzed, and capture an honest comparison. This phase is mostly in
Josh's browser; Claude's job is preflight, debrief, and notes.

Interview relevance: "I built the roll-your-own version, then ran ClickUp's
native AI on identical data" — a comparison almost no other candidate has.

## Handoff from previous phase (context to load)

- Radar v2 works: structured output (pydantic schema on Vertex), rubric-based
  health colors, evidence required per risk, runtime list discovery.
- Calibration verified: Acme 🔴 / Beta 🔴 / Gamma 🟢. Key learnings so far
  live in `clickup-notes.md` (schema-as-anti-hallucination, rubric bugs,
  models abhor an empty risks list, fabrication-vs-judgment line, Josh's
  risk-posture counterpoint on the Gamma flag).
- Decision made: leave the "empty risks list" prompt lever unfixed as a
  human-in-the-loop exhibit.
- The Enterprise trial workspace is confirmed accessible; whether its trial
  includes Brain/Super Agents is UNVERIFIED — that recon is step 1 below.

## Preflight (Claude, before any changes)

- Read `clickup-notes.md` and `git log --oneline -5`.
- Do not modify radar code in this phase unless Josh asks; the comparison
  needs a stable baseline.
- If Josh reports a paywall: stop, do not suggest entering payment. The
  packaging observation itself goes in the notes.

## Steps

### 1. Recon — does the trial include AI? (Josh, browser, ~10 min)
- Look for a Brain / AI entry point (toolbar, top-right, command bar) and an
  Agents area (sidebar, Space settings: "Agents" / "Autopilot Agents").
- Outcome A: AI available → continue. Outcome B: upsell dialog / locked →
  record exactly what's gated and stop this phase; that's a finding.

### 2. Head-to-head on Beta Inc (Josh, ~15 min)
- Open the Beta Inc Renewal list. Ask Brain, as close to our prompt as the
  UI allows: "Assess the health of this engagement. Green, yellow, or red?
  Top risks? Single best next action?"
- Save the answer VERBATIM (paste into a scratch note or straight into
  `clickup-notes.md` under a "Brain raw output" heading).
- Repeat on Gamma (the healthy control) if quick: does Brain say "healthy"?

### 3. Build a Super Agent (Josh, ~30 min)
- Try the services-relevant ones ClickUp promotes: follow-up email drafter or
  engagement health summarizer. Catalog first; natural-language setup if no
  catalog template; manual config as fallback. Note which setup paths exist.
- Watch the governance surfaces: what permissions did it request? Is there an
  approval/review mode? An activity log of agent actions?

### 4. Debrief (Josh + Claude, ~20 min)
- Josh pastes Brain's outputs and gut reactions into the session.
- Claude leads the comparison against radar2's reports on the same data:
  - Where Brain wins (lives inside the data: comments, docs, history we
    never exported; zero setup; no code).
  - Where the Radar wins (controllable rubric, enforced schema, evidence
    field, portable to any LLM, versioned in git).
  - Calibration: did Brain give health colors consistently? Could you tell
    WHY it concluded what it did?
- Claude updates `clickup-notes.md` with the comparison and fills in the
  handoff section below.

## Friction to watch for
- Feature names drift fast (Brain / AI / Autopilot / Super Agents) — hunt by
  concept, not exact name; note renames.
- Trial gating: which AI features exist vs. which are locked.
- Setup-quality dependence: does Brain's answer quality visibly depend on how
  well-structured the List is? (Our data is clean; a real client's isn't.)

## Definition of done
- Brain's verbatim output on Beta (and ideally Gamma) captured.
- At least one Super Agent built OR the exact blocker documented.
- Comparison written into `clickup-notes.md`.
- Handoff section below filled in; PLAN.md status updated; committed.

## Handoff to next phase (fill in at phase end)
- Key learnings:
- Decisions made:
- Open questions carried forward:
