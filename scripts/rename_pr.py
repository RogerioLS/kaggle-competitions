#!/usr/bin/env python3
"""Rename Pull Request Title with Clean Chassis Audit Results.

Appends live audit status and test counts to the PR title via GitHub REST API.
Example: "✨ feat(agent): [TASK-04:#9] ... | ✅ Audit 100% | 🧪 29/29 Tests | 🔒 Security OK"
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"


def get_token_and_repo() -> Tuple[Optional[str], Optional[str]]:
    """Retrieves token and repository slug from env or local config."""
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        try:
            from scripts.create_pr import get_github_token

            token = get_github_token()
        except Exception:
            token = None

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        try:
            from scripts.create_pr import get_repository_slug

            owner, r = get_repository_slug()
            repo = f"{owner}/{r}"
        except Exception:
            repo = None

    return token, repo


def get_clean_title(raw_title: str) -> str:
    """Removes existing status suffixes and recovers untruncated commit subject."""
    clean = raw_title.split(" | ")[0].strip()

    # If title was truncated (e.g. ends with '…' or '...'), recover from git log
    if clean.endswith(("…", "...")):
        try:
            git_log = subprocess.run(
                ["git", "--no-pager", "log", "-n", "1", "--pretty=format:%s"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
            )
            if git_log.stdout.strip():
                clean = git_log.stdout.strip()
        except Exception:
            pass

    return clean


def main() -> None:
    """Updates the PR title with the latest audit results."""
    parser = argparse.ArgumentParser(description="Rename PR with audit results.")
    parser.add_argument("--pr", type=int, default=None, help="Pull Request number override")
    args = parser.parse_args()

    token, repo = get_token_and_repo()
    if not token or not repo:
        print("ℹ️ Missing GitHub token or repository slug. Skipping PR rename.")
        return

    # Load audit metrics
    if not METRICS_PATH.exists():
        print(f"⚠️ Audit summary file missing at {METRICS_PATH}")
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    overall_passed = metrics.get("overall_passed", False)
    passed_tests = metrics.get("passed_tests", 0)
    total_tests = metrics.get("total_tests", 0)

    if overall_passed:
        status_tag = f"✅ Audit 100% | 🧪 {passed_tests}/{total_tests} Tests | 🔒 Security OK"
    else:
        status_tag = f"⚠️ Audit Failed | 🧪 {passed_tests}/{total_tests} Tests"

    pr_number = args.pr
    raw_title = ""

    # Check GITHUB_EVENT_PATH
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path) and not pr_number:
        with open(event_path, "r", encoding="utf-8") as f:
            event_data = json.load(f)
        if "pull_request" in event_data:
            pr_number = event_data["pull_request"]["number"]
            raw_title = event_data["pull_request"]["title"]

    import ssl

    ctx = ssl._create_unverified_context()

    # If PR number given or discovered, fetch title if empty
    if pr_number and not raw_title:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Kaggle-Competitions-PR-Renamer",
            },
        )
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                pr_data = json.loads(resp.read().decode("utf-8"))
                raw_title = pr_data.get("title", "")
        except Exception as e:
            print(f"⚠️ Error fetching PR #{pr_number} from API: {e}")
            return
    elif not pr_number:
        # Fallback to current branch
        try:
            from scripts.create_pr import get_current_branch

            branch = get_current_branch()
            if branch:
                owner = repo.split("/")[0]
                url = f"https://api.github.com/repos/{repo}/pulls?head={owner}:{branch}&state=open"
                req = urllib.request.Request(
                    url,
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "Kaggle-Competitions-PR-Renamer",
                    },
                )
                with urllib.request.urlopen(req, context=ctx) as resp:
                    prs = json.loads(resp.read().decode("utf-8"))
                    if prs:
                        pr_number = prs[0]["number"]
                        raw_title = prs[0].get("title", "")
        except Exception:
            pass

    if not pr_number:
        print("ℹ️ No active pull request found to rename.")
        return

    clean_title = get_clean_title(raw_title)
    new_title = f"{clean_title} | {status_tag}"

    if new_title == raw_title:
        print("ℹ️ PR title is already up to date.")
        return

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kaggle-Competitions-PR-Renamer",
    }
    data = json.dumps({"title": new_title}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            if resp.status == 200:
                print(f"✅ PR #{pr_number} title updated successfully:")
                print(f"   Original: {raw_title}")
                print(f"   Updated : {new_title}")
            else:
                print(f"⚠️ Failed to update PR title: HTTP {resp.status}")
    except Exception as e:
        print(f"⚠️ Error updating PR title via API: {e}")


if __name__ == "__main__":
    main()
