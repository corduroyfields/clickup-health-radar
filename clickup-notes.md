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

## Phase 2 — Claude + the official ClickUp MCP server

### Connection log (2026-07-08)

- **Connected to the official server** (`https://mcp.clickup.com/mcp`,
  HTTP transport) via `claude mcp add`, saved at **local scope** — i.e.
  keyed to this project folder only. OAuth completed on the first try;
  no retries, no token errors. Smooth.
- **Setup friction was all on the Claude side, not ClickUp's.** The
  desktop app doesn't ship a terminal `claude` command (its bundled copy
  is a private app bundle), so step zero was installing the standalone
  CLI via the native installer. Then TWO auth layers before any ClickUp
  data flows: (1) CLI → Anthropic account login, (2) `/mcp` → ClickUp
  OAuth. Contrast with Miro, which was already wired in as a claude.ai
  connector with zero terminal setup. Lesson for the integration story:
  "connect X to your AI" is really an auth *chain*, and each link is a
  place a less technical user stalls.
- **OAuth consent screen: a workspace picker and nothing else.** Already
  signed into ClickUp in the browser, so the whole grant was one click:
  choose which workspace, done. **No scope/permission list was shown** —
  no read-vs-write distinction, no object-level choices, no way to
  narrow the grant below "the workspace." The absence is the datapoint:
  we went looking for the consent-BEFORE governance moment (vs Sentinel
  Sam's inspect-AFTER model from Phase 1) and found that the consent
  screen exists but carries near-zero information — you authorize a
  51-tool read/write surface without being told that's what it is. An
  enterprise admin evaluating this would have to get the effective
  permission list from documentation (or from `/mcp` after connecting),
  not from the grant screen. Frictionless for the user, thin for
  governance — the same trade Phase 1 found on the agent side.
- **51 tools.** That's the headline number from `/mcp`: the ClickUp
  server exposes 51 tools — for comparison, in the same session Miro's
  connector exposes 36, Notion's 20, Gmail's 13. Two immediate
  observations:
  - Tool definitions occupy the model's context window like anything
    else; a 51-tool surface is a real prompt-space cost before the
    first request is even typed.
  - Tool-selection risk scales with the menu. With 51 options, "did the
    model pick the right tool?" (the thing experiment 1 watches for)
    is a genuinely harder problem than with a 6-tool allowlist like
    Sentinel Sam's. Bigger surface = more capable and more fallible.
  - (Tool names/granularity to be captured from the interactive session
    during the experiments.)
- **Local scope has a nice side effect:** because the server was saved to
  the project folder's config, EVERY Claude session launched from this
  folder now sees it — the desktop session picked up the 51 tools without
  any extra setup. Config-by-directory is the mechanism.

### The 51-tool surface, mapped (2026-07-08)

Ten clusters: task CRUD (incl. `delete_task`, `merge_tasks`), task
discovery (`search`, `filter_tasks`, `get_workspace_hierarchy`), task
relationships (dependencies/links/tags), comments + attachments, Chat
(read AND `send_chat_message`), Docs (create/update pages), people
(`get_workspace_members`, `resolve_assignees`), time tracking, flow
analytics (`get_task_time_in_status` + bulk variant), workspace admin
(folders/lists/custom fields/reminders).

- **It's a designed product, not a generated API wrapper.** The tells:
  `resolve_assignees` / `find_member_by_name` exist only because models
  talk in human names while the API demands numeric IDs; and
  `get_bulk_tasks_time_in_status` pre-computes an aggregate so the model
  doesn't do arithmetic. ClickUp's MCP team independently arrived at our
  "Python does math, the model does judgment" pattern — the glue tools
  are where you can see it.
- **What's ABSENT answers a Phase 1 open question:** no Brain, no
  Agents, no Automations, no Goals, no Whiteboards. MCP exposes the data
  plane, not the AI/automation plane — external AI (us) and their AI
  (Sentinel Sam) are parallel tracks that can't drive each other.
- **Governance kicker:** the one-click, no-scope-list OAuth grant
  included `delete_task` and `send_chat_message`. The consent screen
  never surfaced that an AI was being given delete rights and a voice in
  team chat. Our phase rule (no destructive actions without explicit
  go-ahead) is supplying the governance the platform didn't.
- **No bulk-write tools** — bulk read analytics exists, but writes are
  one-task-at-a-time. Caps the blast radius of a misfiring agent,
  intentionally or not.
- **Value framing (interview-ready):** read tools make ClickUp data
  AI-legible (the radar2 use case with zero code); write tools make it
  AI-actionable (insight → intervention in one conversation); glue tools
  are the ergonomic layer that makes the first two reliable.

### Experiment 2 — write (Acme escalation task) (2026-07-08)

Created via MCP: "Send SSO escalation email to Acme exec sponsor",
urgent, due Jul 10, in Acme Corp Onboarding → task `86bauv9fq`,
one-shot success, URL returned. Two calls again (`get_list` → 
`create_task`). Observations:

- **Reads resolve names; writes demand IDs.** `get_list` happily takes
  a list *name*, but `create_task` requires a numeric `list_id`.
  Sensible asymmetry: fuzzy matching is fine when the worst case is a
  wrong answer, not fine when the worst case is a mutation landing in
  the wrong place. Precision requirements scale with blast radius —
  a pattern worth quoting.
- **Same asymmetry in dates:** writes accept human `YYYY-MM-DD`; reads
  return epoch milliseconds. Generous input, lazy output.
- **ClickUp embeds human-in-the-loop instructions INSIDE the tool
  schema.** `create_task`'s field descriptions literally say "always
  ask the user which list" and "Ask the user what they want to name
  the task." The vendor is prompt-injecting governance into every MCP
  host's orchestration loop — consent-at-the-moment-of-action, exactly
  what the OAuth screen didn't provide. (Satisfied here: Josh approved
  the exact task before creation per our phase rule.)
