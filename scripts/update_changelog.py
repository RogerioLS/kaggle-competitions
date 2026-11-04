#!/usr/bin/env python3
"""AI-Driven Changelog Synthesizer and Milestone Tracker.

Inspects upstream submodule commits during synchronization, filters for relevant
engineering milestones, and curates high-level project narrative entries in CHANGELOG.md.

Usage:
    python3 scripts/update_changelog.py --check
    python3 scripts/update_changelog.py --write
    python3 scripts/update_changelog.py --entry "Gemma 4: Reached Stage 6 - LoRA inference"
"""

from __future__ import annotations

import argparse
import configparser
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HUB_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = HUB_ROOT / "CHANGELOG.md"


class Colors:
    """ANSI color codes."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def get_submodules() -> List[Dict[str, str]]:
    """Discovers submodules registered in .gitmodules."""
    gitmodules_path = HUB_ROOT / ".gitmodules"
    if not gitmodules_path.is_file():
        return []

    config = configparser.ConfigParser()
    config.read(gitmodules_path)

    submodules = []
    for section in config.sections():
        path = config.get(section, "path", fallback="")
        if path:
            submodules.append(
                {
                    "name": section.replace("submodule ", "").strip('"'),
                    "path": path,
                }
            )
    return sorted(submodules, key=lambda s: s["path"])


def get_recent_submodule_commits(sub_path: Path, max_count: int = 10) -> List[str]:
    """Retrieves recent commit subjects from a submodule."""
    if not sub_path.is_dir():
        return []

    try:
        proc = subprocess.run(
            ["git", "log", f"-n{max_count}", "--pretty=format:%s"],
            cwd=str(sub_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception:
        pass
    return []


def is_relevant_milestone(commit_msg: str) -> bool:
    """Filters out trivial chores or merge commits, focusing on architectural milestones."""
    lower = commit_msg.lower()
    # Exclude internal merge noise and routine bump commits
    if lower.startswith("merge pull request") or lower.startswith("bump "):
        return False
    if "typo" in lower or "format" in lower or "cleanup" in lower:
        return False

    # High-relevance indicators
    keywords = [
        "feat",
        "lora",
        "agent",
        "gpu",
        "benchmark",
        "submission",
        "dataset",
        "architecture",
        "stage",
        "vllm",
        "swe-bench",
        "react",
        "pipeline",
        "harness",
    ]
    return any(kw in lower for kw in keywords)


def clean_milestone_text(commit_msg: str) -> str:
    """Strips conventional tags and formats commit message into a public project update."""
    # Remove conventional prefix: feat(core): [TASK-01:#1] ->
    cleaned = re.sub(r"^[a-zA-Z]+\([^)]*\):\s*", "", commit_msg)
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned.strip()


def synthesize_milestones() -> List[Tuple[str, List[str]]]:
    """Inspects all submodules and compiles high-level milestones."""
    submodules = get_submodules()
    compiled: List[Tuple[str, List[str]]] = []

    for sub in submodules:
        sub_dir = HUB_ROOT / sub["path"]
        commits = get_recent_submodule_commits(sub_dir, max_count=15)
        milestones = []
        for c in commits:
            if is_relevant_milestone(c):
                text = clean_milestone_text(c)
                if text and text not in milestones:
                    milestones.append(text)
        if milestones:
            compiled.append((sub["name"], milestones[:5]))

    return compiled


def update_changelog_content(new_bullets: List[str]) -> bool:
    """Injects new bullet points into CHANGELOG.md under ## [Unreleased]."""
    if not CHANGELOG_PATH.is_file():
        return False

    content = CHANGELOG_PATH.read_text(encoding="utf-8")
    if "## [Unreleased]" not in content:
        err = "❌ Error: '## [Unreleased]' section not found in CHANGELOG.md."
        print(f"{Colors.RED}{err}{Colors.RESET}")
        return False

    # Check which bullets are not yet present in CHANGELOG.md
    unique_bullets = [b for b in new_bullets if b not in content]
    if not unique_bullets:
        msg = "ℹ️ No new uncataloged milestones found. CHANGELOG.md is up to date."
        print(f"{Colors.YELLOW}{msg}{Colors.RESET}")
        return False

    parts = content.split("## [Unreleased]", 1)
    header = parts[0] + "## [Unreleased]\n"
    rest = parts[1]

    # Find or create ### Added
    injection = "\n".join(f"- {b}" for b in unique_bullets) + "\n"

    if "\n### Added\n" in rest:
        rest = rest.replace("\n### Added\n", f"\n### Added\n{injection}", 1)
    else:
        rest = f"\n### Added\n{injection}" + rest

    new_content = header + rest
    CHANGELOG_PATH.write_text(new_content, encoding="utf-8")
    success_msg = f"✔ Injected {len(unique_bullets)} new milestone(s) into CHANGELOG.md."
    print(f"{Colors.GREEN}{success_msg}{Colors.RESET}")
    return True


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="AI-driven changelog synthesizer and milestone tracker."
    )
    parser.add_argument(
        "--check",
        "-c",
        action="store_true",
        help="Scan submodules and display discovered milestones without writing",
    )
    parser.add_argument(
        "--write",
        "-w",
        action="store_true",
        help="Extract and write discovered milestones into CHANGELOG.md",
    )
    parser.add_argument(
        "--entry",
        "-e",
        type=str,
        default=None,
        help="Manually inject a specific milestone description",
    )

    args = parser.parse_args()

    if args.entry:
        entry_text = clean_milestone_text(args.entry)
        update_changelog_content([entry_text])
        return 0

    print(f"\n{Colors.BOLD}{Colors.BLUE}==================================================")
    print(" 🧠 AI CHANGELOG & MILESTONE SYNTHESIZER")
    print(f"=================================================={Colors.RESET}")

    milestones_by_sub = synthesize_milestones()
    if not milestones_by_sub:
        print(f"{Colors.YELLOW}No active submodules or recent commits found.{Colors.RESET}\n")
        return 0

    flat_bullets: List[str] = []
    for sub_name, items in milestones_by_sub:
        print(f"\n{Colors.CYAN}Submodule: {sub_name}{Colors.RESET}")
        for item in items:
            bullet = f"**{sub_name}**: {item}"
            print(f"  • {item}")
            flat_bullets.append(bullet)

    if args.check or not args.write:
        check_msg = (
            f"✔ Discovered {len(flat_bullets)} potential milestone(s). "
            "(Use --write to commit to CHANGELOG.md)"
        )
        print(f"\n{Colors.GREEN}{check_msg}{Colors.RESET}\n")
        return 0

    if args.write:
        update_changelog_content(flat_bullets)

    return 0


if __name__ == "__main__":
    sys.exit(main())
