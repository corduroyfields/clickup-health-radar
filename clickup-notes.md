# ClickUp Health Radar — field notes

Honest, first-hand observations from building an AI engagement-health tool
against ClickUp's API, with Gemini on Vertex AI as the analysis engine.
(This file is the real deliverable — friction points are talking points.)

## Friction log (what actually bit us)

1. **Workspace config broke the integration on day one.** API-created Spaces
   start with only two task statuses (`to do` / `complete`). Our script assumed
   `in progress` existed → 400 error. Lesson: any integration or AI agent is
   only as reliable as the workspace configuration underneath it. A real
   client's half-configured workspace breaks tools the same way.

2. **Error messages hide in the response body.** `raise_for_status()` alone
   told us "400" but not why. Had to add a helper to print ClickUp's actual
   error text. Lesson: read the body, always.

3. **Idempotency is the integrator's job.** The seed script died halfway and
   left a partial Space; re-running would have duplicated everything. Fixed by
   making the script delete-then-rebuild. ClickUp does not dedupe by name.

4. **Silent default filters.** `GET /list/{id}/task` omits completed tasks
   unless you pass `include_closed=true`. Without it, every account looks
   unhealthier than it is — invisible data loss, no warning.

5. **API vocabulary drift.** The API calls workspaces "teams" (historical).
   Small, but the kind of thing that burns an hour.

## LLM output critique (first Radar run, Gemini 2.5 Flash)

**Got right:** caught both planted risks (blocked SSO, departed champion) and
ranked them first. The Acme recommendation (escalate to AE + exec sponsor when
chases fail) was genuine TAM judgment, not in the data. Beta's "value erosion"
risk synthesized three separate tasks into one narrative — real analysis.

**Pushback:**
- Both accounts scored 🔴 RED. One blocked task ≠ red; a human might say
  yellow for Acme. Untested whether it ever says GREEN — an alarm that always
  fires gets ignored. Calibration needs a healthy-account test case.
- Rule violation: claimed the data import "could be dependent on SSO" —
  invented inference despite an explicit "evidence only" instruction. Hedged,
  plausible, and precisely why a human stays in the loop.
- The two reports formatted differently (backticks vs bold, different HEALTH
  line shapes). Fine for humans, fatal for machine parsing → motivates
  structured (JSON-schema) output.

## Structured output (v2) — findings

- **Schema as contract:** passing a pydantic model as `response_schema` makes
  Vertex enforce the shape at generation time. Both reports came back
  structurally identical; the portfolio dashboard is *computed* from them.
  "Please format nicely" → "output physically can't be malformed."
- **Requiring evidence killed the hallucination.** v1 invented a dependency
  ("import could depend on SSO"). In v2, `evidence_tasks` is a required field
  and the fabricated claim simply didn't survive. Schema design is an
  anti-hallucination lever, not just a formatting tool.
- **Rubrics are code and can have bugs.** Acme stayed RED because our own
  rubric's RED clause ("core objective in jeopardy") overlapped YELLOW's.
  The model resolved OUR ambiguity conservatively. Audit instructions before
  blaming the model.
- **Calibration test passed:** a deliberately healthy control account (Gamma)
  came back GREEN. The alarm doesn't always fire.
- **But: models abhor an empty list.** Even at GREEN, the model manufactured
  a MEDIUM "risk" about a task due in 10 days with zero evidence of trouble
  (and Beta got a "deck at risk of delay" for a task that's simply not due
  yet). LLMs optimize for looking thorough; an explicit "return an empty
  risks list if there are none" instruction is the lever. Kept unfixed as a
  human-in-the-loop exhibit.
  - **Counterpoint (Josh):** the Gamma flag is defensible — security tasks
    punish lateness disproportionately (sick leave, vendor slippage), and 10
    days isn't much runway. So "manufactured concern" vs "prudent foresight"
    is itself a judgment call: evaluating AI output means grading against a
    *chosen risk posture*, not against objective truth. Reasonable seniors
    disagree with each other here, not just with the model.
- **Fabrication vs judgment is a blurry line.** "SSO is foundational to
  enterprise onboarding" isn't in our data — it's the model's domain prior,
  true and usefully applied. You can't suppress priors; you can only force
  them to cite evidence.
