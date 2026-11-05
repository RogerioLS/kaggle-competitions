#!/usr/bin/env python3
"""Autonomous Discovery and Registration Engine for Kaggle Competitions Hub.

Discovers uncataloged 'kaggle-*' repositories via GitHub API and local sibling workspaces,
enforces git hooks installation, creates a compliant feature branch, registers the
submodule, updates the README.md table, and integrates the changes via Pull Request or merge.

Usage:
    python3 scripts/auto_discover_competitions.py --dry-run
    python3 scripts/auto_discover_competitions.py --auto-merge
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set

HUB_ROOT = Path(__file__).resolve().parent.parent

# Import registration helpers from add_competition
sys.path.insert(0, str(HUB_ROOT))
from scripts.add_competition import (  # noqa: E402
    Colors,
    discover_next_index,
    register_submodule,
)


def ensure_githooks_installed() -> bool:
    """Verifies that .githooks are configured and executable in .git/hooks."""
    hooks_script = HUB_ROOT / "scripts" / "install-hooks.sh"
    if not hooks_script.is_file():
        print(f"{Colors.YELLOW}Warning: install-hooks.sh not found.{Colors.RESET}")
        return False

    print(f"{Colors.CYAN}🔒 [HOOKS] Ensuring Git hooks are active and compliant...{Colors.RESET}")
    res = subprocess.run(
        ["bash", str(hooks_script)],
        cwd=str(HUB_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0:
        print(f"{Colors.GREEN}✔ Local Git hooks installed and verified.{Colors.RESET}")
        return True
    print(f"{Colors.RED}❌ Failed to install Git hooks: {res.stderr}{Colors.RESET}")
    return False


def get_registered_submodule_urls() -> Set[str]:
    """Parses .gitmodules and returns normalized set of registered repository URLs and slugs."""
    gitmodules_path = HUB_ROOT / ".gitmodules"
    registered: Set[str] = set()

    if not gitmodules_path.is_file():
        return registered

    content = gitmodules_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("url ="):
            url = line.split("=", 1)[1].strip()
            registered.add(url.lower())
            slug = url.rstrip("/").split("/")[-1].replace(".git", "").lower()
            registered.add(slug)
        elif line.startswith("path ="):
            path_val = line.split("=", 1)[1].strip()
            # remove 01_, 02_ prefix
            clean_path = re.sub(r"^\d+_", "", path_val).lower()
            registered.add(clean_path)

    return registered


def discover_remote_github_repos(token: Optional[str]) -> List[Dict[str, str]]:
    """Discovers repositories starting with 'kaggle-' via GitHub REST API."""
    if not token:
        return []

    url = "https://api.github.com/user/repos?per_page=100&type=owner"
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Kaggle-Hub-AutoDiscover",
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, list):
                return []
            repos = []
            for item in data:
                name = item.get("name", "")
                if name.startswith("kaggle-") and name != "kaggle-competitions":
                    repos.append(
                        {
                            "name": name,
                            "url": item.get("ssh_url") or item.get("clone_url"),
                            "description": item.get("description") or "",
                        }
                    )
            return repos
    except Exception as exc:
        print(f"{Colors.YELLOW}Notice: GitHub API query: {exc}{Colors.RESET}")
        return []


def discover_local_sibling_repos() -> List[Dict[str, str]]:
    """Discovers repositories starting with 'kaggle-' in parent workspace folder."""
    parent_dir = HUB_ROOT.parent
    discovered = []

    if not parent_dir.is_dir():
        return discovered

    for entry in parent_dir.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if name.startswith("kaggle-") and "kaggle-competitions" not in name:
            git_dir = entry / ".git"
            if git_dir.exists():
                res = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=str(entry),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                url = res.stdout.strip()
                if url:
                    discovered.append(
                        {
                            "name": name,
                            "url": url,
                            "description": "Local workspace competition",
                        }
                    )

    return discovered


def collect_uncataloged_competitions(
    token: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Combines remote and local discoveries and returns uncataloged repositories."""
    registered = get_registered_submodule_urls()
    candidates: Dict[str, Dict[str, str]] = {}

    # 1. Query GitHub API
    for repo in discover_remote_github_repos(token):
        candidates[repo["name"].lower()] = repo

    # 2. Query Local Sibling Repositories
    for repo in discover_local_sibling_repos():
        candidates[repo["name"].lower()] = repo

    # 3. Filter out already registered
    uncataloged = []
    for name_lower, repo_data in candidates.items():
        if (
            name_lower not in registered
            and repo_data["url"].lower() not in registered
            and name_lower != "kaggle-competitions"
        ):
            uncataloged.append(repo_data)

    return sorted(uncataloged, key=lambda x: x["name"])


