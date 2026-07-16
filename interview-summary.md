# Interview summary — ClickUp Health Radar

A one-page distillation of `clickup-notes.md` for interview prep.
(Draft by Claude; Josh — rewrite anything you'd actually say out loud
into your own words. Especially the 60-second answer at the bottom.)

## What the project was

An AI **engagement-health radar** built against ClickUp's public API:
a Python agent on Google Cloud that sweeps a set of client accounts,
has Gemini (on Vertex AI) grade each one GREEN/YELLOW/RED against an
explicit rubric with schema-enforced structured output, and reports
risks with cited task evidence plus a recommended next action. By the
end it ran fully unattended — Cloud Run job, fired by Cloud Scheduler
every weekday at 8am ET, token in Secret Manager, every run appended
as rows to BigQuery for trend history.

Then the same scenario was run through **ClickUp's own AI stack** —
Brain chat, an autonomous agent ("Sentinel Sam"), and the official MCP
server driven by Claude — producing a four-system comparison of the
same accounts on the same data: roll-your-own vs. platform AI vs.
model-orchestrated.

## The scenario (who we impersonated)

Two perspectives at once — and the duality is the point:

- **The seat we sat in: a ClickUp customer.** The workspace is exactly
  what a customer-success / account-management team's would look like —
  a CSM running their book of client business in ClickUp. Every friction
  point, governance surprise, and trust question in the notes was
  experienced the way a *customer* experiences it: trial onboarding,
  half-configured workspace, one-click OAuth grants, agents that go
  live in 60 seconds.
- **The lens we judged with: a senior TAM / Strategic Services
  persona** — assessing engagement health, deciding escalations,
  grading the AI's judgment against what a senior human would say.

That combination is deliberate interview material: a ClickUp team
member's job is to understand the customer's experience from the
inside, and this project *is* that experience, documented honestly.

The three fictional accounts, each a deliberate test case:

- **Acme Corp** — troubled onboarding (blocked SSO, slipping go-live)
- **Beta Inc** — troubled renewal (departed champion, usage decline,
  support-ticket spike)
- **Gamma LLC** — healthy steady state (the calibration control — the
  account that ended up teaching us the most)

All data was planted, so we always knew the ground truth the AI was
being graded against.

## Why it was performed

1. **Interview prep with receipts:** genuine hands-on experience with
   agentic AI around ClickUp specifically — friction points observed
   first-hand, not read about.
2. **Portfolio artifact** on a deliberate AI-assisted learning path:
   the design-to-deployed-app workflow, done honestly.
3. **Skills breadth:** GCP (Vertex AI, Secret Manager, Cloud Run,
   Scheduler, BigQuery, IAM), API integration, prompt/schema design,
   MCP.

## Key learnings

- **We built both sides of the current applied-AI divide.** Platform AI
  (Brain/agents) has the better *data position* — zero setup, full data
  model, it caught things our export couldn't see. Roll-your-own has
  the better *contract* — owned prompt and rubric in git, output that
  physically can't be malformed, deterministic scope, and you can fix
  it when it's wrong (ClickUp's agent instructions were readable but
  not editable). Neither wins; knowing which one a use case needs is
  the actual skill.
- **Schema is a two-edged anti-hallucination lever.** Requiring an
  evidence field killed a fabricated claim; but required fields also
  *compel* content — a healthy account got manufactured risks because
  the list had to be filled. An explicit "empty list is valid"
  instruction fixed it — and we proved that with a measured A/B against
  BigQuery history, not a vibe. ClickUp's own agent template contains
  the same instruction ("don't invent problems"): vendor-grade
  confirmation the failure mode is real and prompt-patchable.
- **AI verdicts have error bars, and they're widest at the rubric
  boundary.** Same account, same data, same code: YELLOW and GREEN
  five minutes apart when a task sat near a threshold. The grading
  date is an input. Product implication: never alert on a single run's
  color — require consecutive changes or majority-of-N.
- **Governance defaults are opt-out everywhere.** ClickUp's agent went
  live in 60 seconds with memory on by default; MCP OAuth granted a
  51-tool surface (including delete) with no scope screen; GCP's
  default service account carries near-Owner Editor rights. In every
  system, the human review moment was supplied by our process, not by
  the platform.
- **Orchestration is a stack, not a binary.** Your code, the model,
  the vendor's tool descriptions (which steered behavior, embedded
  governance, and once simply lied), and host permissions all get a
  vote. Architecture is deciding which one gets the veto.
- **Human-in-the-loop is a specific list, not a slogan:** contested
  risk posture (models split exactly where senior humans split), echo
  loops (AI output became AI input in one cycle), write-review (models
  compose content, not just actions), and the last mile (the radar
  says "call the champion"; it can't call the champion).

## Phase 4 addendum — the front-end (built after stage 1)

An interactive explorer over the radar's BigQuery history, built by hand
with no frameworks: a FastAPI endpoint layer + vanilla HTML/JS/SVG.
Portfolio at a glance, per-run trend dots, click-to-expand risk detail
with cited evidence. Runs locally; demo takes one command. New talking
points it earned:

- **My dashboard's first catch was my own pipeline.** The prompt fix we
  had measured with an A/B (and celebrated) had never actually been
  redeployed — the cloud job ran the old prompt for four days. Logs
  showed nothing; *looking at the data* caught it in minutes. Lesson:
  a deploy is a snapshot, not a subscription — "fixed" and "shipped"
  are different states, and the gap between them is what CI/CD exists
  to close.
- **Chart design is risk communication.** One dot per run instead of a
  smoothed trend line; same-day disagreements left visible. The same
  table can tell a cleaner, less true story — the AI's error bars only
  exist if someone chooses to draw them. Whoever builds the dashboard
  decides what stakeholders believe about the AI's reliability.
- **Decoupling paid off as designed:** the explorer reads accumulated
  warehouse history, not ClickUp live — it keeps working even after the
  trial expires and the upstream agent starts failing.
- **The ending is a deliberate scope cut.** When the final interview
  landed, the remaining step (cloud-deploying the front-end) was cut:
  its value was learning, not demo, and the deadline that mattered was
  human. Shipping the three functions with demo value and documenting
  the cut honestly *is* the build-to-friction method, applied to
  the project itself.

## The 60-second answer: "Tell me about your AI agent experience"

High-level version (the default):

> I recently built and ran an AI agent end to end: every weekday
> morning, unattended, it grades the health of client accounts in
> ClickUp, flags risks with evidence, and recommends a next action.
> I built it from the customer's seat — a customer-success team's book
> of business — so I experienced ClickUp the way a customer does. Then
> I ran the same accounts through ClickUp's own AI and compared
> honestly: where the platform wins, where roll-your-own wins, where
> both still need a human. The lesson: making an agent act is easy —
> the real work is calibration, governance, and knowing which judgment
> calls stay human.

Optional technical add-on (one breath, only if they lean in):

> Under the hood it's Python on Google Cloud — Gemini with
> schema-enforced structured output, deployed as a scheduled Cloud Run
> job with the token in Secret Manager, and every run's verdicts
> appended to BigQuery so health is a trend, not a snapshot. The
> comparison side used ClickUp Brain, one of their autonomous agents,
> and their official MCP server driven by Claude.
