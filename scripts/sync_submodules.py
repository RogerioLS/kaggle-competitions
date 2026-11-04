#!/usr/bin/env python3
"""Submodule Synchronization and Status Utility for Kaggle Competitions Hub.

Provides bulk status discovery, uncommitted change detection, and one-command
updating across all registered competition submodules.

Usage:
    python3 scripts/sync_submodules.py --status
    python3 scripts/sync_submodules.py --update
    python3 scripts/sync_submodules.py --dry-run
"""

from __future__ import annotations

import argparse
import configparser
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

HUB_ROOT = Path(__file__).resolve().parent.parent


class Colors:
    """ANSI color codes for formatted terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


def parse_gitmodules() -> List[Dict[str, str]]:
    """Reads .gitmodules and extracts registered submodule specifications."""
    gitmodules_path = HUB_ROOT / ".gitmodules"
    if not gitmodules_path.is_file():
        return []

    config = configparser.ConfigParser()
    config.read(gitmodules_path)

    submodules = []
    for section in config.sections():
        path = config.get(section, "path", fallback="")
        url = config.get(section, "url", fallback="")
        name = section.replace("submodule ", "").strip('"')
        if path:
            submodules.append({"name": name, "path": path, "url": url})

    return sorted(submodules, key=lambda s: s["path"])


def inspect_submodule_status(submodule: Dict[str, str]) -> Dict[str, str]:
    """Queries git status and commit pointers for an individual submodule."""
    sub_path = HUB_ROOT / submodule["path"]
    status_info = {
        "name": submodule["name"],
        "path": submodule["path"],
        "commit": "N/A",
        "branch": "N/A",
        "clean": "N/A",
        "exists": str(sub_path.is_dir()),
    }

    if not sub_path.is_dir():
        status_info["clean"] = "Missing (Run git submodule update --init)"
        return status_info

    # 1. Query Current Commit SHA
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(sub_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            status_info["commit"] = proc.stdout.strip()
    except Exception:
        pass

    # 2. Query Branch
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(sub_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            status_info["branch"] = proc.stdout.strip()
    except Exception:
        pass

    # 3. Check for uncommitted working tree modifications
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(sub_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            changes = [line for line in proc.stdout.splitlines() if line.strip()]
            status_info["clean"] = "Clean" if not changes else f"⚠️ {len(changes)} modified file(s)"
    except Exception:
        pass

    return status_info


def display_status() -> int:
    """Displays terminal overview of all registered submodules."""
    submodules = parse_gitmodules()
    if not submodules:
        print(f"{Colors.YELLOW}No submodules found in .gitmodules.{Colors.RESET}")
        return 0

    sep = "=" * 74
    dash = "-" * 74
    print(f"\n{Colors.BOLD}{Colors.BLUE}{sep}")
    print(" 📊 KAGGLE COMPETITIONS HUB — SUBMODULE HEALTH MATRIX")
    print(f"{sep}{Colors.RESET}")
    hdr = f"{'Path / Directory':<35} {'Commit':<10} {'Branch':<12} {'Working Tree':<20}"
    print(f"{Colors.BOLD}{hdr}{Colors.RESET}")
    print(f"{Colors.BLUE}{dash}{Colors.RESET}")

    for sub in submodules:
        info = inspect_submodule_status(sub)
        color = Colors.GREEN if "Clean" in info["clean"] else Colors.YELLOW
        print(
            f"{info['path']:<35} "
            f"{info['commit']:<10} "
            f"{info['branch']:<12} "
            f"{color}{info['clean']:<20}{Colors.RESET}"
        )

    print(f"{Colors.BLUE}{dash}{Colors.RESET}\n")
    return 0


def update_submodules(dry_run: bool = False) -> int:
    """Updates all submodules to latest remote commits."""
    print(f"{Colors.BOLD}{Colors.CYAN}🔄 Syncing submodules to latest remote HEAD...{Colors.RESET}")
    if dry_run:
        msg = "[DRY-RUN] git submodule update --remote --merge simulated."
        print(f"{Colors.GREEN}✔ {msg}{Colors.RESET}")
        return 0

    cmd = ["git", "submodule", "update", "--remote", "--merge"]
    try:
        proc = subprocess.run(cmd, cwd=str(HUB_ROOT), capture_output=True, text=True, check=True)
        print(f"{Colors.GREEN}✔ Submodules synchronized successfully!{Colors.RESET}")
        if proc.stdout:
            print(proc.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Synchronization failed: {e.stderr}{Colors.RESET}")
        return e.returncode


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Inspect status or update all Kaggle competition submodules."
    )
    parser.add_argument(
        "--status",
        "-s",
        action="store_true",
        help="Display health status table of all submodules",
    )
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="Update all submodules to remote HEAD",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operation without modifying git state",
    )

    args = parser.parse_args()

    if args.update:
        return update_submodules(dry_run=args.dry_run)

    # Default action is displaying status
    return display_status()


if __name__ == "__main__":
    sys.exit(main())
