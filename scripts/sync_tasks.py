#!/usr/bin/env python3
"""Sync GitHub Issues to local .github/issues/ directory.

Queries open/closed issues via GitHub CLI ('gh') and ensures local Markdown
task templates stay dynamically up-to-date with new issues created on the Web UI.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ISSUES_DIR = BASE_DIR / ".github" / "issues"


def main() -> None:
    """Fetches GitHub issues and syncs local task markdown files."""
    ISSUES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        cmd = [
            "gh",
            "issue",
            "list",
            "--limit",
            "100",
            "--state",
            "all",
            "--json",
            "number,title,body,labels,milestone",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issues = json.loads(result.stdout)
    except FileNotFoundError:
        print("❌ gh CLI is not installed. Please install 'gh' to sync tasks.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ℹ️ Skipping sync: Unable to reach GitHub API: {e.stderr.strip()}")
        return

    synced = 0
    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body", "")
        # Extract task identifier e.g. [DSLR-01] or [LR-02]
        match = re.search(r"\[([A-Za-z0-9_-]+)\]", title)
        if match:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            target_file = ISSUES_DIR / f"{slug}.md"

            # Only write if file doesn't exist or is empty
            if not target_file.exists() or target_file.stat().st_size == 0:
                target_file.write_text(body or f"# {title}\n", encoding="utf-8")
                print(f"➕ Synced task file: {target_file.name}")
                synced += 1

    print(f"✔ Sync complete! {synced} new task file(s) synchronized.")


if __name__ == "__main__":
    main()
