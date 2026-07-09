"""ClickUp Health Radar — Step 3: the AI health analysis.

For each client List:
  1. Pull every task from ClickUp (the facts).
  2. Pre-compute the objective bits Python is good at (days overdue).
  3. Hand the facts to Gemini on Vertex AI with a TAM-style briefing prompt.
  4. Print the health read: status color, risks, recommended next action.

Run:  uv run python radar.py
"""

import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from google import genai

TEAM_ID = "90141353314"  # the workspace
SPACE_NAME = "Client Accounts"

GCP_PROJECT = "clickup-health-radar"
GCP_LOCATION = "us-central1"
MODEL = "gemini-2.5-flash"


def get_clickup_token() -> str:
    """Fetch the ClickUp token, preferring Secret Manager over the local .env.

    Order matters for where this code will run:
      1. GCP Secret Manager — one central copy, guarded by IAM, versioned,
         every access audit-logged. On the laptop this authenticates via ADC;
         in Cloud Run it will authenticate as the job's service account.
         Same code, both places — that's the point.
      2. .env fallback — keeps the radar runnable offline or on a machine
         with no GCP credentials at all.
    """
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT}/secrets/clickup-api-token/versions/latest"
        payload = client.access_secret_version(name=name).payload.data
        print("(ClickUp token: Secret Manager)")
        return payload.decode()
    except Exception as exc:
        # Whatever went wrong (package missing, no ADC, IAM denied), fall
        # back to the .env — but say why, so IAM problems aren't invisible.
        load_dotenv()
        token = os.environ.get("CLICKUP_API_TOKEN")
        if token:
            print(f"(ClickUp token: .env fallback — Secret Manager said: {type(exc).__name__})")
            return token
        raise RuntimeError(
            "No ClickUp token available: Secret Manager failed and .env has no CLICKUP_API_TOKEN"
        ) from exc


TOKEN = get_clickup_token()
HEADERS = {"Authorization": TOKEN}
BASE_URL = "https://api.clickup.com/api/v2"


def discover_lists() -> dict[str, str]:
    """Ask ClickUp what client Lists exist right now, instead of hardcoding
    IDs that go stale every time the Space is re-seeded."""
    resp = requests.get(f"{BASE_URL}/team/{TEAM_ID}/space", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    spaces = {s["name"]: s["id"] for s in resp.json()["spaces"]}
    space_id = spaces[SPACE_NAME]

    resp = requests.get(f"{BASE_URL}/space/{space_id}/list", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return {lst["name"]: lst["id"] for lst in resp.json()["lists"]}


def fetch_tasks(list_id: str) -> list[dict]:
    """Pull all tasks in a List. include_closed matters: without it,
    ClickUp silently omits completed tasks — and 'work that got done'
    is part of an honest health picture."""
    resp = requests.get(
        f"{BASE_URL}/list/{list_id}/task",
        headers=HEADERS,
        params={"include_closed": "true"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["tasks"]


def describe_task(task: dict) -> str:
    """Flatten one task into a single factual line for the prompt.

    We pre-compute 'days overdue' in Python instead of asking the model
    to do date math — LLMs are unreliable calculators, so give them
    conclusions, not arithmetic homework.
    """
    status = task["status"]["status"]

    priority = "none"
    if task.get("priority"):
        priority = task["priority"]["priority"]  # e.g. "urgent", "high"

    due_note = "no due date"
    if task.get("due_date"):
        due = datetime.fromtimestamp(int(task["due_date"]) / 1000, tz=timezone.utc)
        days = (datetime.now(timezone.utc) - due).days
        if status == "complete":
            due_note = "completed"
        elif days > 0:
            due_note = f"OVERDUE by {days} day(s)"
        else:
            due_note = f"due in {-days} day(s)"

    description = (task.get("description") or "").strip()
    line = f"- {task['name']} | status: {status} | priority: {priority} | {due_note}"
    if description:
        line += f"\n  notes: {description}"
    return line


def build_prompt(client_name: str, task_lines: list[str]) -> str:
    tasks_block = "\n".join(task_lines)
    return f"""You are a senior Technical Account Manager reviewing the health of
a client engagement. Below are the current tasks for the "{client_name}"
engagement, exported from our project tracker.

TASKS:
{tasks_block}

Write a concise engagement health report with exactly these sections:

HEALTH: one of 🟢 GREEN (on track), 🟡 YELLOW (at risk), or 🔴 RED (in trouble),
followed by a one-sentence justification.

TOP RISKS: the 2-3 most important risks, each one line, most severe first.
Base risks only on evidence in the tasks — do not invent facts.

RECOMMENDED NEXT ACTION: the single highest-leverage thing the account team
should do this week, and why.

Be direct and specific. Name the tasks you are referring to."""


def main() -> None:
    # vertexai=True routes calls through YOUR GCP project via ADC —
    # no API key in the code, and usage shows up in your project's billing.
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)

    for client_name, list_id in discover_lists().items():
        print(f"\n{'=' * 60}")
        print(f"ENGAGEMENT HEALTH: {client_name}")
        print("=" * 60)

        tasks = fetch_tasks(list_id)
        task_lines = [describe_task(t) for t in tasks]
        prompt = build_prompt(client_name, task_lines)

        response = client.models.generate_content(model=MODEL, contents=prompt)
        print(response.text)


if __name__ == "__main__":
    main()
