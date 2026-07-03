"""ClickUp Health Radar — Step 2: seed a realistic client-services scenario.

Creates (via the ClickUp API):
    Space "Client Accounts"
      ├── List "Acme Corp Onboarding"   (a healthy-ish engagement)
      └── List "Beta Inc Renewal"       (a troubled engagement)

The tasks are deliberately imperfect — overdue items, a blocker, stale work —
so the Health Radar has real signals to detect.

Safe to re-run: it first deletes any existing "Client Accounts" Space,
then rebuilds everything from scratch.

Run:  uv run python seed_workspace.py
"""

import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["CLICKUP_API_TOKEN"]
HEADERS = {"Authorization": TOKEN}
BASE_URL = "https://api.clickup.com/api/v2"

# Your workspace ("team" in API-speak), found by main.py.
TEAM_ID = "90141353314"


def check(resp: requests.Response) -> None:
    """Like raise_for_status(), but shows ClickUp's actual error message first."""
    if not resp.ok:
        print(f"\nClickUp said no ({resp.status_code}): {resp.text}\n")
    resp.raise_for_status()


def days_from_now(days: int) -> int:
    """ClickUp wants due dates as Unix milliseconds. Negative days = overdue."""
    moment = datetime.now(timezone.utc) + timedelta(days=days)
    return int(moment.timestamp() * 1000)


def delete_space_if_exists(name: str) -> None:
    """Make the script re-runnable: clear out any previous copy of our Space."""
    resp = requests.get(f"{BASE_URL}/team/{TEAM_ID}/space", headers=HEADERS, timeout=30)
    check(resp)
    for space in resp.json()["spaces"]:
        if space["name"] == name:
            print(f"Deleting existing Space '{name}' (id: {space['id']})...")
            resp = requests.delete(
                f"{BASE_URL}/space/{space['id']}", headers=HEADERS, timeout=30
            )
            check(resp)


def create_space(name: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/team/{TEAM_ID}/space",
        headers=HEADERS,
        json={"name": name},
        timeout=30,
    )
    check(resp)
    space = resp.json()
    print(f"Created Space: {space['name']} (id: {space['id']})")
    return space["id"]


def create_list(space_id: str, name: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/space/{space_id}/list",
        headers=HEADERS,
        json={"name": name},
        timeout=30,
    )
    check(resp)
    lst = resp.json()
    print(f"  Created List: {lst['name']} (id: {lst['id']})")
    return lst["id"]


def create_task(list_id: str, task: dict) -> None:
    resp = requests.post(
        f"{BASE_URL}/list/{list_id}/task",
        headers=HEADERS,
        json=task,
        timeout=30,
    )
    check(resp)
    print(f"    Created task: {task['name']}")


# Priority codes in ClickUp's API: 1=Urgent, 2=High, 3=Normal, 4=Low.
ACME_TASKS = [
    {
        "name": "Kickoff call with Acme stakeholders",
        "description": "Intro call complete; notes shared with account team.",
        "status": "complete",
        "priority": 3,
        "due_date": days_from_now(-10),
    },
    {
        "name": "Provision Acme sandbox environment",
        "description": "Sandbox created and admin invites sent.",
        "status": "complete",
        "priority": 2,
        "due_date": days_from_now(-6),
    },
    {
        "name": "Configure SSO for Acme",
        "description": "Waiting on Acme IT to supply their SAML metadata file. "
        "Chased twice — no response since last week. BLOCKED on client.",
        "status": "to do",  # workspace only has "to do"/"complete" statuses
        "priority": 1,
        "due_date": days_from_now(-3),  # overdue and blocked: the key risk
    },
    {
        "name": "Import Acme legacy project data",
        "description": "CSV import of ~2,400 tasks from their old tool.",
        "status": "to do",  # workspace only has "to do"/"complete" statuses
        "priority": 2,
        "due_date": days_from_now(2),
    },
    {
        "name": "Train Acme power users (session 1 of 2)",
        "description": "90-minute admin training for 12 power users.",
        "status": "to do",
        "priority": 3,
        "due_date": days_from_now(5),
    },
    {
        "name": "Acme go-live readiness review",
        "description": "Checklist review with stakeholders before launch.",
        "status": "to do",
        "priority": 2,
        "due_date": days_from_now(9),
    },
]

