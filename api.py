"""Radar front-end API.

The backend half of the Phase 4 explorer: a small web service that reads
the radar's BigQuery history and answers in JSON. The browser-side page
(built later) will be its only customer.

Run locally:   uv run uvicorn api:app --reload --port 8000
Try it:        curl http://localhost:8000/api/portfolio
"""

from fastapi import FastAPI
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


@app.get("/api/portfolio")
def portfolio():
    """Current portfolio at a glance: each client's most recent verdict."""
    rows = bq.query(PORTFOLIO_SQL).result()
    return [dict(row) for row in rows]


# Serve the browser-side files from static/. Mounted LAST so the /api/*
# routes above are matched first; html=True makes "/" serve index.html.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
