#!/usr/bin/env python3
"""Automatically Check Off Issue Checkboxes and Close Tasks Upon Audit Success.

Parses PR title, description, and commit messages for task references like [DSLR-01:#1]
or 'Closes #1'. When make audit passes 100%, fetches the linked GitHub Issue,
converts all '- [ ]' checkboxes to '- [x]', posts an audit verification comment,
and closes the Issue via GitHub REST API.
"""

import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"


def _extract_issue_number(event_data: dict) -> Optional[int]:
    """Extracts issue number from PR title, body, branch name, or git log."""
    search_texts: list[str] = []

    if "pull_request" in event_data:
        pr = event_data["pull_request"]
        search_texts.append(pr.get("title", ""))
        search_texts.append(pr.get("body", "") or "")
        search_texts.append(pr.get("head", {}).get("ref", ""))

    if "commits" in event_data:
        for commit in event_data["commits"]:
            search_texts.append(commit.get("message", ""))

    if "head_commit" in event_data:
        search_texts.append(event_data["head_commit"].get("message", ""))

    try:
        git_log = subprocess.run(
            ["git", "log", "-n", "10", "--oneline"],
            capture_output=True,
            text=True,
            check=False,
        )
        if git_log.stdout:
            search_texts.append(git_log.stdout)
    except Exception:
        pass

    patterns = [
        r"\[[a-zA-Z0-9_-]+:#([0-9]+)\]",
        r"(?:Closes|Close|Fixes|Fix|Resolves|Resolve)\s+#([0-9]+)",
        r"(?:feat|fix|test|docs|refactor|chore)/(?:task|dslr)-0*([0-9]+)",
        r"(?:task|dslr)-0*([0-9]+)",
    ]

    for text in search_texts:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

    return None


def _github_api_request(url: str, method: str, token: str, data: Optional[dict] = None) -> dict:
    """Executes an HTTP request against GitHub REST API and returns JSON response."""
    import ssl

    ctx = ssl._create_unverified_context()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kaggle-Competitions-Issue-Automator",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    with urllib.request.urlopen(req, context=ctx) as resp:
        content = resp.read().decode("utf-8")
        return json.loads(content) if content else {}


def _poke_milestone(
    repo: str, milestone_number: int, token: str, issue_number: Optional[int] = None
) -> None:
    """Forces GitHub to recalculate milestone progress counters.

    Args:
        repo: Repository slug in format 'owner/repo'.
        milestone_number: The integer milestone number to refresh.
        token: GitHub authentication token.
        issue_number: Optional linked issue number to re-assert milestone association.
    """
    ms_url = f"https://api.github.com/repos/{repo}/milestones/{milestone_number}"
    try:
        ms_data = _github_api_request(ms_url, "GET", token)
        desc = ms_data.get("description") or ""
        _github_api_request(ms_url, "PATCH", token, {"description": desc})
        print(f"🔄 Milestone #{milestone_number} poked successfully via REST API.")
    except Exception as exc:
        print(f"⚠️ Failed to poke Milestone #{milestone_number}: {exc}")

    if issue_number:
        try:
            issue_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
            _github_api_request(issue_url, "PATCH", token, {"milestone": milestone_number})
            print(f"🔄 Issue #{issue_number} milestone association refreshed.")
        except Exception as exc:
            print(f"⚠️ Failed to refresh milestone on Issue #{issue_number}: {exc}")


def _sync_all_open_milestones(repo: str, token: str) -> None:
    """Audits all open milestones and triggers recalculation if counts are out of sync.

    Args:
        repo: Repository slug in format 'owner/repo'.
        token: GitHub authentication token.
    """
    url = f"https://api.github.com/repos/{repo}/milestones?state=open"
    try:
        milestones = _github_api_request(url, "GET", token)
        if not isinstance(milestones, list):
            return
        for ms in milestones:
            ms_num = ms.get("number")
            if not ms_num:
                continue
            desc = ms.get("description") or ""
            ms_url = f"https://api.github.com/repos/{repo}/milestones/{ms_num}"
            _github_api_request(ms_url, "PATCH", token, {"description": desc})

            # Re-assert milestone on closed issues to force GitHub's progress counter worker
            try:
                closed_url = (
                    f"https://api.github.com/repos/{repo}/issues"
                    f"?milestone={ms_num}&state=closed&per_page=20"
                )
                closed_issues = _github_api_request(closed_url, "GET", token)
                if isinstance(closed_issues, list):
                    for c_iss in closed_issues:
                        c_num = c_iss.get("number")
                        if c_num:
                            c_url = f"https://api.github.com/repos/{repo}/issues/{c_num}"
                            _github_api_request(c_url, "PATCH", token, {"milestone": ms_num})
            except Exception as inner_exc:
                print(f"ℹ️ Could not refresh closed issues for milestone #{ms_num}: {inner_exc}")

            print(f"🎯 Verified and refreshed Milestone #{ms_num} ('{ms.get('title')}').")
    except Exception as exc:
        print(f"⚠️ Failed to sync open milestones: {exc}")


def _post_audit_comment(comments_url: str, token: str, issue_number: int, metrics: dict) -> None:
    """Posts an audit verification comment on the specified issue.

    Args:
        comments_url: URL for posting comments to the issue.
        token: GitHub authentication token.
        issue_number: The integer issue number.
        metrics: Dictionary containing passed and total test counts.
    """
    passed_tests = metrics.get("passed_tests", 0)
    total_tests = metrics.get("total_tests", 0)
    timestamp = metrics.get("timestamp", "N/A")

    comment_text = (
        f"### 🧙‍♂️ 42 DSLR — Automated Audit Verification\n\n"
        f"✅ **Task Audit Passed 100%** (`{timestamp}`)\n"
        f"- 🛡️ **42 Norm & Anti-Cheating**: 0 errors\n"
        f"- 🧪 **Unit Tests**: {passed_tests}/{total_tests} passed\n"
        f"- ⚡ **Python 3.10 Syntax**: Verified\n\n"
        f"All acceptance criteria validated. Issue checked off and closed automatically."
    )

    try:
        _github_api_request(comments_url, "POST", token, {"body": comment_text})
        print(f"✅ Posted audit certificate comment on Issue #{issue_number}.")
    except Exception as exc:
        print(f"⚠️ Failed to post comment on Issue #{issue_number}: {exc}")


def _close_issue_record(issue_url: str, issue_number: int, token: str) -> None:
    """Closes the specified issue via gh CLI (GraphQL) or REST API fallback.

    Args:
        issue_url: URL of the issue resource.
        issue_number: The integer issue number.
        token: GitHub authentication token.
    """
    closed_via_gh = False
    try:
        gh_result = subprocess.run(
            ["gh", "issue", "close", str(issue_number), "--reason", "completed"],
            capture_output=True,
            text=True,
            check=False,
        )
        if gh_result.returncode == 0:
            print(f"✅ Issue #{issue_number} closed via gh CLI (GraphQL mutation).")
            closed_via_gh = True
        else:
            print(
                f"ℹ️ gh issue close non-zero exit ({gh_result.returncode}): "
                f"{gh_result.stderr.strip()}"
            )
    except Exception as exc:
        print(f"ℹ️ gh CLI execution error: {exc}")

    if not closed_via_gh:
        patch_data = {"state": "closed", "state_reason": "completed"}
        try:
            _github_api_request(issue_url, "PATCH", token, patch_data)
            print(f"✅ Issue #{issue_number} state set to closed via REST API.")
        except Exception as exc:
            print(f"⚠️ Failed to close Issue #{issue_number} via REST API: {exc}")


def _update_issue_checkboxes(repo: str, issue_number: int, token: str, metrics: dict) -> None:
    """Checks off issue checkboxes, posts audit certificate, closes issue, and updates milestone.

    Args:
        repo: Repository slug in format 'owner/repo'.
        issue_number: The integer issue number to update.
        token: GitHub authentication token.
        metrics: Dictionary containing audit metrics.
    """
    issue_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    comments_url = f"{issue_url}/comments"

    try:
        issue_data = _github_api_request(issue_url, "GET", token)
    except Exception as exc:
        print(f"⚠️ Failed to fetch Issue #{issue_number}: {exc}")
        return

    body = issue_data.get("body") or ""
    new_body = body.replace("- [ ]", "- [x]")
    count_updated = body.count("- [ ]")

    _post_audit_comment(comments_url, token, issue_number, metrics)

    if new_body != body:
        try:
            _github_api_request(issue_url, "PATCH", token, {"body": new_body})
            print(
                f"✅ Issue #{issue_number} description updated: "
                f"{count_updated} checkboxes checked off."
            )
        except Exception as exc:
            print(f"⚠️ Failed to update Issue #{issue_number} body: {exc}")

    _close_issue_record(issue_url, issue_number, token)

    milestone_obj = issue_data.get("milestone")
    if isinstance(milestone_obj, dict) and milestone_obj.get("number"):
        _poke_milestone(repo, int(milestone_obj["number"]), token, issue_number)


def main() -> None:
    """Main entrypoint for issue checklist automation script."""
    event_path = os.getenv("GITHUB_EVENT_PATH")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not event_path or not token or not repo or not os.path.exists(event_path):
        print(
            "ℹ️ Skipping Issue automation: "
            "Not running inside GitHub Action or missing required env vars."
        )
        return

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    issue_number = _extract_issue_number(event_data)
    if not issue_number:
        print(
            "ℹ️ Generic PR / Commit detected. "
            "No task issue reference (e.g. [DSLR-01:#1]) found. Skipping issue closure."
        )
        # Still synchronize all open milestones to ensure progress bars are up to date
        _sync_all_open_milestones(repo, token)
        return

    if not METRICS_PATH.exists():
        print(f"⚠️ Audit summary metrics missing at {METRICS_PATH}")
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    if not metrics.get("overall_passed", False):
        print(
            f"ℹ️ Audit failed for Issue #{issue_number}. "
            "Leaving issue open and checkboxes unchecked."
        )
        return

    print(f"🚀 Processing automated checklist and closure for Issue #{issue_number}...")
    _update_issue_checkboxes(repo, issue_number, token, metrics)
    _sync_all_open_milestones(repo, token)


if __name__ == "__main__":
    main()