- **Hardcoded IDs are instant tech debt.** Re-seeding regenerates List IDs;
  fixed by discovering lists at runtime (which also made the Radar
  automatically sweep any new client added to the Space).

## Phase 1 — ClickUp Brain head-to-head

Trial recon: the Enterprise trial DOES include the AI product. In-product
naming as of Jul 2026: **Brain** (chat) and **Agents** — the phase plan's
"Super Agents / Autopilot" names had already drifted.

Prompt used both times (radar-style): "Assess the health of this engagement.
Green, yellow, or red? Top risks? Single best next action?"

### Brain raw output #1 — asked at the "Client Accounts" SPACE level (scope mistake, kept because it's informative)

> **🔴 Red.** Here's why:
>
> **Beta Inc is on fire.** The renewal call with their champion is 11 days
> overdue, the renewal proposal is due *today* and untouched, and a
> high-priority support-ticket spike has gone uninvestigated for 5 days.
> That's a churn cocktail.
>
> **Acme is slipping yellow→red.** SSO config is 7 days overdue (urgent),
> legacy data import is 2 days late, and both block the Jul 12 go-live
> readiness review. The onboarding timeline is compressing fast.
>
> **Gamma is fine.** Green, steady-state, nothing overdue.
>
> **Top risks:**
> 1. Beta Inc renewal stalls because you haven't even gotten the champion on
>    a call yet
> 2. Acme go-live date blows because upstream blockers keep cascading
> 3. The unresolved Beta support-ticket spike erodes trust right when you
>    need goodwill for renewal
>
> **Single best next action:** Drop everything and schedule that
> [Beta Inc renewal call](https://app.clickup.com/t/86baqzgw0). The proposal,
> the deck, the ticket investigation... none of it matters if you lose the
> relationship thread. Get the meeting on calendar today, then you'll know
> what shape the proposal needs to take.

### Brain raw output #2 — same prompt, asked from the Beta Inc Renewal LIST

> **🔴 Red.** This engagement is in trouble.
>
> You have 4 overdue tasks, zero assignees across the board, and the two
> most critical items (scheduling the renewal call and preparing the
> proposal) are both urgent and past due. The renewal call is 11 days
> overdue and hasn't even been *scheduled* yet, meaning you don't have a
> meeting on the books with the champion. The proposal was due today and
> hasn't started.
>
> **Top risks:**
> 1. No renewal call scheduled (11 days late) — you literally can't close a
>    renewal you haven't booked
> 2. Proposal not prepped (due today) — nothing to present even if you get
>    the meeting
> 3. Support-ticket spike uninvestigated (5 days late) — unresolved pain
>    gives the champion ammo to churn or push back on price
> 4. No one is assigned to any of this — accountability gap
>
> **Single best next action:** Drop everything and get that renewal call on
> the calendar today. Reach out directly to the Beta Inc champion. The
> proposal, the deck, the ticket investigation… none of it matters if you
> can't get in the room.

### First observations (full debrief after the Agent build)

- **Scope is respected, and it's on the user.** Run #1 was accidentally
  asked at the Space level and Brain correctly swept all three accounts;
  run #2 asked from the Beta list and Brain stayed inside it. So Brain is
  scope-faithful — but the *same words* ("this engagement") silently mean
  different things depending on where your cursor was. In radar2 scope is
  code; in Brain scope is UI state. An accidental experiment worth keeping:
  the Space-level answer also gave ONE header color ("🔴 Red") for a
  three-account scope where one account is green — a schema would have
  forced a color *per account*.
- **Brain caught something our radar never surfaced: zero assignees.**
  "No one is assigned to any of this — accountability gap" is a real,
  planted-data-adjacent signal radar2 never mentioned — because our export
  step never included assignee data, so our model couldn't see it. Brain
  lives inside the full data model and wins on breadth of context. (Radar
  lesson: an analysis is bounded by its export; the export is a silent
  filter you wrote.)
- **Health colors match the radar** on every graded account: Beta red,
  Gamma green (run #1 also volunteered an Acme "yellow→red" trajectory —
  portfolio-level synthesis we didn't ask for).
- **Consistent judgment across runs:** both runs picked the identical next
  action ("get the call booked; none of it matters if you can't get in the
  room") — stable, not a coin flip. And it's real TAM-caliber reasoning,
  same league as radar v1's escalate-to-exec-sponsor call.
- **Evidence present but unenforced.** Both runs cite day counts; run #1
  deep-linked the actual task, run #2 didn't. That variance is the point:
  radar2's schema makes evidence structurally mandatory, Brain includes it
  when it feels like it.
- **No structure, strong voice.** "On fire," "churn cocktail" — great
  human-calibrated prose, unparseable by a machine, no format lever found.
  This is exactly our v1 problem, on their side of the fence.
- **Calibration caveat:** Gamma got "fine" only inside a workspace sweep
  where Beta/Acme gave the model plenty of real trouble to talk about. The
  clean test of "models abhor an empty risks list" is a Gamma-ONLY question.
  (Done — see raw output #3 below.)

### Brain raw output #3 — same prompt, asked from the Gamma LLC Steady State LIST (calibration test)

> **Yellow.** The account isn't on fire, but it's drifting.
>
> The good: Q2 value report and the monthly stakeholder sync both got done.
> The bad: all 3 open tasks are still "to do" with **zero assignees**, and
> [Rotate Gamma integration credentials](https://app.clickup.com/t/86baqzh1p)
> is due next Monday with no one owning it and no progress.
>
> **Top risks:**
> 1. **Credential rotation (due 7/13)** is 6 days out, unassigned,
>    untouched. If this slips, it's a security exposure.
> 2. **No ownership on anything open.** The Q3 roadmap workshop (due 7/17)
>    needs prep time you don't have if nobody picks it up this week.
> 3. **Light task list overall.** Only 5 items for a "steady state" account
>    feels thin. Either work is happening off-platform or this engagement is
>    on autopilot without enough proactive touches.
>
> I'd assign the credential rotation today and block time for roadmap prep
> by Thursday, or this tips red fast.

### The calibration verdict: the two AIs disagree, and both flagged the SAME task

- **Radar2 said GREEN; Brain (list-scoped) said YELLOW.** And strikingly,
  Brain's #1 risk is the *identical task* our Gemini radar manufactured
  concern about — the credential rotation. Two independent models, different
  vendors, different context, both refuse to give a healthy account a clean
  bill, and both anchor on the same security task. "Models abhor an empty
  risks list" is not a Gemini quirk; it looks like an LLM trait.
- **…which strengthens Josh's counterpoint.** If every model independently
  flags it, "manufactured concern vs prudent foresight" is genuinely
  contested territory — grading AI output means grading against a chosen
  risk posture, not objective truth.
- **But the disagreement isn't pure temperament — Brain had more evidence.**
  (1) Brain sees assignees; a security task with *no owner* is legitimately
  scarier than the same task in our assignee-blind export. (2) Time passed
  between runs: our radar graded at ~10 days of runway, Brain at 6. Same
  account, closer to the cliff. Honest read: can't fully separate "sees more
  data" from "grades harsher" — which is itself a lesson about comparing AI
  systems (control the inputs AND the clock, or the comparison is mush).
- **Brain interrogates the data's absence, not just its contents.** Risk #3
  ("only 5 items feels thin — work is off-platform or the engagement is on
  autopilot") questions whether the List itself is trustworthy input. Our
  radar treats the export as ground truth; Brain treated it as a witness to
  cross-examine. Genuinely senior behavior — and also exactly how a model
  pads a risks list when the account is fine. Both readings are true.
- **Note Brain's own health-color drift:** run #1 (Space sweep) called Gamma
  "fine/green"; run #3 (list-scoped, days later) called it yellow. Scope and
  timing change the verdict. Radar2 would give the same answer at the same
  timestamp every run — that reproducibility is what you're buying with the
  roll-your-own build.

### Super Agent build — "Account Sentinel" → "Sentinel Sam"

- **The catalog is a prompt, not a wizard.** Picking the "Account Sentinel"
  card just pre-filled a natural-language request into the AI chat ("Help me
  build a Account Sentinel Super Agent…" — grammar bug included). So the
  three setup paths we were told to look for (catalog / natural-language /
  manual) collapse: catalog IS natural-language setup with a starter string.
- **Governance is inspect-after, not consent-before.** Creation itself was
  zero-friction: no clarifying questions, no permissions dialog, no approval
  step — the AI designed the agent and went "live" in under 60 seconds
  (self-named "Sentinel Sam"). But the agent's page (screenshots captured)
  exposes real post-hoc governance, tabbed Instructions / Triggers / Skills /
  Knowledge / Memory:
  - **Knowledge (access scoping):** workspace-level toggle ON by default
    (whole "Technical Assessment Workspace" + Client Accounts · 3 Lists);
    external **Web Search OFF by default** — conservative default, good.
  - **Triggers (allowlist):** Mention ON, Assign task ON, Direct Message
    OFF; plus Scheduled (hourly/daily/weekly/custom) and Automated
    (criteria-based) as add-ons. Note: **the Scheduled trigger is our whole
    Phase 3 Cloud Run + Scheduler plan as a single button.**
  - **Skills:** "What actions can the Agent take?" — ClickUp · 6 tools,
    extendable. A capability allowlist, i.e. the same idea as MCP tool
    permissions.
  - **Memory:** three toggles, ALL ON by default, including "Intelligence
    (Beta) — automatically learn & store helpful memories." Memory-on-by-
    default is the kind of thing an enterprise admin would want to know.
  - So the model is: agent ships live with sane-ish defaults, and the human
    reviews after the fact — opt-out governance, not opt-in. Nothing forced
    Josh to ever open this page.
  - Also visible: **usage metering** ("31 Brain AI uses / 1.5k credits
    left") — trial AI is credit-metered.
- **The default agent instructions are readable — and they're good.**
  Verbatim below. It's essentially radar2's architecture, rediscovered by
  ClickUp's prompt engineers: a role, a health rubric (🟢/🟡/🔴 with defined
  checks), a fixed output shape (risk level, 2-3 one-sentence concerns, one
  next action), style guardrails.
- **The kicker:** the template ends with *"If the account looks healthy, say
  so in one line and move on. **Don't invent problems.**"* That is exactly
  the "models abhor an empty risks list" lever we found and deliberately
  left unfixed as an exhibit. ClickUp's own template guards against the same
  failure mode — vendor-grade confirmation that the phenomenon is real and
  prompt-patchable. (Ironic footnote: Brain chat, which presumably doesn't
  carry this instruction, graded Gamma yellow; the agent template explicitly
  tries to prevent that.)
- **What the template does NOT have vs radar2:** (1) no enforced schema —
  the output shape is requested in prose, v1-style, not contract-enforced
  like Vertex `response_schema`; (2) no "Python does math" split — it asks
  the model itself to do date arithmetic (overdue, "due within 7 days"),
  which we specifically engineered out as unreliable; (3) no required
  evidence field.
- **Template interpolation confirmed broken — and you can't fix it.** The
  blanks are genuinely empty in the UI ("triggered on a task in ,"
  "which client account: , , or ."), not copy-paste-stripped chips. The
  generated agent shipped with holes in its own instructions. Worse for
  the control story: **the instructions field is read-only.** We couldn't
  repair their broken interpolation if we wanted to; changes presumably
  go through the Builder chat (prompt-to-prompt, no diff, no history).
  radar2's prompt is 100% ours, versioned in git. This is the single
  starkest control difference found in Phase 1.
- **But you CAN pick the model — including Claude Opus 4.8.** The one deep
  knob exposed is model choice (multi-vendor). Odd inversion vs radar2:
  ClickUp gives you the heaviest lever (which frontier model) and withholds
  the lightest (edit a sentence of the prompt). Also means a fun experiment:
  our Gemini-powered radar vs a Claude-powered ClickUp agent on identical
  data.

### Sentinel Sam's first run (triggered by @mention on "Prepare Beta Inc renewal proposal")

Output arrived as a task comment AND as an email notification (sender
`notifications@tasks.clickup.com`, rendered "Sentinel Sam commented", Gmail
auto-labeled it IMPORTANT). Verbatim comment (task/list names were live
mention-chips, shown here as [brackets]):

> 🔴 **At Risk** — [Beta Inc Renewal]
> - 4 of 5 open tasks are overdue; [Schedule renewal call with Beta Inc
>   champion] is 12 days late and [Investigate Beta Inc support-ticket
>   spike] is 6 days late.
> - 3 high/urgent items are still sitting in **to do**.
> - The only non-overdue open item, [Draft Beta Inc exec business review
>   deck], is due Wed Jul 15.
> - Recommended next action: triage the overdue renewal work today, assign
>   owners, and reset dates where the current plan is no longer real.

Findings from the run:

- **The broken blanks didn't matter.** Despite the empty list-name slots in
  its instructions, the agent correctly identified the account list from
  the triggering task's location. Models infer around holes — which cuts
  both ways: resilient in the demo, and the bug stays invisible until the
  inference someday goes wrong.
- **Template compliance is strong.** Header risk level on the 3-level scale,
  short bullets, exactly one next action, no wall of text — the agent's
  constrained output is far closer to spec than Brain chat's freeform prose
  on the same account. Instructions-as-guardrails works even without an
  enforced schema... on this run. (One run ≠ contract; that's still the
  schema's job.)
- **Evidence beats both Brain chat and radar2 on form:** the cited tasks are
  live object mentions (chips that deep-link), not strings. Best evidence UX
  of the three systems.
- **Date math was correct this run** — "12 days late" / "6 days late" is
  exactly Brain chat's "11 / 5 days" plus the one day that elapsed. The
  template makes the model do arithmetic we deliberately moved to Python;
  it got it right here, but nothing guarantees it.
- **It respected "never echo what the assignee can already see"** — the
  comment doesn't restate the triggering task's own overdue status; it
  reports the account around it. Subtle instruction, followed.
- **Agent output rides the normal notification pipeline.** The AI comment
  emailed like any human comment (and Gmail ranked it IMPORTANT). One
  @mention = one email; an automation firing on every status change would
  be an inbox flood of AI assessments. Notification hygiene is part of
  agent design, not an afterthought.
- **The email doubles as an audit artifact** — timestamped, attributed
  ("Sentinel Sam commented"), immutable in the inbox. (In-app Activity log
  still to verify.)

### Sentinel Sam on Gamma — the experiment that closed the loop

Triggered by @mention on "Rotate Gamma integration credentials" (<30s
response, emailed like the first). Verbatim:

> 🟢 Healthy
> No overdue work across Gamma, and nothing urgent/high priority is sitting
> in `to do`.
> Only watchout: 1 open item is due within the next 7 days, so timeline
> risk is low but active.
> No stalling pattern — 0 tasks have gone 14+ days without activity.
> Recommended next action: keep one clear owner on the next due item and
> close it this week to stay green.

**This is the money result of Phase 1.** Same vendor, same data, same day:
Brain chat said YELLOW on Gamma; Sentinel Sam — whose template carries
"don't invent problems" — said GREEN. The only meaningful difference is the
prompt. Full calibration table across all systems that looked at Gamma:

| System | Empty-risks guard in prompt? | Gamma verdict |
|---|---|---|
| radar2 (Gemini, ours) | No (left unfixed as exhibit) | 🟢 GREEN + one manufactured MEDIUM risk |
| Brain chat (list-scoped) | No (freeform) | 🟡 YELLOW, 3 risks |
| Sentinel Sam (agent template) | **Yes — "don't invent problems"** | 🟢 GREEN, watchout only |

- **The lever works, and the vendor proved it for us.** We hypothesized
  that an explicit "it's OK to say no risks" instruction would fix the
  manufactured-concern problem; ClickUp's own template contains exactly
  that instruction and its agent produced the only clean green of the
  three. The prompt IS the risk posture.
- **And it's the best-calibrated output of the three:** it still *surfaced*
  the 7-day credential task, but explicitly sized it ("timeline risk is low
  but active") instead of downgrading the account. Surfaced-not-alarmed is
  precisely what a senior human does with a watch item.
- **The model quietly invented a threshold:** "0 tasks have gone 14+ days
  without activity" — the template says only "many tasks with no recent
  updates"; the 14-day cutoff is the model operationalizing a vague rubric
  on its own. Reasonable, but unversioned and could differ next run; in
  radar2, thresholds are code.
- **Assignee posture flipped with the prompt too:** Brain chat made "no
  ownership" a headline risk; Sentinel Sam folded it into a gentle "keep
  one clear owner." Same platform, same data-model access — the prompt
  decided how scary the same fact sounds.

### Phase 1 verdict — the three-system comparison

| | Radar2 (ours) | Brain chat | Super Agent (Sentinel Sam) |
|---|---|---|---|
| Setup cost | Days (code, GCP, prompt, schema) | Zero | ~60 seconds |
| Scope control | In code, deterministic | UI state (cursor position) | Trigger task's list |
| Prompt control | Every word, in git | None visible | Readable, NOT editable (model choice only) |
| Output shape | Schema-enforced (can't be malformed) | Freeform prose | Template-shaped (held, but unenforced) |
| Evidence | Required field | Sometimes, sometimes linked | Live task chips (best UX) |
| Data access | What our export fetches (assignee-blind) | Full data model | Full data model |
| Gamma calibration | Green + invented risk | Yellow | Clean green |
| Reproducibility | Same input → same rubric every run | Drifted across scope/days | Unknown (n=1 per account) |
| Audit trail | Git history + our own logs | None visible | Comment + email trail |

Where Brain wins: zero setup, lives inside the full data model (caught
zero-assignees, which our assignee-blind export structurally couldn't),
clickable evidence, TAM-caliber judgment, cross-account synthesis for free.
Where the Radar wins: owned prompt/rubric/thresholds versioned in git,
schema-enforced output a machine can consume, deterministic scope, portable
to any LLM, and you can *fix* it when it's wrong — we couldn't even correct
the broken blanks in Sentinel Sam's instructions.
The honest summary: ClickUp's AI has the better *data position*; ours has
the better *contract*. The interview line: "I built the version you'd
build when you need control, then ran theirs and found where each one is
genuinely better."

#### Sentinel Sam default instructions (verbatim)

> 👋 Role and Objective
> You're the team's always-on account health monitor. Sharp, concise,
> slightly paranoid about deadlines. You spot risk before it becomes a fire
> and say it plainly.
>
> When triggered on a task in , you assess the health of the account that
> task belongs to and post a brief risk report as a comment on the
> triggering task.
>
> 🔍 What to Do When Triggered
> Identify which client account (list) the triggering task belongs to:
> , , or .
> Pull all open tasks for that account list.
> Assess account health by checking:
> Overdue tasks (anything past its due date)
> Tasks due within the next 7 days
> Urgent/High priority items still in "to do"
> Any patterns that signal stalling (many tasks with no recent updates)
> Post a comment on the triggering task with a short health snapshot:
> Overall risk level (🟢 Healthy / 🟡 Needs Attention / 🔴 At Risk)
> Top 2-3 concerns, each one sentence max
> One recommended next action
>
> ✍️ Communication Style
> Keep comments to 4-6 lines max. No walls of text.
> Use emoji sparingly for scanability (risk indicators only).
> Be direct. "SSO config is 8 days overdue and blocking go-live" not "It
> appears the SSO configuration task may be slightly behind schedule."
> Never echo information the assignee can already see on the task itself.
> If the account looks healthy, say so in one line and move on. Don't
> invent problems.

## Design patterns worth repeating

- **Python does math, the model does judgment.** We pre-compute "overdue by
  N days" in code; LLMs are unreliable calculators. Give the model
  conclusions, not arithmetic homework.
- **Prompt = job description:** role, evidence, fixed output shape, and
  guardrails ("evidence only", "name the tasks") to make output *checkable*.
- **Two GCP logins:** `gcloud auth login` (CLI) vs
  `gcloud auth application-default login` (your code / ADC). Separate ID
  cards; mixing them up is the #1 GCP beginner trap.
- **Vertex (`vertexai=True`) over a raw API key:** auth rides on ADC, usage
  bills to the project, nothing secret in the code — the enterprise pattern.

## Still to explore
- Structured JSON output via Gemini response schema (fix the parsing problem).
- A healthy account test case (calibration).
- ClickUp Brain / Super Agents on the same data (Enterprise trial) — compare
  to roll-your-own.
- ClickUp official MCP server from Claude Code — compare to Miro MCP
  experience.
- Cloud Run + Scheduler (make it a daily radar, not a manual script).
