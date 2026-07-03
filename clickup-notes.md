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
- **Fabrication vs judgment is a blurry line.** "SSO is foundational to
  enterprise onboarding" isn't in our data — it's the model's domain prior,
  true and usefully applied. You can't suppress priors; you can only force
  them to cite evidence.
- **Hardcoded IDs are instant tech debt.** Re-seeding regenerates List IDs;
  fixed by discovering lists at runtime (which also made the Radar
  automatically sweep any new client added to the Space).

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
