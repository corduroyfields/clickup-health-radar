"""ClickUp Health Radar v2 — structured output.

Same pipeline as radar.py, with one upgrade: instead of free text, Gemini
must return JSON matching a schema we define. Vertex AI enforces the shape
at generation time, so the output is machine-parseable — ready for a
dashboard, a Slack alert, or a BigQuery row.

Also fixes the calibration problem from v1: the prompt now contains an
explicit rubric for GREEN / YELLOW / RED instead of leaving it to vibes.

Run:  uv run python radar2.py
"""

import json
from datetime import datetime, timezone
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel

# Reuse the ClickUp plumbing from v1 — no copy-paste.
# (Safe to import: radar.py's main() only runs under `if __name__ == "__main__"`.)
from radar import (
    GCP_LOCATION,
    GCP_PROJECT,
    MODEL,
    describe_task,
    discover_lists,
    fetch_tasks,
)


# ---- The contract: Gemini's answer MUST fit these shapes ----

class Risk(BaseModel):
    summary: str
    severity: Literal["high", "medium", "low"]
    evidence_tasks: list[str]  # names of the tasks this risk is based on


class HealthReport(BaseModel):
    health: Literal["GREEN", "YELLOW", "RED"]
    justification: str
    risks: list[Risk]
    next_action: str


def build_prompt(client_name: str, task_lines: list[str]) -> str:
    tasks_block = "\n".join(task_lines)
    return f"""You are a senior Technical Account Manager reviewing the health of
the "{client_name}" client engagement. Below are its current tasks from our
project tracker.

TASKS:
{tasks_block}

Assess engagement health using this rubric:
- GREEN: work is on track; no urgent/high-priority items are overdue.
- YELLOW: one contained problem OR several small ones; recoverable with
  normal effort this week.
- RED: a core objective of the engagement (go-live, renewal) is in jeopardy,
  or multiple urgent items are overdue with no path forward.

Rules: base every risk only on evidence in the tasks — never invent facts or
dependencies. For each risk, list the exact task names it rests on.
The next_action is the single highest-leverage move for the account team
this week."""


def analyze(client: genai.Client, client_name: str, list_id: str) -> HealthReport:
    tasks = fetch_tasks(list_id)
    prompt = build_prompt(client_name, [describe_task(t) for t in tasks])

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=HealthReport,
        ),
    )
    # .parsed = the JSON already validated and loaded into our HealthReport class.
    return response.parsed


DOT = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}

# Where run history accumulates: project.dataset.table
BQ_TABLE = f"{GCP_PROJECT}.radar.health_reports"


def store_reports(reports: dict[str, "HealthReport"]) -> None:
    """Append this run's reports to BigQuery — one row per client account.

    This is the structured-output payoff: because every report is a
    HealthReport (not prose), each one maps 1:1 onto table columns.
    Free text could never become rows. All reports in a run share one
    run_time, so SQL can group by run as well as by day.
    """
    from google.cloud import bigquery

    bq = bigquery.Client(project=GCP_PROJECT)
    run_time = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "run_time": run_time,
            "client": client_name,
            "health": r.health,
            "justification": r.justification,
            "risk_count": len(r.risks),
            # risks keep their full structure as a JSON column — queryable
            # later with JSON functions, without needing more columns now.
            "risks": json.dumps([risk.model_dump() for risk in r.risks]),
            "next_action": r.next_action,
        }
        for client_name, r in reports.items()
    ]
    errors = bq.insert_rows_json(BQ_TABLE, rows)
    if errors:
        print(f"(BigQuery: some rows failed: {errors})")
    else:
        print(f"(BigQuery: {len(rows)} report row(s) appended to {BQ_TABLE})")


def main() -> None:
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)

    reports: dict[str, HealthReport] = {}
    for client_name, list_id in discover_lists().items():
        report = analyze(client, client_name, list_id)
        reports[client_name] = report

        print(f"\n{'=' * 60}\n{DOT[report.health]} {report.health} — {client_name}")
        print(f"   {report.justification}")
        for risk in report.risks:
            print(f"\n   [{risk.severity.upper()}] {risk.summary}")
            print(f"   evidence: {', '.join(risk.evidence_tasks)}")
        print(f"\n   NEXT ACTION: {report.next_action}")

    # The payoff of structure: reports are now data, so we can compute with them.
    print(f"\n{'=' * 60}\nPORTFOLIO DASHBOARD")
    for client_name, report in reports.items():
        print(f"  {DOT[report.health]} {client_name}: {report.health} "
              f"({len(report.risks)} risk(s))")

    # History is best-effort: a warehouse hiccup shouldn't kill the health
    # report itself (monitoring must degrade, not die). Failures print loudly.
    try:
        store_reports(reports)
    except Exception as exc:
        print(f"(BigQuery append SKIPPED — {type(exc).__name__}: {exc})")


if __name__ == "__main__":
    main()
