# Phase 4 — a front-end for the Radar

Objective: put a human-facing face on the radar's BigQuery history — turn
`radar.health_reports` rows into something a TAM (or an interviewer) can
*look at*: current portfolio health, trend over time, risks with evidence.

Status: post-interview enhancement phase. The radar itself is complete and
running unattended (see phase 3 handoff); this phase is additive and can be
dropped or paused at any point without affecting what's deployed.

## ⚠️ Session kickoff ritual (Claude: do this FIRST, before ANY design or code)

This phase was deliberately scoped WITHOUT deciding what the front-end is.
Josh explicitly asked to be interviewed about it at the start of the next
session. So, after the standard session-start ritual (CLAUDE.md), the first
action of the phase is a REQUIREMENTS INTERVIEW — ask Josh, one topic at a
time, and listen before proposing anything:

1. **Audience & moment:** who is looking at this, and when? (Josh demoing in
   an interview? A pretend-TAM starting their morning? A pretend-exec
   glancing weekly?) The audience decides everything downstream.
2. **Form:** what should it feel like — a read-only dashboard? An
   interactive explorer (filter by account, click into risks)? A daily
   digest/report? Something else he has in mind?
3. **Function (the questions it answers):** rank what matters — current
   colors at a glance? Trend lines over time? Risk detail with evidence?
   The jitter/error-bar story made visible? Portfolio vs single-account?
4. **Effort & learning appetite:** is this a half-day artifact or a
   multi-day build? And which does Josh want more from this phase —
   a polished demo, or maximum new-concept learning (they pull in
   different directions)?
5. **Hosting posture:** private on-laptop, or deployed/shareable (a URL he
   can open in an interview)? Cost and auth complexity follow from this.

Only AFTER those answers: propose 2–3 approaches with honest trade-offs and
let Josh choose. Do not pre-decide the stack. Candidate space to draw from
(each teaches different things — present costs and concepts, not hype):

- **Looker Studio** — zero code, connects straight to BigQuery, drag-and-drop
  charts. Teaches: BI-tool thinking, semantic fields. Fastest demo, least
  learning depth. ~$0.
- **Streamlit (Python)** — Josh has prior experience (glean-cockpit). A
  Python script becomes a web app; reads BigQuery via ADC. Teaches: charts
  in code, BigQuery client reads, and (if deployed) Cloud Run *services* —
  the sibling of the jobs we already know. ~$0 locally; pennies deployed.
- **No-build vanilla HTML/JS + small Python API** — most learning about how
  the web actually works (frontend/backend split, endpoints we design).
  Slowest to polish. NOTE: **Node.js is NOT installed** on this machine and
  that's a deliberate environment constraint — no npm/React toolchains
  unless Josh explicitly opts into installing Node.

## ✅ Spec — decided in the kickoff interview (2026-07-13)

- **Audience:** interviewer watching Josh demo (primary viewer), but the
  screen is *designed for* a CSM/AE persona doing account health checks.
  Equal-weight goal: hands-on builder reps for Josh.
- **Form:** interactive explorer — portfolio overview, click an account
  to drill in.
