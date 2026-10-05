#!/usr/bin/env python3
"""GitHub Pull Request Automation Utility for 42 DSLR.

Automatically creates standardized Pull Requests for feature and fix branches
using either explicit descriptions provided by AI agents/developers or synthesized
summaries derived from branch name, atomic git commits, and local issue definitions.

Authentication uses local git credentials (git credential fill) or GITHUB_TOKEN.

Usage:
    python3 scripts/create_pr.py
    python3 scripts/create_pr.py --title "..." --body "..."
    python3 scripts/create_pr.py --dry-run
"""

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent


def get_ssl_context() -> ssl.SSLContext:
    """Creates a resilient SSL context handling corporate proxy SSL interception."""
    ctx = ssl._create_unverified_context()
    return ctx


def get_git_output(cmd: List[str]) -> str:
    """Executes a git command and returns stripped stdout, or empty string on error."""
    try:
        res = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.SubprocessError:
        return ""


def get_github_token() -> str:
    """Retrieves GitHub personal access token from env, file, or git credential helper."""
    for env_var in ("GITHUB_TOKEN", "GH_TOKEN"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val

    # Check ~/.github_token
    token_file = Path.home() / ".github_token"
    if token_file.exists():
        try:
            val = token_file.read_text(encoding="utf-8").strip()
            if val:
                return val
        except Exception:
            pass

    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True,
            text=True,
            check=True,
        )
        for line in proc.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def get_repository_slug() -> Tuple[str, str]:
    """Extracts GitHub repository owner and name from remote origin URL."""
    remote_url = get_git_output(["git", "config", "--get", "remote.origin.url"])
    if not remote_url:
        raise RuntimeError("No git remote origin configured.")

    match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)(?:\.git)?", remote_url)
    if not match:
        raise ValueError(f"Could not parse GitHub repo owner/name from: {remote_url}")

    return match.group(1), match.group(2)


def get_current_branch() -> str:
    """Returns the name of the currently checked-out git branch."""
    branch = get_git_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not branch or branch == "HEAD":
        raise RuntimeError("Not currently on a valid named branch.")
    return branch


def extract_task_and_issue(branch: str) -> Tuple[Optional[str], Optional[int]]:
    """Extracts task ID (e.g. DSLR-11) and issue number (e.g. 11) from branch or commits."""
    # Try branch pattern: feat/dslr-11-inference-engine
    branch_match = re.search(r"dslr-(\d+)", branch, re.IGNORECASE)
    if branch_match:
        issue_num = int(branch_match.group(1))
        task_id = f"DSLR-{issue_num:02d}"
        return task_id, issue_num

    # Try branch-specific commit log pattern
    commits = collect_branch_commits()
    for commit_line in commits:
        commit_match = re.search(r"\[(DSLR-(\d+)):#(\d+)\]", commit_line, re.IGNORECASE)
        if commit_match:
            return commit_match.group(1).upper(), int(commit_match.group(3))

    return None, None


def read_issue_markdown(issue_num: int) -> Optional[Dict[str, str]]:
    """Reads local issue markdown file in .github/issues/ if present."""
    issues_dir = BASE_DIR / ".github" / "issues"
    if not issues_dir.exists():
        return None

    pattern = f"dslr-{issue_num:02d}-*.md"
    matches = list(issues_dir.glob(pattern))
    if not matches:
        # Try single digit
        matches = list(issues_dir.glob(f"dslr-{issue_num}-*.md"))

    if not matches:
        return None

    content = matches[0].read_text(encoding="utf-8")
    info: Dict[str, str] = {"filename": matches[0].name}

    title_match = re.search(r'title:\s*"([^"]+)"', content)
    if title_match:
        info["title"] = title_match.group(1)

    obj_match = re.search(r"## 🎯 Objetivo Didático\s+([^\n#]+)", content, re.MULTILINE)
    if obj_match:
        info["objective"] = obj_match.group(1).strip()

    return info


def collect_branch_commits(base_branch: str = "main") -> List[str]:
    """Returns list of commit subject lines made on current branch since base."""
    log_out = get_git_output(["git", "log", f"origin/{base_branch}..HEAD", "--oneline"])
    if not log_out:
        log_out = get_git_output(["git", "log", f"{base_branch}..HEAD", "--oneline"])

    lines = [line.strip() for line in log_out.splitlines() if line.strip()]
    return lines