BETA_TASKS = [
    {
        "name": "Pull Beta Inc usage / adoption report",
        "description": "Licenses used: 41 of 100. Adoption trending down since March.",
        "status": "complete",
        "priority": 2,
        "due_date": days_from_now(-14),
    },
    {
        "name": "Schedule renewal call with Beta Inc champion",
        "description": "Champion left the company in May. No new contact identified. "
        "Renewal is in 6 weeks.",
        "status": "to do",
        "priority": 1,
        "due_date": days_from_now(-7),  # badly overdue, high priority
    },
    {
        "name": "Prepare Beta Inc renewal proposal",
        "description": "Draft pricing for renewal; depends on the renewal call happening.",
        "status": "to do",
        "priority": 1,
        "due_date": days_from_now(4),
    },
    {
        "name": "Investigate Beta Inc support-ticket spike",
        "description": "18 tickets last month vs. usual 5. Mostly permissions confusion.",
        "status": "to do",  # workspace only has "to do"/"complete" statuses
        "priority": 2,
        "due_date": days_from_now(-1),
    },
    {
        "name": "Draft Beta Inc exec business review deck",
        "description": "QBR deck showing value delivered this year.",
        "status": "to do",
        "priority": 3,
        "due_date": days_from_now(12),
    },
    {
        "name": "Log Beta Inc feature requests in product tracker",
        "description": "Three requests from their ops team, sitting untriaged.",
        "status": "to do",
        "priority": 4,
        "due_date": days_from_now(-20),  # long-stale low-priority item
    },
]


# A deliberately HEALTHY account — the calibration control. If the Radar
# can't say GREEN here, the rubric (or the model) needs work.
GAMMA_TASKS = [
    {
        "name": "Monthly sync with Gamma stakeholders",
        "description": "June sync held; no open issues. Client happy with rollout pace.",
        "status": "complete",
        "priority": 3,
        "due_date": days_from_now(-5),
    },
    {
        "name": "Publish Gamma Q2 value report",
        "description": "Delivered to their VP Ops; positive feedback received.",
        "status": "complete",
        "priority": 3,
        "due_date": days_from_now(-12),
    },
    {
        "name": "Rotate Gamma integration credentials",
        "description": "Routine quarterly credential rotation.",
        "status": "to do",
        "priority": 3,
        "due_date": days_from_now(10),
    },
    {
        "name": "Plan Gamma Q3 roadmap workshop",
        "description": "Half-day workshop; agenda drafting underway.",
        "status": "to do",
        "priority": 3,
        "due_date": days_from_now(14),
    },
    {
        "name": "Refresh Gamma runbook documentation",
        "description": "Routine doc pass after the June feature release.",
        "status": "to do",
        "priority": 4,
        "due_date": days_from_now(21),
    },
]


def main() -> None:
    delete_space_if_exists("Client Accounts")
    space_id = create_space("Client Accounts")

    acme_id = create_list(space_id, "Acme Corp Onboarding")
    for task in ACME_TASKS:
        create_task(acme_id, task)

    beta_id = create_list(space_id, "Beta Inc Renewal")
    for task in BETA_TASKS:
        create_task(beta_id, task)

    gamma_id = create_list(space_id, "Gamma LLC Steady State")
    for task in GAMMA_TASKS:
        create_task(gamma_id, task)

    print("\nDone. Open ClickUp in your browser to see the new Space.")
    print("(No need to note List IDs — the radar discovers lists at runtime now.)")


if __name__ == "__main__":
    main()