def process_discovery_pipeline(
    dry_run: bool = False,
    auto_merge: bool = False,
    token: Optional[str] = None,
) -> int:
    """Executes the complete discovery, branching, registration, and merge lifecycle."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}==================================================")
    print(" 🤖 KAGGLE HUB AUTONOMOUS DISCOVERY ENGINE")
    print(f"=================================================={Colors.RESET}")

    ensure_githooks_installed()

    uncataloged = collect_uncataloged_competitions(token)
    if not uncataloged:
        msg = "✔ All 'kaggle-*' repositories are fully registered and up to date!"
        print(f"\n{Colors.GREEN}{msg}{Colors.RESET}\n")
        return 0

    header = f"Found {len(uncataloged)} uncataloged competition repository(ies):"
    print(f"\n{Colors.CYAN}{header}{Colors.RESET}")
    for item in uncataloged:
        print(f"  - {item['name']} ({item['url']})")

    if dry_run:
        dry_msg = "✔ [DRY-RUN] Discovery scan complete. 0 changes written to git."
        print(f"\n{Colors.GREEN}{dry_msg}{Colors.RESET}\n")
        return 0

    for repo_info in uncataloged:
        name = repo_info["name"]
        url = repo_info["url"]
        next_idx = discover_next_index()
        branch_name = f"feat/register-{next_idx:02d}-{name}"

        print(f"\n{Colors.BOLD}{Colors.BLUE}──────────────────────────────────────────────────")
        print(f" 🚀 Processing: {name} (Submodule #{next_idx:02d})")
        print(f"──────────────────────────────────────────────────{Colors.RESET}")

        # 1. Create compliant feature branch
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=str(HUB_ROOT), check=True)

        # 2. Register Submodule and update README
        register_submodule(
            repo_input=url,
            title=name.replace("kaggle-", "").replace("-", " ").title(),
            dry_run=False,
        )

        # Update visual summary report
        summary_script = HUB_ROOT / "scripts" / "generate_summary.py"
        if summary_script.is_file():
            subprocess.run([sys.executable, str(summary_script)], cwd=str(HUB_ROOT), check=False)

        # 3. Commit with conventional format
        commit_msg = f"feat(hub): [INFRA] auto-register {next_idx:02d}_{name} submodule"
        subprocess.run(["git", "add", "."], cwd=str(HUB_ROOT), check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(HUB_ROOT), check=True)

        if auto_merge:
            print(f"{Colors.CYAN}🔀 Merging '{branch_name}' into 'main'...{Colors.RESET}")
            subprocess.run(["git", "checkout", "main"], cwd=str(HUB_ROOT), check=True)
            subprocess.run(
                ["git", "merge", branch_name, "--no-ff", "-m", f"Merge {branch_name}"],
                cwd=str(HUB_ROOT),
                check=True,
            )
            subprocess.run(["git", "branch", "-d", branch_name], cwd=str(HUB_ROOT), check=True)
            print(f"{Colors.GREEN}✔ Successfully merged '{branch_name}' into main!{Colors.RESET}")
        else:
            msg = f"📡 Pushing feature branch '{branch_name}' to origin..."
            print(f"{Colors.CYAN}{msg}{Colors.RESET}")
            subprocess.run(["git", "push", "origin", branch_name], cwd=str(HUB_ROOT), check=False)
            repo = os.environ.get("GITHUB_REPOSITORY")
            repo_arg = ["--repo", repo] if repo else []
            pr_cmd = [
                "gh",
                "pr",
                "create",
                *repo_arg,
                "--title",
                commit_msg,
                "--body",
                f"Auto-discovery registered competition submodule: `{name}`.",
                "--base",
                "main",
                "--head",
                branch_name,
            ]
            subprocess.run(pr_cmd, check=False)

    if auto_merge:
        print(f"{Colors.CYAN}📡 Pushing updated main branch to origin...{Colors.RESET}")
        try:
            subprocess.run(["git", "push", "origin", "main"], cwd=str(HUB_ROOT), check=True)
        except subprocess.CalledProcessError:
            warn_msg = (
                f"Notice: Direct push to 'main' rejected (branch protection enabled). "
                f"Opening Pull Request for '{branch_name}' instead..."
            )
            print(f"{Colors.YELLOW}{warn_msg}{Colors.RESET}")
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=str(HUB_ROOT), check=False)
            subprocess.run(["git", "push", "origin", branch_name], cwd=str(HUB_ROOT), check=False)
            repo = os.environ.get("GITHUB_REPOSITORY")
            repo_arg = ["--repo", repo] if repo else []
            pr_cmd = [
                "gh",
                "pr",
                "create",
                *repo_arg,
                "--title",
                "feat(hub): [INFRA] auto-register uncataloged competition",
                "--body",
                "Auto-discovery registered uncataloged competition repository into the hub.",
                "--base",
                "main",
                "--head",
                branch_name,
            ]
            subprocess.run(pr_cmd, check=False)

    print(f"\n{Colors.GREEN}✅ Auto-discovery pipeline completed successfully!{Colors.RESET}\n")
    return 0


def main() -> int:
    """CLI Entrypoint."""
    parser = argparse.ArgumentParser(
        description="Autonomous discovery and auto-registration engine for Kaggle Competitions Hub."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate scan without creating branches or modifying git",
    )
    parser.add_argument(
        "--auto-merge",
        action="store_true",
        help="Automatically merge the registration branch into main upon success",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"),
        help="GitHub personal access token for remote discovery",
    )

    args = parser.parse_args()
    return process_discovery_pipeline(
        dry_run=args.dry_run,
        auto_merge=args.auto_merge,
        token=args.token,
    )


if __name__ == "__main__":
    sys.exit(main())
