"""Radar front-end API.

The backend half of the Phase 4 explorer: a small web service that reads
the radar's BigQuery history and answers in JSON. The browser-side page
(built later) will be its only customer.

Run locally:   uv run uvicorn api:app --reload --port 8000
Try it:        curl http://localhost:8000/api/portfolio
"""

import json
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from google.cloud import bigquery

# The FastAPI object is the "app" — uvicorn hands every incoming HTTP
# request to it, and it routes the request to the matching function below.
app = FastAPI(title="ClickUp Health Radar API")

# One BigQuery client for the whole process. Locally this authenticates as
# Josh (ADC); on Cloud Run it will authenticate as the service's robot.
bq = bigquery.Client(project="clickup-health-radar")

# "Latest row per client": rank each client's rows newest-first, keep rank 1.
PORTFOLIO_SQL = """
SELECT run_time, client, health, risk_count, justification, next_action
FROM `clickup-health-radar.radar.health_reports`
QUALIFY ROW_NUMBER() OVER (PARTITION BY client ORDER BY run_time DESC) = 1
ORDER BY client
"""


HISTORY_SQL = """
SELECT run_time, client, health, risk_count
FROM `clickup-health-radar.radar.health_reports`
ORDER BY run_time
"""


@app.get("/api/portfolio")
def portfolio():
    """Current portfolio at a glance: each client's most recent verdict."""
    rows = bq.query(PORTFOLIO_SQL).result()
    return [dict(row) for row in rows]


# The client name arrives from the URL and lands in the SQL as a QUERY
# PARAMETER (@client), never by pasting it into the SQL string. Pasted-in
# values are how SQL injection happens — same rule as textContent vs
# innerHTML on the browser side: data must never be able to become code.
DETAIL_SQL = """
SELECT run_time, client, health, risk_count, justification, next_action, risks
FROM `clickup-health-radar.radar.health_reports`
WHERE client = @client
ORDER BY run_time DESC
LIMIT 1
"""


@app.get("/api/account/{client}")
def account_detail(client: str):
    """Latest full report for one client, risks parsed and included."""
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("client", "STRING", client)]
    )
    rows = list(bq.query(DETAIL_SQL, job_config=job_config).result())
    if not rows:
        raise HTTPException(status_code=404, detail=f"No reports for client {client!r}")

    report = dict(rows[0])
    # BigQuery's JSON column may arrive as an already-parsed object or as a
    # raw string depending on client-library version — normalize to parsed.
    if isinstance(report["risks"], str):
        report["risks"] = json.loads(report["risks"])
    return report


@app.get("/api/history")
def history():
    """Every run per client, oldest first — the trend chart's data.

    Grouped by client here (not in the browser) because JSON should be
    shaped for its consumer: the chart draws one dot-row per client.
    """
    grouped = defaultdict(list)
    for row in bq.query(HISTORY_SQL).result():
        grouped[row["client"]].append(
            {
                "run_time": row["run_time"],
                "health": row["health"],
                "risk_count": row["risk_count"],
            }
        )
    return grouped


# Serve the browser-side files from static/. Mounted LAST so the /api/*
# routes above are matched first; html=True makes "/" serve index.html.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
