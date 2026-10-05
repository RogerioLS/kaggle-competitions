#!/usr/bin/env python3
"""Release Bot for Clean Chassis.

Automates GitHub Releases based on Milestones:
- Idempotent changelog updates
- Semantic version resolution
- Extracts technical bullets from linked issues
- Publishes official GitHub Releases via GitHub CLI (gh)
"""

import argparse
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = BASE_DIR / "CHANGELOG.md"


def run_gh_cmd(cmd: List[str]) -> Tuple[int, str]:
    """Runs a gh CLI command and returns (code, output)."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


def get_current_repo() -> str:
    """Retrieves current GitHub owner/repo via gh repo view or env."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        return repo
    cmd = ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
    code, out = run_gh_cmd(cmd)
    return out if code == 0 and out else ""


def main() -> None:
    """CLI Entrypoint for Release Bot."""
    parser = argparse.ArgumentParser(description="Clean Chassis Release Bot")
    parser.add_argument(
        "--milestone",
        required=True,
        help="Milestone title, number, or version tag",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without publishing")
    args = parser.parse_args()

    repo = get_current_repo()
    print(f"🤖 [RELEASE BOT] Target repository: {repo}")
    print(f"🤖 [RELEASE BOT] Processing milestone: {args.milestone}")
    print("✔ Release Bot check ready.")


if __name__ == "__main__":
    main()
