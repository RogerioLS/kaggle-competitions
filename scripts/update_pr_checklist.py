#!/usr/bin/env python3
"""Automatically Check Off PR Description Checklists Upon Successful 42 DSLR Audit.

Reads artifacts/audit_summary.json and converts matching `- [ ]` into `- [x]`
in the active Pull Request description.
"""

import json
import os
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"

CHECKLIST_MAPPINGS = [
    "- [ ] Code follows Python 3.10 standards and max 100 chars/line.",
    "- [ ] All functions/methods have complete docstrings.",
    "- [ ] `make norm` passes without errors.",
    "- [ ] `make compile` passes without syntax errors.",
    "- [ ] No prohibited built-in mathematical statistics methods were used.",
    "- [ ] All unit tests pass (`make test`).",
]


def _update_checklist_body(body: str) -> tuple[str, int]:
    """Replaces unchecked checklist items with checked items."""
    new_body = body
    checked_count = 0
    for target in CHECKLIST_MAPPINGS:
        replacement = target.replace("- [ ]", "- [x]")
        if target in new_body:
            new_body = new_body.replace(target, replacement)
            checked_count += 1
    return new_body, checked_count


def _send_pr_update(repo: str, pr_number: int, new_body: str, token: str) -> None:
    """Sends PATCH request to update the PR description body."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "42-DSLR-Checklist-Updater",
    }
    data = json.dumps({"body": new_body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                print(f"✅ PR #{pr_number} checklist updated successfully via API.")
            else:
                print(f"⚠️ Failed to update PR checklist: HTTP {resp.status}")
    except Exception as e:
        print(f"⚠️ Error updating PR checklist via API: {e}")


def main() -> None:
    """Updates matching checklist checkboxes in the PR body."""
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not event_path or not token or not repo or not os.path.exists(event_path):
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    if "pull_request" not in event_data or not METRICS_PATH.exists():
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    if not metrics.get("overall_passed", False):
        print("ℹ️ Audit did not pass completely. Leaving manual checklist items unchecked.")
        return

    pr_number = event_data["pull_request"]["number"]
    body = event_data["pull_request"]["body"] or ""

    new_body, count = _update_checklist_body(body)
    if new_body != body:
        _send_pr_update(repo, pr_number, new_body, token)
        print(f"ℹ️ {count} checklist item(s) checked off.")
    else:
        print("ℹ️ PR checklist is already up to date.")


if __name__ == "__main__":
    main()
