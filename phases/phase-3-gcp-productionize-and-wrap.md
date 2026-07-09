# Phase 3 — GCP productionization + final capture

Objective: turn the Radar from "script I run by hand" into "service that runs
itself," collecting the GCP breadth Josh wants (bonus points: AI/API tools) —
then close the project with the retro and interview synthesis.

Timing: this phase is OPTIONAL for the interview and safe to continue after
it. Modules are ordered by value-per-hour; stop anywhere. The wrap-up
(module W) is NOT optional — do it whenever the project ends.

## Handoff from previous phase (fill from phase 2 before starting)

Carried forward 2026-07-08 (full detail in `clickup-notes.md`, Phase 2
section, and in phase 2's handoff):

- **The identity gap is Phase 3's reason to exist.** MCP is per-user OAuth
  (acts-as-Josh, interactive); an unattended pipeline needs its own
  credentials — the token+REST pattern radar2 uses. Cloud Run + Scheduler
  is that niche made real: a service account (robot identity) holding the
  ClickUp token, no human in the loop. Sentinel Sam's "Scheduled trigger"
  button is the platform version of the same idea; Module B/C is the
  roll-your-own version, and the comparison belongs in the notes.
- **Four-system comparison is done and captured:** radar2 (schema contract,
  deterministic scope, assignee-blind), Brain chat (full data model,
  freeform, scope = cursor), Sentinel Sam ("don't invent problems" →
  cleanest Gamma calibration), MCP-Claude (model-orchestrated, adaptive and
  unauditable export boundary, self-healed a broken tool contract).
- **Reproducibility has two asterisks now:** the date is an input (Gamma
  flipped GREEN→YELLOW on clock alone — verdict = f(data, rubric, clock)),
  and severities jitter between same-day runs (schema guarantees shape,
  not judgment). Module D's trend table will make both visible as data:
  day-over-day color changes need reading with error bars in mind.
- **Echo-loop on record:** radar recommended escalation → MCP-Claude
  created the task (86bauv9fq, description synthesized from the radar's
  own report) → radar now cites it as evidence. That task is live
  workspace data; scheduled daily runs will keep re-ingesting AI-authored
  content. Relevant to Module E and the wrap-up's human-in-the-loop story.
- **Module E's lever is already vendor-validated:** ClickUp's own agent
  template ships "don't invent problems," and Sam produced the only clean
  green. Adding the empty-risks instruction to radar2 tests the same lever
  on our side of the fence.
- **Workspace state:** experiment 2's escalation task remains in Acme
  (assigned to Josh — the only assigned task in the Space). Re-seeding
  would delete it; avoid re-running `seed_workspace.py` unless accepted.
- **Open questions still carried:** Agents' in-app Activity log never
  inspected; MCP Docs/Chat/time-tracking tools untried; whether the
  claude.ai connector exposes the same 51 tools.

## Preflight (Claude, before any changes)

- Read `clickup-notes.md`, `git log --oneline -5`, and the handoff above.
- Before enabling ANY new GCP API: state what it is, why, and expected cost.
  Everything below fits free tier / pennies at this usage; flag anything that
  wouldn't. Josh runs all gcloud commands himself.
- Check current code state before editing (radar2.py is the live version).

## Modules (in recommended order)

### Module A — Secret Manager (~30 min, quick win)
Move the ClickUp token out of `.env` into GCP Secret Manager.
- Teach: what a secret manager is vs an env file (central storage, IAM
  access control, versioning, audit log — the enterprise answer to "where
  do keys live?").
- Josh: `printf` the token into `gcloud secrets create clickup-api-token
  --data-file=-` (pipe, never paste into a command line argument), verify
  with a length-only accessor call.
- Claude: update the code to try Secret Manager first (via
  `google-cloud-secret-manager` + ADC), fall back to `.env` locally.
- Note the friction: IAM roles needed, the "grant your own account
  secretAccessor" moment.

### Module B — Cloud Run Job (~1–2 hr, the big one)
Deploy the Radar as a **Cloud Run Job** (container that runs to completion on
demand — the right shape for a batch sweep; a web service would be the wrong
tool and cost more).
- Teach: what a container is; `gcloud run jobs deploy --source .` builds the
  container in the cloud (Cloud Build) — no local Docker needed.
- Requires enabling: `run.googleapis.com`, `cloudbuild.googleapis.com`,
  `artifactregistry.googleapis.com` (all free-tier friendly at this scale).
- Gotcha to expect: the job's service account needs Secret Manager accessor
  + Vertex AI user roles — teach service accounts here (a robot identity for
  code running in the cloud, vs Josh's ADC on his laptop).
- Definition of done: `gcloud run jobs execute radar-sweep` produces the
  three health reports in Cloud Logging.

### Module C — Cloud Scheduler (~30 min)
Make it a real radar: run the job automatically every weekday morning.
- Teach: cron syntax; Scheduler → Cloud Run Job trigger wiring.
- Free tier: 3 jobs. Effectively $0.
- This is the "agentic" claim made honest: software acting on a schedule
  without a human pressing enter.

### Module D — BigQuery trend history (~1–2 hr)
Append each run's structured reports (thank you, pydantic schema) as rows;
query health over time.
- Teach: dataset/table creation, one `INSERT` per report from the job,
  a first SQL query ("show me Beta's health color by day").
- This is where structured output pays off visibly: free text could never
  become rows.
- Stretch: a Looker Studio dashboard over the table (pure clicking, no code).

### Module E (stretch) — prompt levers
Only if curious: add the "return an empty risks list if none" instruction and
watch Gamma's manufactured risk disappear/persist; try a stricter rubric.
Document whichever way it goes.

### Module W — wrap-up (NOT optional)
1. Finalize `clickup-notes.md`: adoption crawl-walk-run for a skeptical
   strategic account; where it shines; where clients get stuck; the limits
   (human-in-the-loop moments); the three-way comparison (Radar vs Brain vs
   MCP); the Miro paragraph.
2. Interview synthesis: Claude drafts a one-page "talking points" distillation
   from the notes — 5-6 stories, each with the observation and the senior
   takeaway. Josh edits it into his own words.
3. Run `/retro` to write the student-facing article into `~/knowledge/`
   (glossary links for: API endpoint, HTTP verbs, headers, JSON, idempotency,
   ADC, structured output / schema, MCP, service account, container, cron).
4. Teardown decision: keep the GCP project (pennies) or delete it
   (`gcloud projects delete clickup-health-radar`) — Josh's call. ClickUp
   trial workspace: leave as-is; it expires on its own.
5. Final commit; update PLAN.md to all-green.

## Definition of done
Wrap-up module complete. Everything else is optional by design.

## Handoff (fill in at project end)
- Key learnings:
- What would we do differently next project:
