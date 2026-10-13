#!/usr/bin/env python3
"""Automatically Update PR Description, Checklists & Issue Link Upon Audit Success.

Reads artifacts/audit_summary.json and converts matching `- [ ]` into `- [x]`
in the active Pull Request description. Also resolves `Resolves #[ISSUE_NUMBER]`
and placeholder descriptions with actual task objectives from .github/issues/.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

METRICS_PATH = BASE_DIR / "artifacts" / "audit_summary.json"


def extract_task_and_issue(
    branch: str, title: str = "", body: str = ""
) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """Extracts task ID, GitHub issue number, and task objective."""
    task_id: Optional[str] = None
    issue_num: Optional[int] = None
    objective: Optional[str] = None

    # 1. Try commit / title pattern: [TASK-04:#9]
    search_texts = [title, body, branch]
    try:
        git_log = subprocess.run(
            ["git", "--no-pager", "log", "-n", "5", "--oneline"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        if git_log.stdout:
            search_texts.append(git_log.stdout)
    except Exception:
        pass

    for text in search_texts:
        m = re.search(r"\[([a-zA-Z0-9_-]+):#(\d+)\]", text)
        if m:
            task_id = m.group(1).upper()
            issue_num = int(m.group(2))
            break

    # 2. Try branch pattern: feat/task-04-declarative-agent-baseline
    if not task_id:
        m_branch = re.search(r"task-0*(\d+)", branch, re.IGNORECASE)
        if m_branch:
            idx = int(m_branch.group(1))
            task_id = f"TASK-{idx:02d}"

    # 3. Lookup in .github/issues/
    issues_dir = BASE_DIR / ".github" / "issues"
    if issues_dir.exists() and task_id:
        idx_match = re.search(r"(\d+)", task_id)
        idx_str = f"{int(idx_match.group(1)):02d}" if idx_match else ""
        for f in issues_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            if (idx_str and f"task-{idx_str}" in f.name.lower()) or (f"id: {task_id}" in content):
                m_iss = re.search(r"github_issue:\s*(\d+)", content)
                if m_iss and not issue_num:
                    issue_num = int(m_iss.group(1))

                m_obj = re.search(
                    r"## 🎯 (?:Task Objective|Objetivo Didático)\s+([^\n#]+)",
                    content,
                )
                if m_obj:
                    objective = m_obj.group(1).strip()
                break

    return task_id, issue_num, objective


def update_pr_body(
    body: str,
    branch: str = "",
    title: str = "",
) -> Tuple[str, int]:
    """Updates checklist items, resolves issue placeholders, and refines body."""
    new_body = body
    checked_count = 0

    # 1. Clean up accidental truncated title prefix at very beginning
    new_body = re.sub(r"^…[^\n]*\n+", "", new_body.strip())

    # 2. Extract task / issue details
    _, issue_num, objective = extract_task_and_issue(branch, title, body)

    # 3. Resolve #[ISSUE_NUMBER] placeholder
    if issue_num:
        new_body = re.sub(
            r"(?:Resolves|Closes|Fixes)\s*#\[(?:ISSUE_NUMBER|ISSUE_NUM|NUM)\]",
            f"Resolves #{issue_num}",
            new_body,
            flags=re.IGNORECASE,
        )

    # 4. Replace description placeholder if present
    if objective:
        placeholder_pattern = (
            r"(?:-\s*\*\*Description\*\*:\s*|Description:\s*)"
            r"Brief explanation of what was added or refactored\.?"
        )
        if re.search(placeholder_pattern, new_body, re.IGNORECASE):
            new_body = re.sub(
                placeholder_pattern,
                f"- **Description**: {objective}",
                new_body,
                flags=re.IGNORECASE,
            )

    # 5. Check off Quality Gate checklist items
    checklist_patterns = [
        r"- \[[ \t]\](\s*Code complies with project style[^\n]*)",
        r"- \[[ \t]\](\s*Unit and integration tests pass[^\n]*)",
        r"- \[[ \t]\](\s*Security audit passes with zero critical findings[^\n]*)",
        r"- \[[ \t]\](\s*Documentation updated[^\n]*)",
    ]

    for pat in checklist_patterns:
        if re.search(pat, new_body, re.IGNORECASE):
            new_body = re.sub(pat, r"- [x]\1", new_body, flags=re.IGNORECASE)
            checked_count += 1

    return new_body, checked_count


def send_pr_update(repo: str, pr_number: int, new_body: str, token: str) -> bool:
    """Sends PATCH request to update the PR description body."""
    import ssl

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kaggle-Competitions-Checklist-Updater",
    }
    data = json.dumps({"body": new_body}).encode("utf-8")
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            if resp.status == 200:
                print(f"✅ PR #{pr_number} checklist & description updated successfully via API.")
                return True
            print(f"⚠️ Failed to update PR checklist: HTTP {resp.status}")
            return False
    except Exception as e:
        print(f"⚠️ Error updating PR checklist via API: {e}")
        return False


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


def main() -> None:
    """Updates matching checklist checkboxes and issue references in the PR body."""
    parser = argparse.ArgumentParser(description="Update PR checklist and issue link.")
    parser.add_argument("--pr", type=int, default=None, help="Pull Request number override")
    args = parser.parse_args()

    token, repo = get_token_and_repo()
    if not token or not repo:
        print("ℹ️ Missing GitHub token or repository slug. Skipping PR checklist update.")
        return

    # Check audit metrics
    if not METRICS_PATH.exists():
        print(f"⚠️ Audit summary file missing at {METRICS_PATH}")
        return

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    if not metrics.get("overall_passed", False):
        print("ℹ️ Audit did not pass completely. Leaving checklist items unchecked.")
        return

    pr_number = args.pr
    branch = ""
    title = ""
    body = ""

    # If running in GitHub Actions
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path) and not pr_number:
        with open(event_path, "r", encoding="utf-8") as f:
            event_data = json.load(f)
        if "pull_request" in event_data:
            pr_number = event_data["pull_request"]["number"]
            body = event_data["pull_request"]["body"] or ""
            title = event_data["pull_request"]["title"] or ""
            branch = event_data["pull_request"].get("head", {}).get("ref", "")

    import ssl

    ctx = ssl._create_unverified_context()

    # If PR number specified or discovered, fetch details via API
    if pr_number:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "Kaggle-Competitions-Checklist-Updater",
            },
        )
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                pr_data = json.loads(resp.read().decode("utf-8"))
                body = pr_data.get("body", "") or ""
                title = pr_data.get("title", "") or ""
                branch = pr_data.get("head", {}).get("ref", "")
        except Exception as e:
            print(f"⚠️ Error fetching PR #{pr_number} from API: {e}")
            return
    else:
        # Fallback: check open PR for current branch
        try:
            from scripts.create_pr import get_current_branch

            branch = get_current_branch()
        except Exception:
            branch = ""

        if branch:
            owner = repo.split("/")[0]
            url = f"https://api.github.com/repos/{repo}/pulls?head={owner}:{branch}&state=open"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Kaggle-Competitions-Checklist-Updater",
                },
            )
            try:
                with urllib.request.urlopen(req, context=ctx) as resp:
                    prs = json.loads(resp.read().decode("utf-8"))
                    if prs:
                        pr_number = prs[0]["number"]
                        body = prs[0].get("body", "") or ""
                        title = prs[0].get("title", "") or ""
            except Exception:
                pass

    if not pr_number:
        print("ℹ️ No active pull request found to update.")
        return

    new_body, count = update_pr_body(body, branch=branch, title=title)
    if new_body != body:
        send_pr_update(repo, pr_number, new_body, token)
        print(f"ℹ️ PR #{pr_number} updated: {count} checklist item(s) checked off.")
    else:
        print(f"ℹ️ PR #{pr_number} body is already up to date.")


if __name__ == "__main__":
    main()