- **Function (priority = build order, stop at friction):**
  1. Current portfolio at a glance (today's color + risk count per account)
  2. Trend over time (health across runs — show the jitter story honestly)
  3. Risk detail with evidence (per-account drill-down)
  - Cut: "what changed between runs" diff view.
- **Effort:** learning-first, ~2–3 sessions. No known interview date.
- **Hosting:** deployed as a Cloud Run *service* with a URL Josh can open
  in an interview. Read-only service account (the phase's IAM lesson).
- **Stack:** vanilla HTML/JS frontend + small Python API (FastAPI) — chosen
  over Streamlit (fewer new concepts; Josh already used it) and Looker
  Studio (no building = fails the purpose). **Fallback agreed:** if session
  2 ends without a demoable screen, port the view layer to Streamlit — the
  API/BigQuery work transfers.
- **Build sequence (one layer at a time):** API alone first, tested with
  `curl` → HTML page that fetches it → chart/drill-down → deploy.
- Glossary queue for /retro: web *service* vs *job*, frontend/backend
  split, endpoint, JSON API, UI state, chart library, window function.

## 🎓 Coaching contract for this phase (Claude: hold yourself to it)

Josh asked for DEEP education and coaching this phase. Concretely:
- Follow the CLAUDE.md working agreement strictly (Josh drives, Claude
  navigates; Josh runs every command; define every term on first use).
- Prefer the option that teaches durable concepts over the option that
  demos fastest — unless Josh's interview timeline says otherwise (ask).
- For every design choice, present the "why" and the alternative that was
  rejected — in student terms, before code is written.
- Introduce front-end concepts as first-class glossary material (this
  project's first UI work): e.g. what a chart library is, what a web
  *service* is vs the *jobs* we've built, what "state" means in a UI,
  query→view data flow. Queue new terms for the eventual /retro update.
- Keep the build-to-friction rule: each piece is done when it produced an
  authentic observation (there's a "Phase 4" section waiting to be started
  in `clickup-notes.md`).

## Handoff from previous phase (phase 3 / project wrap, 2026-07-09)

- **What exists to build on:** BigQuery table
  `clickup-health-radar.radar.health_reports` — columns: run_time
  (TIMESTAMP), client (STRING), health (STRING), justification (STRING),
  risk_count (INTEGER), risks (JSON: summary/severity/evidence_tasks per
  risk), next_action (STRING). The Cloud Run job `radar-sweep` appends 3
  rows every weekday at 8am ET via Cloud Scheduler. All in `us-central1`.
- **The data has a story the front-end should tell honestly:** verdict
  jitter exists and peaks at rubric boundaries (see notes, Module D/E) —
  a good front-end shows trends/consecutive changes, not just today's
  color. Post-Module-E, risk_count is meaningful (0 = clean).
- **Expected upstream failure:** the ClickUp Enterprise trial will expire
  at some point → the radar job will start logging 401s and stop appending
  rows. THE FRONT-END STILL WORKS — it reads accumulated BigQuery history,
  not ClickUp. That decoupling is itself a teaching point (and the 401s in
  Cloud Logging are a worthwhile "how agents fail" observation to capture
  when noticed).
- **Identity thread continues:** a front-end reading BigQuery needs an
  identity too. Local Streamlit = Josh's ADC; deployed service = a service
  account with `bigquery.dataViewer`-ish read-only role (note: the radar's
  robot has dataEditor — the front-end should NOT reuse it; least
  privilege, reads only). Looker Studio = Google handles it. Whatever the
  choice, it's the phase's IAM lesson.
- **Cost guardrails carry over:** state expected cost before enabling
  anything new; everything in the candidate space is free-tier/pennies at
  this scale; flag anything that could exceed ~$5. BigQuery reads on this
  table are KBs — effectively free.
- **Interview context:** interview stage 1 (2026-07-09) went well — Josh
  demoed the live radar on the call. ≥2 stages remain; a visual front-end
  is a natural stage-2+ demo upgrade. Ask Josh about timeline pressure in
  the kickoff interview (it affects the form/effort answer).

## Preflight (Claude, before any changes)

- Standard ritual: PLAN.md, this file top to bottom, `clickup-notes.md`,
  `git log --oneline -5`, `git status`.
- Verify the BigQuery table still exists and has fresh rows
  (`bq query` — Josh runs it): if rows stopped, check whether the ClickUp
  trial expired (expected!) before debugging anything.
- Confirm environment facts before proposing stacks: Node still absent?
  (`node --version`) — do not assume.

## Definition of done

Whatever form/function Josh chooses in the kickoff interview — captured as
a short spec at the top of this phase's work, built to friction, observed
honestly in `clickup-notes.md`, committed. Plus the phase-end ritual
(handoff below, PLAN.md row, notes, commit).

## Handoff (fill in at phase end)
- Key learnings:
- Decisions made:
- Open questions:
