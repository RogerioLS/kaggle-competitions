#!/usr/bin/env python3
"""Auto-update Linked Issue Checklist & Close Upon Audit Pass.

Parses PR description and commits for linked issues (#XX or TASK-XX)
and marks tasks as completed upon full audit pass.
"""

import json
import os
import re
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"


def main() -> None:
    """Updates linked issues based on audit results."""
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not event_path or not token or not repo or not os.path.exists(event_path):
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    if not METRICS_PATH.exists():
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    if not metrics.get("overall_passed", False):
        return

    pr_body = event_data.get("pull_request", {}).get("body", "")
    pattern = r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)"
    linked_issues = re.findall(pattern, pr_body, re.IGNORECASE)

    for issue_num in set(linked_issues):
        url = f"https://api.github.com/repos/{repo}/issues/{issue_num}"
        req = urllib.request.Request(
            url,
            data=json.dumps({"state": "closed", "state_reason": "completed"}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "Clean-Chassis-Issue-Updater",
            },
            method="PATCH",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    print(f"✔ Closed issue #{issue_num} with state_reason: completed.")
        except Exception as e:
            print(f"⚠️ Error closing issue #{issue_num}: {e}")


if __name__ == "__main__":
    main()
