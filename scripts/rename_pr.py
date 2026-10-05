#!/usr/bin/env python3
"""Rename Pull Request Title with Clean Chassis Audit Results.

Appends live audit status and test metrics to the PR title via GitHub REST API.
Example: "feat(core): implement engine | ✅ Audit 100% | 🧪 2/2 Passed"
"""

import json
import os
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"


def main() -> None:
    """Updates the PR title with the latest audit results."""
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not event_path or not token or not repo:
        print("ℹ️ Skipping PR rename: Not running inside a PR workflow or missing tokens.")
        return

    if not os.path.exists(event_path):
        print(f"⚠️ Event file not found: {event_path}")
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    if "pull_request" not in event_data:
        print("ℹ️ Event is not a pull_request. Skipping rename.")
        return

    pr_number = event_data["pull_request"]["number"]
    raw_title = event_data["pull_request"]["title"]

    # Clean previous status suffix from title if present
    clean_title = raw_title.split(" | ✅ Audit")[0].split(" | ⚠️ Audit")[0].strip()

    if not METRICS_PATH.exists():
        print(f"⚠️ Audit summary file missing at {METRICS_PATH}")
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    overall_passed = metrics.get("overall_passed", False)
    passed_tests = metrics.get("passed_tests", 0)
    total_tests = metrics.get("total_tests", 0)

    if overall_passed:
        status_tag = f"✅ Audit 100% | 🧪 {passed_tests}/{total_tests} Passed"
    else:
        status_tag = "⚠️ Audit Failed"

    new_title = f"{clean_title} | {status_tag}"
    if new_title == raw_title:
        print("ℹ️ PR title is already up to date.")
        return

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"title": new_title}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Clean-Chassis-PR-Renamer",
        },
        method="PATCH",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                print(f"✔ Successfully renamed PR #{pr_number} -> '{new_title}'")
            else:
                print(f"⚠️ Unexpected status while renaming PR: {resp.status}")
    except Exception as e:
        print(f"❌ Error renaming PR: {e}")


if __name__ == "__main__":
    main()
