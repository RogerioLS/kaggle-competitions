#!/usr/bin/env python3
"""Competition Registration Utility for Kaggle Competitions Hub.

Registers a newly created Kaggle repository as an ordered Git Submodule (01_, 02_, ...),
updates .gitmodules, and synchronizes the README.md index table.

Usage:
    python3 scripts/add_competition.py --repo kaggle-nfl-big-data-bowl-2027
    python3 scripts/add_competition.py --repo kaggle-arc-prize-2024 --title "ARC Prize"
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

HUB_ROOT = Path(__file__).resolve().parent.parent


class Colors:
    """ANSI color codes for terminal formatting."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


def discover_next_index() -> int:
    """Parses existing submodules to find the next sequential number (e.g. 01, 02)."""
    gitmodules_path = HUB_ROOT / ".gitmodules"
    if not gitmodules_path.is_file():
        return 1

    content = gitmodules_path.read_text(encoding="utf-8")
    matches = re.findall(r'\[submodule\s+"?(\d+)_', content)
    if not matches:
        return 1

    indices = [int(m) for m in matches]
    return max(indices) + 1


def format_repo_url(repo: str) -> Tuple[str, str]:
    """Normalizes repository input into SSH clone URL and clean slug.

    Args:
        repo: Repository slug or full URL.

    Returns:
        Tuple of (ssh_url, clean_name).
    """
    clean = repo.strip().rstrip("/")
    if clean.endswith(".git"):
        clean = clean[:-4]

    # Extract name part
    if "/" in clean:
        name = clean.split("/")[-1]
    else:
        name = clean

    if clean.startswith("git@") or clean.startswith("https://"):
        url = f"{clean}.git" if not clean.endswith(".git") else clean
    else:
        url = f"git@github.com:RogerioLS/{name}.git"

    return url, name


def update_readme_table(
    index_num: int,
    title: str,
    task: str,
    stack: str,
    status: str,
    submodule_dir: str,
    kaggle_url: Optional[str] = None,
) -> None:
    """Appends a new competition entry row to the README.md table."""
    readme_path = HUB_ROOT / "README.md"
    if not readme_path.is_file():
        return

    content = readme_path.read_text(encoding="utf-8")
    table_header = "| # | Competition | Domain / Task | Core Stack | Status | Submodule Pointer |"

    if table_header not in content:
        warn = "Warning: Table header not found in README.md. Skipping table update."
        print(f"{Colors.YELLOW}{warn}{Colors.RESET}")
        return

    comp_link = f"[{title}]({kaggle_url})" if kaggle_url else title
    new_row = (
        f"| **{index_num:02d}** | {comp_link} | {task} | {stack} | {status} | "
        f"[`{submodule_dir}`]({submodule_dir}) |"
    )

    lines = content.splitlines()
    insert_idx = -1

    # Find the last table row
    for i, line in enumerate(lines):
        if line.startswith(f"| **{index_num - 1:02d}** |") or (
            line.strip().startswith("|") and insert_idx != -1
        ):
            insert_idx = i

    if insert_idx != -1:
        lines.insert(insert_idx + 1, new_row)
    else:
        # Fallback: append after table divider
        for i, line in enumerate(lines):
            if line.startswith("|---|---|"):
                lines.insert(i + 1, new_row)
                break

    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    msg = f"✔ README.md competition index updated with row: {index_num:02d}"
    print(f"{Colors.GREEN}{msg}{Colors.RESET}")


def register_submodule(
    repo_input: str,
    title: Optional[str] = None,
    task: Optional[str] = "Machine Learning / Competitive AI",
    stack: Optional[str] = "Python, PyTorch, Clean Chassis",
    status: Optional[str] = "🚀 Active",
    kaggle_url: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Registers the repository as a submodule and updates project documentation."""
    next_idx = discover_next_index()
    url, clean_name = format_repo_url(repo_input)
    submodule_dir = f"{next_idx:02d}_{clean_name}"
    comp_title = title or clean_name.replace("kaggle-", "").replace("-", " ").title()

    print(f"{Colors.BOLD}{Colors.BLUE}==================================================")
    print(f" 🏆 REGISTERING COMPETITION SUBMODULE #{next_idx:02d}")
    print(f"=================================================={Colors.RESET}")
    print(f"  Repository URL  : {url}")
    print(f"  Submodule Path  : {submodule_dir}")
    print(f"  Title           : {comp_title}")
    print(f"  Task/Domain     : {task}")
    print(f"  Tech Stack      : {stack}")
    print(f"  Status          : {status}")
    print(f"{Colors.BLUE}--------------------------------------------------{Colors.RESET}")

    if dry_run:
        msg = "[DRY-RUN] Submodule registration simulated successfully."
        print(f"{Colors.GREEN}✔ {msg}{Colors.RESET}")
        return 0

    cmd = ["git", "submodule", "add", url, submodule_dir]
    print(f"{Colors.CYAN}📡 Executing: {' '.join(cmd)}{Colors.RESET}")

    try:
        subprocess.run(cmd, cwd=str(HUB_ROOT), check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Failed to add git submodule: {e}{Colors.RESET}")
        return e.returncode

    update_readme_table(
        index_num=next_idx,
        title=comp_title,
        task=task or "Machine Learning",
        stack=stack or "Clean Chassis",
        status=status or "🚀 Active",
        submodule_dir=submodule_dir,
        kaggle_url=kaggle_url,
    )

    print(f"{Colors.GREEN}✔ Submodule '{submodule_dir}' successfully registered!{Colors.RESET}")
    print(f"{Colors.BOLD}Next steps:{Colors.RESET}")
    print(f'  git commit -m "feat(hub): [INFRA] register {submodule_dir} submodule"')
    print("  git push origin main\n")
    return 0


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Register a newly created competition repository into the Kaggle Hub."
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        required=True,
        help="Repository name or URL (e.g. kaggle-nfl-big-data-bowl-2027)",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        default=None,
        help="Human-readable title for the competition",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="Competitive Machine Learning / Data Science",
        help="Domain or competition task description",
    )
    parser.add_argument(
        "--stack",
        type=str,
        default="Python, PyTorch, Clean Chassis",
        help="Core technical stack",
    )
    parser.add_argument(
        "--status",
        type=str,
        default="🚀 Active",
        help="Current competition status",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Official Kaggle competition URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate registration without invoking git",
    )

    args = parser.parse_args()
    return register_submodule(
        repo_input=args.repo,
        title=args.title,
        task=args.task,
        stack=args.stack,
        status=args.status,
        kaggle_url=args.url,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
