#!/usr/bin/env python3
"""Governance Linter for Branch Names and Conventional Commits.

Validates that:
1. The branch name follows: <type>/<description> or <type>/<task-id>-<description>
2. All commits in the PR follow:
   <type>(<scope>): [<TASK-ID>:#<NUM>] <description> or
   <type>(<scope>): [<TASK-ID>] <description> or
   <type>(<scope>): [<RESERVED_TAG>] <description>
3. If executed within GitHub Actions and violations occur, posts feedback and
   automatically closes the Pull Request.
"""

import argparse
import os
import re
import subprocess
import sys
from typing import List, Tuple

BRANCH_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|hotfix|release)"
    r"(/([a-zA-Z0-9_\-]+))+$"
)

COMMIT_REGEX = re.compile(
    r"^([^:]*\s+)?(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([a-zA-Z0-9_\/-]+\))?:\s*(\[([a-zA-Z0-9_:#-]+)\])?\s*(.+)$"
)

RESERVED_TAGS = {
    "INFRA",
    "CHORE",
    "DOCS",
    "FIX",
    "HOTFIX",
    "GLOBAL",
    "CONFIG",
    "SECURITY",
    "COMMUNITY",
    "DEPS",
    "RELEASE",
}


def validate_branch(branch_name: str) -> Tuple[bool, str]:
    """Validates the branch name against the institutional regex."""
    clean_branch = branch_name.replace("refs/heads/", "").strip()
    if clean_branch in {"main", "master", "develop"}:
        return True, ""
    if BRANCH_REGEX.match(clean_branch):
        return True, ""
    error_msg = (
        f"Invalid branch name: `{clean_branch}`\n"
        "Must follow: `<type>/<description>` or `<type>/<task-id>-<description>`\n"
        "Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, "
        "`test`, `build`, `ci`, `chore`, `hotfix`, `release`\n"
        "Example: `feat/task-01-core-engine`"
    )
    return False, error_msg


def get_pr_commits(base_ref: str) -> List[str]:
    """Retrieves all commit messages in the current branch relative to the base branch."""
    try:
        cmd = ["git", "log", f"origin/{base_ref}..HEAD", "--pretty=format:%s"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            cmd = ["git", "log", f"{base_ref}..HEAD", "--pretty=format:%s"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return [c.strip() for c in res.stdout.strip().split("\n") if c.strip()]
    except Exception as exc:
        print(f"Warning: Failed to inspect git log: {exc}", file=sys.stderr)
        return []


def validate_commit(commit_msg: str) -> Tuple[bool, str]:
    """Validates an individual commit message against conventional rules."""
    if any(commit_msg.startswith(prefix) for prefix in ("Merge ", "Revert ", "v")):
        return True, ""

    match = COMMIT_REGEX.match(commit_msg)
    if not match:
        error_msg = (
            f"Invalid commit format: `{commit_msg}`\n"
            "Required: `<type>(<scope>): [<TASK-ID>:#<NUM>] <description>` or "
            "`<type>(<scope>): [<TASK-ID>] <description>`\n"
            "Example: `feat(core): [TASK-01:#1] implement calculation engine`"
        )
        return False, error_msg

    raw_task_tag = match.group(5)
    if raw_task_tag:
        task_id = raw_task_tag.split(":")[0].upper()
        if task_id not in RESERVED_TAGS:
            issues_dir = os.path.join(os.path.dirname(__file__), "..", ".github", "issues")
            if os.path.isdir(issues_dir) and os.listdir(issues_dir):
                lower_id = task_id.lower()
                matching = [f for f in os.listdir(issues_dir) if lower_id in f.lower()]
                if not matching:
                    error_msg = (
                        f"Task `[{task_id}]` does not exist in `.github/issues/`.\n"
                        "Use a registered task file or a reserved tag: "
                        f"{', '.join(sorted(RESERVED_TAGS))}"
                    )
                    return False, error_msg

    return True, ""


def close_pull_request(pr_number: str, comment_body: str) -> None:
    """Comments feedback and automatically closes the Pull Request."""
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not gh_token or not pr_number:
        print("Notice: GITHUB_TOKEN or PR number missing. Skipping auto-close.")
        return

    try:
        print(f"Closing PR #{pr_number} due to governance policy violation...")
        comment_cmd = ["gh", "pr", "comment", str(pr_number), "--body", comment_body]
        subprocess.run(comment_cmd, check=False)
        close_cmd = ["gh", "pr", "close", str(pr_number)]
        subprocess.run(close_cmd, check=False)
        print(f"✔ PR #{pr_number} successfully closed.")
    except Exception as exc:
        print(f"Failed to auto-close PR #{pr_number}: {exc}", file=sys.stderr)


def main() -> None:
    """CLI orchestrator for branch and commit linting."""
    parser = argparse.ArgumentParser(description="Lint branch and commits.")
    parser.add_argument("--branch", default="", help="Branch name")
    parser.add_argument("--base", default="main", help="Base branch")
    parser.add_argument("--pr-number", default="", help="Pull request number")
    args = parser.parse_args()

    branch = args.branch or os.environ.get("GITHUB_HEAD_REF", "")
    violations: List[str] = []

    if branch:
        branch_ok, branch_err = validate_branch(branch)
        if not branch_ok:
            violations.append(f"### 🌿 Branch Name Violation\n{branch_err}")

    commits = get_pr_commits(args.base)
    for commit in commits:
        commit_ok, commit_err = validate_commit(commit)
        if not commit_ok:
            violations.append(f"### 📝 Commit Message Violation\n{commit_err}")

    if violations:
        report = (
            "## ⛔ Quality Gate Rejected: Governance Policy Violation\n\n"
            "This Pull Request has been automatically closed because it violates the repository "
            "governance standards:\n\n" + "\n\n".join(violations) + "\n\n---\n"
            "💡 **How to fix:**\n"
            "1. Rename your local branch: `git branch -m <valid-name>`\n"
            "2. Amend non-compliant commits: `git commit --amend` or `git rebase -i`\n"
            "3. Force push and reopen a new Pull Request."
        )
        print("\n" + "=" * 70)
        print(" ⛔ REPOSITORY GOVERNANCE VIOLATIONS DETECTED")
        print("=" * 70)
        print(report)
        print("=" * 70 + "\n")

        if args.pr_number:
            close_pull_request(args.pr_number, report)

        sys.exit(1)

    print("✔ All branch naming and commit conventions passed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
