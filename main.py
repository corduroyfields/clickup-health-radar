"""ClickUp Health Radar — Step 1: prove we can talk to ClickUp.

Asks the ClickUp API two questions:
  1. Who am I?                   (confirms the token works)
  2. What workspaces can I see?  (finds the Enterprise trial workspace)
"""

import os

import requests
from dotenv import load_dotenv

# Read .env and make CLICKUP_API_TOKEN available to os.environ.
load_dotenv()

TOKEN = os.environ["CLICKUP_API_TOKEN"]

# Every ClickUp API call carries this header — it's how each request proves who we are.
HEADERS = {"Authorization": TOKEN}

BASE_URL = "https://api.clickup.com/api/v2"


def main() -> None:
    # --- Question 1: who does ClickUp think we are? ---
    resp = requests.get(f"{BASE_URL}/user", headers=HEADERS, timeout=30)
    resp.raise_for_status()  # stop loudly if ClickUp says no (bad token = 401)
    user = resp.json()["user"]
    print(f"Logged in as: {user['username']} ({user['email']})")

    # --- Question 2: which workspaces (ClickUp calls them "teams") can we see? ---
    resp = requests.get(f"{BASE_URL}/team", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    teams = resp.json()["teams"]
    print(f"\nWorkspaces visible to this token: {len(teams)}")
    for team in teams:
        print(f"  - {team['name']}  (id: {team['id']})")


if __name__ == "__main__":
    main()