- **The model authored unrequested content.** The phase spec dictated
  name/priority/due date; the task *description* (SAML metadata
  context, Jul 12 go-live tie-in, exec-help ask) was model-written,
  synthesized from radar2's report earlier in the session. Useful — 
  and it means a write-enabled model doesn't just execute writes, it
  *composes* them. Review-before-send matters for content, not just
  for the act of writing.
- **First tool failure of the phase — and it's a documentation bug, not
  a model miss.** Assigning the task: `update_task`'s own description
  says it supports assignees as "user IDs, emails, usernames, or
  'me'"… and passing `"me"` returned `Assignees list invalid`. The
  model did exactly what the vendor's docs said and got an error;
  recovery required falling back to `resolve_assignees` ("me" →
  numeric ID) + retry. Three lessons: (1) tool descriptions are
  load-bearing prompt engineering, so when they overpromise, the
  *model* looks unreliable — description-vs-implementation drift is a
  new API-contract failure mode; (2) self-healing worked — the model
  recovered in one extra round-trip without human help, which is the
  actual value-add of model orchestration (radar2 would have crashed);
  (3) this is the phase file's predicted "tool-selection miss," except
  the model selected *correctly per the docs* — the docs were wrong.
- **Josh's UI check caught it: the task has no assignee.** Nobody told
  the AI to assign an owner, so it didn't — we just reproduced the
  exact accountability gap every system in this project flags, via AI
  write. Unowned tasks aren't only a messy-workspace symptom; they're
  the *natural output of automated task creation* (our seed script,
  and now MCP-Claude, both). Any org adopting AI task creation should
  expect its zero-assignee count to climb unless "always assign an
  owner" is baked into the instructions — the same lesson as "return
  an empty risks list if none," but on the write side.

Radar re-run after the write (same day) — two findings:

- **The loop closed, but the phase file's prediction was falsified in
  an interesting direction.** Predicted: the new urgent task "should
  raise Acme's risk picture." Actual: still RED / 3 risks — the radar
  read the escalation task SEMANTICALLY, folding it into the SSO risk
  as evidence and making "complete the escalation email" its NEXT
  ACTION. It judged the task by content (escalation = remedy underway),
  not metadata (another urgent item due in 2 days). Bonus irony: radar
  recommended escalation → MCP-Claude created the task, description
  written from the radar's own report → radar now cites that
  AI-authored task as evidence and recommends executing it. **AI output
  became AI input in one cycle.** At scale, that's an echo-chamber
  failure mode: models validating work that models generated, with the
  human increasingly out of the citation chain.
- **Free nondeterminism experiment:** between the two same-day runs,
  Beta and Gamma inputs were UNCHANGED — yet Beta went 4 risks → 3
  (regrouped), legacy import HIGH → MEDIUM, Gamma workshop MEDIUM →
  LOW, and a new Acme training LOW appeared. Second asterisk on
  radar2's reproducibility claim (first was the clock): **the schema
  guarantees shape, not judgment** — severities and groupings jitter
  with sampling randomness. Same day, same data, different risk
  counts. If a customer dashboards these severities, they need to know
  the error bars exist.

### Experiment 3 — judgment ("which account needs attention most this week?") (2026-07-08)

