#!/usr/bin/env python3
"""Auto-update Pull Request Description Checklist.

Checks off the verification checkboxes in the PR body automatically when
quality gate checks pass.
"""

import json
import os
import re
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"


def main() -> None:
    """Updates PR description checkboxes based on audit results."""
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not event_path or not token or not repo or not os.path.exists(event_path):
        print("ℹ️ Skipping PR checklist update: missing event context.")
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    if "pull_request" not in event_data:
        return

    pr_number = event_data["pull_request"]["number"]
    body = event_data["pull_request"].get("body") or ""

    if not METRICS_PATH.exists():
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    if metrics.get("overall_passed", False):
        new_body = re.sub(r"- \[[ xX]\] (.*test.*)", r"- [x] \1", body, flags=re.IGNORECASE)
        new_body = re.sub(r"- \[[ xX]\] (.*lint.*)", r"- [x] \1", new_body, flags=re.IGNORECASE)
        new_body = re.sub(r"- \[[ xX]\] (.*quality.*)", r"- [x] \1", new_body, flags=re.IGNORECASE)

        if new_body != body:
            url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            req = urllib.request.Request(
                url,
                data=json.dumps({"body": new_body}).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json",
                    "User-Agent": "Clean-Chassis-PR-Checklist",
                },
                method="PATCH",
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    if resp.status == 200:
                        print(f"✔ Checklist automatically checked off for PR #{pr_number}.")
            except Exception as e:
                print(f"⚠️ Error updating PR checklist: {e}")


if __name__ == "__main__":
    main()