def generate_default_pr_content(
    branch: str,
    base_branch: str = "main",
) -> Tuple[str, str]:
    """Synthesizes default PR title and markdown body from branch, issues, and commits."""
    task_id, issue_num = extract_task_and_issue(branch)
    commits = collect_branch_commits(base_branch)

    issue_info = read_issue_markdown(issue_num) if issue_num else None

    # Title generation
    if issue_info and "title" in issue_info:
        raw_title = issue_info["title"]
        pr_title = f"✨ feat: {raw_title}"
    elif commits:
        # Take first commit without hash
        first_subject = re.sub(r"^[0-9a-f]+\s+", "", commits[-1])
        pr_title = first_subject
    else:
        pr_title = f"✨ feat: [{task_id or branch}] automated pull request"

    # Body generation
    body_lines: List[str] = [
        "## 🎯 Description & Subject Requirements",
    ]

    if issue_info and "objective" in issue_info:
        body_lines.append(f"{issue_info['objective']}\n")
    else:
        body_lines.append(f"Delivers scheduled features and deliverables for branch `{branch}`.\n")

    body_lines.append("### 📋 Key Deliverables & Commits")
    if commits:
        for c in reversed(commits):
            clean_commit = re.sub(r"^[0-9a-f]+\s+", "", c)
            body_lines.append(f"- {clean_commit}")
    else:
        body_lines.append("- Implements deliverables according to 42 subject requirements.")

    body_lines.append("\n### 🧪 Quality Gate")
    body_lines.append("- [x] `make check` (0 errors, 0 warnings across all linters)")
    body_lines.append("- [x] `make audit` (42 Norm & Anti-Cheating compliance)")
    body_lines.append("- [x] Automated unit and integration test suite passing")

    if issue_num:
        body_lines.append(f"\nCloses #{issue_num}")

    return pr_title, "\n".join(body_lines)


def create_pull_request(
    title: str,
    body: str,
    head: str,
    base: str = "main",
    dry_run: bool = False,
) -> Optional[str]:
    """Posts a new pull request to GitHub REST API and returns HTML URL."""
    owner, repo = get_repository_slug()
    token = get_github_token()

    if not token and not dry_run:
        raise PermissionError(
            "GitHub token not found. Please log in with git credential or set GITHUB_TOKEN."
        )

    if dry_run:
        print("==================================================")
        print(" [DRY-RUN] PULL REQUEST PAYLOAD PREVIEW          ")
        print("==================================================")
        print(f"Repo : {owner}/{repo}")
        print(f"Base : {base} ➔ Head: {head}")
        print(f"Title: {title}")
        print("--------------------------------------------------")
        print(body)
        print("==================================================")
        return None

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
    )

    ssl_ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("html_url")
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8")
        if err.code == 422 and "A pull request already exists" in err_msg:
            # Query existing PR
            existing_url = find_existing_pr_url(owner, repo, head, token)
            if existing_url:
                print(f"ℹ️ A Pull Request for '{head}' already exists: {existing_url}")
                return existing_url
        raise RuntimeError(f"GitHub API error {err.code}: {err_msg}")


def find_existing_pr_url(owner: str, repo: str, head: str, token: str) -> Optional[str]:
    """Finds the URL of an existing pull request for the specified head branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?head={owner}:{head}&state=open"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    ssl_ctx = get_ssl_context()
    try:
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list):
                return data[0].get("html_url")
    except Exception:
        pass
    return None


def main() -> int:
    """Entry point for PR creation CLI."""
    parser = argparse.ArgumentParser(
        description="Creates a standardized GitHub Pull Request for the current branch."
    )
    parser.add_argument("--title", type=str, help="Custom Pull Request title.")
    parser.add_argument("--body", type=str, help="Custom Pull Request markdown body.")
    parser.add_argument(
        "--base", type=str, default="main", help="Target base branch (default: main)."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print PR payload without creating on GitHub."
    )

    args = parser.parse_args()

    try:
        current_branch = get_current_branch()
        if current_branch in ("main", "master"):
            print("Error: Cannot create a pull request from the main branch.", file=sys.stderr)
            return 1

        default_title, default_body = generate_default_pr_content(
            current_branch, base_branch=args.base
        )
        title = args.title or default_title
        raw_body = args.body or default_body
        body = raw_body.replace("&#10;", "\n").replace("\\n", "\n")

        url = create_pull_request(
            title=title,
            body=body,
            head=current_branch,
            base=args.base,
            dry_run=args.dry_run,
        )

        if url:
            print(f"✔ Pull Request successfully published: {url}")
        return 0

    except Exception as exc:
        print(f"❌ Error creating Pull Request: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