MCP-Claude's answer: **Beta first**, Acme close second, Gamma a watch
item. Reasoning: Acme is acute but *diagnosed with remedy in motion*
(SSO blocker known, escalation task in flight, due Jul 10); Beta is a
structural void — renewal in 6 weeks, champion gone since May, NO
replacement contact, tickets 18 vs usual 5, adoption 41/100 licenses
and falling. Relationship rebuilding has the longest lead time on the
board, so it gets the week.

- **Convergence:** Brain (Phase 1, space-level) also said Beta first,
  nearly verbatim ("drop everything and schedule that renewal call").
  Two different model-orchestrated systems, same portfolio call.
- **radar2 declines to rank — and that's the exhibit.** Its dashboard
  shows 🔴🔴🟡 with risk counts, but cross-account prioritization was
  never in its schema, so the question is literally unanswerable
  without a code change. The schema contract cuts both ways: output
  can't be malformed, AND questions outside the schema can't be asked.
  Model orchestration buys flexibility; the contract is the price.
- **Orchestration: 5 calls** (1 space-wide `filter_tasks` with
  include_closed=true + 4 targeted `get_task` description fetches).
  Notably, this plan APPLIED EXPERIMENT 1'S LESSON unprompted (closed
  tasks + descriptions, having missed the champion story before). The
  model-orchestrated export boundary adapts between runs; radar2's
  can't change without a commit. Same property, two names: "learning"
  and "unauditable drift."
- Small but telling: in the space sweep, the only assigned task in the
  entire Space is the one MCP-Claude created and Josh had it assign —
  every seeded task is ownerless. The workspace's accountability gap
  is now visible in one field scan.

### Experiment 1 — read (Beta Inc summary) (2026-07-08)

Prompt: "Summarize the open tasks in the Beta Inc Renewal list, most
urgent first." Run from the desktop session (same MCP connection).

Result: 4 of 5 open tasks overdue (call 12d, spike 6d, proposal tipped
overdue yesterday, feature-log 25d), zero assignees, only the exec deck
(due Jul 15) healthy. **Numbers exactly match Sentinel Sam's same-day
run** — independent path, same arithmetic, clean cross-validation.

Same-day radar2 cross-check (run by Josh, 2026-07-08) — two findings:

