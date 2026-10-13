#!/usr/bin/env python3
"""Kaggle Competition Submission Utility for Gemma 4 Developer Agent.

Provides pre-submission package validation, offline constraint checking, credential
discovery, Kaggle CLI/API dispatch, and leaderboard status querying.

Usage:
    python3 scripts/submit_kaggle.py --dry-run
    python3 scripts/submit_kaggle.py --message "Gemma 4 LoRA Multi-Agent v1.0"
    python3 scripts/submit_kaggle.py --status
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from competitions.gemma_developer_agent.submission.validator import (  # noqa: E402
    SubmissionValidator,
)

DEFAULT_COMPETITION = "gemma-4-developer-agent"
DEFAULT_SUBMISSION_PATH = REPO_ROOT / "artifacts" / "submission.zip"


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


def compute_file_sha256(filepath: Path) -> str:
    """Computes hexadecimal SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_kaggle_credentials() -> Optional[Tuple[str, str]]:
    """Discovers Kaggle credentials from environment variables or ~/.kaggle/kaggle.json.

    Returns:
        Tuple of (username, key) or None if unconfigured.
    """
    user_env = os.environ.get("KAGGLE_USERNAME", "").strip()
    key_env = os.environ.get("KAGGLE_KEY", "").strip()
    if user_env and key_env:
        return user_env, key_env

    kaggle_json_path = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json_path.is_file():
        try:
            data = json.loads(kaggle_json_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                u = str(data.get("username", "")).strip()
                k = str(data.get("key", "")).strip()
                if u and k:
                    return u, k
        except Exception:
            pass

    return None


def validate_submission_package(package_path: Path) -> Tuple[bool, List[str]]:
    """Validates structure, size, and offline compliance of submission package.

    Returns:
        Tuple of (is_valid, error_list).
    """
    if not package_path.is_file():
        return False, [f"Submission archive not found at: {package_path}"]

    validator = SubmissionValidator(package_path)
    result = validator.validate()
    return result.passed, result.errors


def execute_kaggle_submission(
    competition: str,
    package_path: Path,
    message: str,
    dry_run: bool = False,
) -> int:
    """Dispatches submission archive to Kaggle competition via CLI or dry-run simulation.

    Args:
        competition: Kaggle competition slug.
        package_path: Path to submission.zip.
        message: Descriptive commit/submission message.
        dry_run: When True, simulates submission without invoking external networks.

    Returns:
        Exit code (0 on success, non-zero on failure).
    """
    sha256 = compute_file_sha256(package_path)
    size_bytes = package_path.stat().st_size
    creds = find_kaggle_credentials()

    print(f"{Colors.BOLD}{Colors.BLUE}==================================================")
    print(f" 🚀 KAGGLE SUBMISSION DISPATCH: {competition.upper()}")
    print(f"=================================================={Colors.RESET}")
    print(f"  Archive   : {package_path}")
    print(f"  Size      : {size_bytes:,} bytes")
    print(f"  SHA-256   : {sha256}")
    print(f'  Message   : "{message}"')
    print(f"  Auth User : {creds[0] if creds else 'None (Unconfigured)'}")
    print(f"{Colors.BLUE}--------------------------------------------------{Colors.RESET}")

    if dry_run:
        print(f"{Colors.GREEN}✔ [DRY-RUN] Package verified and formatted successfully!")
        print(f"✔ [DRY-RUN] Ready to submit to competition: '{competition}'{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}To submit live, run:{Colors.RESET}")
        print(f'  kaggle competitions submit -c {competition} -f {package_path} -m "{message}"\n')
        return 0

    if not creds:
        print(f"{Colors.RED}❌ Error: Kaggle API credentials not found.{Colors.RESET}")
        print("Please configure credentials via ~/.kaggle/kaggle.json or environment:")
        print('  export KAGGLE_USERNAME="your_username"')
        print('  export KAGGLE_KEY="your_api_key"')
        return 1

    # Check for kaggle CLI
    kaggle_bin = shutil.which("kaggle")
    if not kaggle_bin:
        print(f"{Colors.RED}❌ Error: 'kaggle' CLI not installed in environment.{Colors.RESET}")
        print("Install via: pip install kaggle")
        return 1

    cmd = [
        kaggle_bin,
        "competitions",
        "submit",
        "-c",
        competition,
        "-f",
        str(package_path),
        "-m",
        message,
    ]

    print(f"{Colors.CYAN}📡 Submitting archive to Kaggle...{Colors.RESET}")
    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = creds[0]
    env["KAGGLE_KEY"] = creds[1]

    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"{Colors.GREEN}✔ Submission successfully submitted!{Colors.RESET}")
        if proc.stdout:
            print(proc.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Submission failed with error code {e.returncode}:{Colors.RESET}")
        if e.stderr:
            print(e.stderr)
        return e.returncode


def query_submission_status(competition: str, dry_run: bool = False) -> int:
    """Queries and displays recent submissions for the competition."""
    print(
        f"{Colors.BOLD}{Colors.BLUE}📊 Querying recent submissions for: "
        f"{competition}{Colors.RESET}"
    )
    if dry_run:
        print(f"{Colors.GREEN}✔ [DRY-RUN] Status query simulated successfully.{Colors.RESET}")
        return 0

    kaggle_bin = shutil.which("kaggle")
    creds = find_kaggle_credentials()

    if not creds:
        print(f"{Colors.RED}❌ Error: Kaggle credentials not configured.{Colors.RESET}")
        return 1

    if not kaggle_bin:
        print(f"{Colors.RED}❌ Error: 'kaggle' CLI not installed.{Colors.RESET}")
        return 1

    cmd = [kaggle_bin, "competitions", "submissions", "-c", competition]
    env = os.environ.copy()
    env["KAGGLE_USERNAME"] = creds[0]
    env["KAGGLE_KEY"] = creds[1]

    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        if proc.stdout:
            print(proc.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Query failed: {e.stderr}{Colors.RESET}")
        return e.returncode


def main() -> int:
    """CLI Entrypoint for Kaggle submission automation."""
    parser = argparse.ArgumentParser(
        description="Kaggle Competition Submission Utility for Gemma 4 Developer Agent"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=str(DEFAULT_SUBMISSION_PATH),
        help=f"Path to submission archive (default: {DEFAULT_SUBMISSION_PATH})",
    )
    parser.add_argument(
        "--competition",
        type=str,
        default=DEFAULT_COMPETITION,
        help=f"Kaggle competition slug (default: {DEFAULT_COMPETITION})",
    )
    parser.add_argument(
        "--message",
        type=str,
        default="Gemma 4 Developer Agent: Declarative Multi-Agent + LoRA W4A16",
        help="Submission description message",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate validation and submission without network calls",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Query status of recent submissions instead of submitting",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip pre-submission validator check",
    )

    args = parser.parse_args()

    if args.status:
        return query_submission_status(args.competition, dry_run=args.dry_run)

    package_path = Path(args.file).resolve()
    if not args.skip_validation:
        print(f"{Colors.CYAN}🔍 Validating submission package before dispatch...{Colors.RESET}")
        is_valid, errors = validate_submission_package(package_path)
        if not is_valid:
            print(f"{Colors.RED}❌ Pre-submission validation failed:{Colors.RESET}")
            for err in errors:
                print(f"  - {err}")
            return 1
        print(f"{Colors.GREEN}✔ Pre-submission package validation passed!{Colors.RESET}\n")

    return execute_kaggle_submission(
        competition=args.competition,
        package_path=package_path,
        message=args.message,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