- **Same Beta verdict (RED, unanimous across all four systems), but
  radar2's read was DEEPER — and the gap is the finding.** radar2 cited
  the departed champion and declining usage (evidence: the usage/
  adoption report task). MCP-Claude's 2-call read saw neither: the
  usage task is completed (excluded by `filter_tasks`' default) and the
  champion story lives in task descriptions (omitted from the compact
  payload; seeing them costs a `get_task` call per task). Phase 1
  lesson was "an analysis is bounded by its export; the export is a
  silent filter you wrote." MCP version is sharper: **the model decides
  its own export boundary fresh every run** — the efficient-looking
  2-call plan WAS the silent filter, and it isn't written down anywhere
  auditable. Correct summary, missing story. (Also kills the clean
  "assignees: MCP sees more than radar2" scoreline from above — each
  system saw a different slice: radar2 got descriptions+closed tasks
  but no assignees; MCP got assignees but skipped descriptions. Data
  position isn't a ranking, it's a Venn diagram.)
- **radar2 flipped Gamma GREEN → YELLOW with identical code.** Nothing
  changed but the clock (credential rotation runway: ~10 days at the
  GREEN run, 5 today). The Phase 1 reproducibility claim needs an
  asterisk: same inputs → same verdict, but **the date is an input** —
  verdict = f(data, rubric, clock). This partially vindicates Brain
  chat's yellow (graded at 6 days runway, between our 10 and 5). The
  pattern across all runs: every system WITHOUT an empty-risks guard
  tips yellow somewhere around the one-week cliff; Sentinel Sam
  ("don't invent problems") is the only one that stayed green next to
  it — and it still surfaced the item, sized low. Calibration is
  three-variable: data seen, prompt posture, grading date.

Orchestration observations (the real experiment):

- **Two MCP calls end-to-end:** `get_list` (name→ID), then
  `filter_tasks` (open tasks, one page). Efficient — no hierarchy
  sweep, no per-task fetches. Model-orchestration overhead vs radar2's
  scripted pipeline was ~zero for a read this simple.
- **The vendor's tool descriptions steered the orchestration.** Planned
  first call was `get_workspace_hierarchy`; its own description ("use
  only when you need structure — most tools resolve names
  automatically") redirected to `get_list`. So there are THREE
  orchestration authorities, not two: our code (radar2), the model
  (MCP), and the vendor's tool-description prose quietly shaping what
  the model does. Tool descriptions are prompt engineering with an
  install base.
- **Friction #4 came back defused:** `filter_tasks` excludes closed
  tasks by default — the same silent filter that bit our raw-API code —
  but declared in the schema, and correct for this ask.
- **Dates arrive as epoch milliseconds.** The tool hands the model
  arithmetic homework (the exact thing radar2 moved into Python).
  Mitigation used here: delegated conversion to a Python one-liner —
  an escape hatch Claude Code has and a chat-only MCP host doesn't.
  Same server, different host, different reliability.
- **Assignees ARE in the MCP payload** (visible empty arrays) — closes
  the handoff question. MCP-Claude sees the zero-assignee gap that
  Brain caught and radar2's assignee-blind export couldn't.
- **Ranking was model judgment, not tool output:** the API returned
  date order; putting the 25d-overdue LOW task below the 1d-overdue
  URGENT one was the model applying priority-over-age reasoning.
  Defensible — and unversioned, like Sam's invented 14-day threshold.

### Phase 2 verdict — script-orchestrated vs model-orchestrated

The question this phase existed to answer: what changes when the model,
not your code, decides which API calls happen?

- **Round-trips: model orchestration was CHEAPER than feared.** The
  reads took 2 calls, the write 2 (+2 for the assignee recovery), the
  portfolio judgment 5. radar2 makes a similar number of API calls —
  the difference isn't volume, it's that radar2's sequence is frozen in
  git and MCP-Claude's is improvised per run.
- **The export boundary is the real divide.** radar2 fetches a fixed
  slice (its blind spots are fixed and auditable: no assignees); 
  MCP-Claude decides its slice fresh each run (missed descriptions in
  experiment 1, learned, fetched them in experiment 3). Script = static
  blind spots you can document; model = dynamic blind spots you can't.
- **Failure behavior inverts.** radar2 hits an API surprise → crashes
  (or silently mis-reports, friction #4). MCP-Claude hit a broken tool
  contract ("me" assignee) → recovered unaided in one round-trip.
  Self-healing is model orchestration's killer feature; determinism is
  script orchestration's. Pick per use case: pipelines want the crash,
  assistants want the recovery.
- **Question flexibility is one-sided.** "Which account needs attention
  most?" — MCP-Claude and Brain answer natively; radar2's schema has no
  rank field, so it structurally can't. New questions cost a code
  change in script-land and a sentence in model-land.
- **Contract flexibility is one-sided the OTHER way.** radar2's output
  can't be malformed, feeds dashboards, has error bars only in
  content (severity jitter), never in shape. MCP-Claude's output is
  prose unless a human re-imposes structure per prompt.
- **A third orchestration author emerged: the vendor.** ClickUp's tool
  descriptions steered call planning ("most tools resolve names
  automatically"), embedded human-in-the-loop instructions ("always ask
  the user which list"), and once outright lied ("me" works). In script
  orchestration the vendor's voice is docs you read once; in model
  orchestration it's live prompt text inside every loop — a
  distribution channel for governance AND a new failure surface.
- **Who orchestrates, really:** radar2 = our code decides, model
  judges. Brain/Sam = their platform decides, their prompt judges.
  MCP = the model decides, steered by vendor tool-prose, guarded by
  host permissions and a human on writes. The interview line: "the
  divide isn't two-sided, it's a stack — code, model, vendor
  tool-design, and host permissions all get a vote; architecture is
  deciding which one gets the veto."

### The Miro comparison (honest paragraph, Josh's read)

The two MCP enablements differed mainly in the on-ramp: Miro arrived
pre-wired as a claude.ai connector, while ClickUp was initiated from the
terminal (`claude mcp add` + `/mcp` OAuth) — more setup, but that's
where the hands-on command-line learning actually happened, so the
friction was a feature. Both authorizations themselves were simple
one-click approvals (and both share the same governance thinness: a
click, not a scope review). The ClickUp testing went materially broader
than the Miro work ever did — read, write, and judgment experiments
cross-checked against three other AI systems, plus digging into the
business drivers behind the server (why a vendor ships MCP at all, and
how an enterprise would implement automations against it with their own
agents) rather than just driving the tools. Ergonomically the two felt
equal — natural-language requests turned into sensible tool calls on
both sides. Honest caveat: that "equal" verdict rests on limited
command-line mileage; more reps running MCP work from the terminal are
needed before the ergonomics judgment means much.

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
