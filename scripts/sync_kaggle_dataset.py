#!/usr/bin/env python3
"""Automated Kaggle Dataset Synchronization Utility.

Packages and synchronizes codebase components (competitions, src, scripts) into a
versioned Kaggle Dataset to enable offline GPU notebook execution on Kaggle.

Usage:
    python3 scripts/sync_kaggle_dataset.py --dry-run
    python3 scripts/sync_kaggle_dataset.py --dataset-slug rogeriols/gemma-agent-code
    python3 scripts/sync_kaggle_dataset.py --message "Sync Gemma 4 agent runner update"
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_SLUG = "gemma-agent-code"
DEFAULT_DATASET_TITLE = "Gemma 4 Developer Agent Codebase"


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


def find_kaggle_credentials() -> Optional[Tuple[str, str]]:
    """Discovers Kaggle credentials from environment variables or ~/.kaggle/.

    Returns:
        Tuple of (username, key) or None if unconfigured.
    """
    # 1. Environment variables (highest priority)
    api_token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    if api_token:
        username = os.environ.get("KAGGLE_USERNAME", "").strip() or "rogeriolopesdasilva"
        return username, api_token

    user_env = os.environ.get("KAGGLE_USERNAME", "").strip()
    key_env = os.environ.get("KAGGLE_KEY", "").strip()
    if user_env and key_env:
        return user_env, key_env

    # 2. Configuration files in ~/.kaggle (fallback)
    token_file = Path.home() / ".kaggle" / "access_token"
    if token_file.is_file():
        try:
            tok = token_file.read_text(encoding="utf-8").strip()
            if tok:
                username = os.environ.get("KAGGLE_USERNAME", "").strip() or "rogeriolopesdasilva"
                return username, tok
        except Exception:
            pass

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


def generate_dataset_metadata(
    dataset_slug: str,
    title: str,
    target_dir: Path,
    licenses: Optional[List[Dict[str, str]]] = None,
) -> Path:
    """Generates dataset-metadata.json conforming to Kaggle API schema.

    Args:
        dataset_slug: Kaggle dataset identifier (e.g., username/slug or slug).
        title: Human-readable dataset title.
        target_dir: Directory where dataset-metadata.json will be written.
        licenses: Optional custom license list. Defaults to Apache 2.0.

    Returns:
        Path to the generated metadata file.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = target_dir / "dataset-metadata.json"

    payload = {
        "title": title,
        "id": dataset_slug,
        "licenses": licenses or [{"name": "Apache 2.0"}],
    }

    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return metadata_path


class KaggleDatasetSync:
    """Orchestrates codebase selective packaging and deployment to Kaggle Datasets."""

    EXCLUDED_PATTERNS = {
        ".git",
        ".github",
        ".githooks",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "artifacts",
        ".coverage",
        "htmlcov",
        ".DS_Store",
        "Thumbs.db",
        "*.tmp",
    }

    INCLUDED_TREES = [
        "competitions/gemma_developer_agent",
        "src",
        "scripts",
    ]

    INCLUDED_FILES = [
        "pyproject.toml",
        "README.md",
        "LICENSE",
    ]

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        dataset_slug: Optional[str] = None,
        title: Optional[str] = None,
        staging_dir: Optional[Path] = None,
        dry_run: bool = False,
    ) -> None:
        self.repo_root = Path(repo_root).resolve() if repo_root else REPO_ROOT
        self.dry_run = dry_run

        creds = find_kaggle_credentials()
        username = creds[0] if creds else "kaggle_user"

        raw_slug = dataset_slug or DEFAULT_DATASET_SLUG
        if "/" not in raw_slug:
            self.dataset_slug = f"{username}/{raw_slug}"
        else:
            self.dataset_slug = raw_slug

        self.title = title or DEFAULT_DATASET_TITLE
        self.staging_dir = (
            Path(staging_dir).resolve()
            if staging_dir
            else self.repo_root / "artifacts" / "kaggle_dataset_staging"
        )

    def is_path_excluded(self, rel_path: Path) -> bool:
        """Determines whether a relative path matches any exclusion rule."""
        parts = rel_path.parts
        for part in parts:
            for pattern in self.EXCLUDED_PATTERNS:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def collect_source_files(self) -> List[Tuple[Path, Path]]:
        """Collects files eligible for synchronization to the Kaggle Dataset.

        Returns:
            List of tuples mapping (absolute_source_path, relative_staging_path).
        """
        collected: List[Tuple[Path, Path]] = []

        # 1. Collect individual files
        for filename in self.INCLUDED_FILES:
            file_path = self.repo_root / filename
            if file_path.is_file() and not self.is_path_excluded(Path(filename)):
                collected.append((file_path, Path(filename)))

        # 2. Collect directory trees
        for tree_rel in self.INCLUDED_TREES:
            tree_path = self.repo_root / tree_rel
            if not tree_path.is_dir():
                continue

            for root, _, files in os.walk(tree_path):
                root_path = Path(root)
                rel_dir = root_path.relative_to(self.repo_root)

                if self.is_path_excluded(rel_dir):
                    continue

                for f in files:
                    file_path = root_path / f
                    rel_file = file_path.relative_to(self.repo_root)
                    if not self.is_path_excluded(rel_file):
                        collected.append((file_path, rel_file))

        return sorted(collected, key=lambda x: str(x[1]))

    def prepare_staging_area(self) -> Tuple[Path, int, int]:
        """Prepares staging directory with filtered files and metadata.

        Returns:
            Tuple of (staging_dir_path, total_file_count, total_bytes).
        """
        if self.staging_dir.exists():
            shutil.rmtree(self.staging_dir)

        self.staging_dir.mkdir(parents=True, exist_ok=True)

        files = self.collect_source_files()
        total_bytes = 0

        for src, rel in files:
            dest = self.staging_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            total_bytes += src.stat().st_size

        generate_dataset_metadata(
            dataset_slug=self.dataset_slug,
            title=self.title,
            target_dir=self.staging_dir,
        )

        metadata_size = (self.staging_dir / "dataset-metadata.json").stat().st_size
        total_bytes += metadata_size
        total_count = len(files) + 1  # Including metadata file

        return self.staging_dir, total_count, total_bytes

    def sync(self, message: Optional[str] = None) -> int:
        """Executes the dataset synchronization or dry-run simulation.

        Args:
            message: Version update description for Kaggle Dataset.

        Returns:
            Exit code (0 on success, non-zero on failure).
        """
        staging_path, file_count, total_bytes = self.prepare_staging_area()
        creds = find_kaggle_credentials()
        version_message = message or f"Automated sync: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"

        print(f"{Colors.BOLD}{Colors.BLUE}==================================================")
        print(" 🔄 KAGGLE DATASET SYNCHRONIZATION")
        print(f"=================================================={Colors.RESET}")
        print(f"  Dataset ID : {self.dataset_slug}")
        print(f"  Title      : {self.title}")
        print(f"  Files      : {file_count} files ({total_bytes:,} bytes)")
        print(f"  Staging    : {staging_path}")
        print(f"  Auth User  : {creds[0] if creds else 'None (Unconfigured)'}")
        print(f'  Version Msg: "{version_message}"')
        print(f"{Colors.BLUE}--------------------------------------------------{Colors.RESET}")

        if self.dry_run:
            print(f"{Colors.GREEN}✔ [DRY-RUN] Staging area prepared and validated successfully!")
            print(
                f"✔ [DRY-RUN] Ready to push to Kaggle Dataset: '{self.dataset_slug}'{Colors.RESET}"
            )
            print(f"{Colors.BOLD}{Colors.CYAN}To sync live, run:{Colors.RESET}")
            print(
                f"  kaggle datasets version -p {staging_path} "
                f'-m "{version_message}" --dir-mode zip\n'
            )
            return 0

        if not creds:
            print(f"{Colors.RED}❌ Error: Kaggle API credentials not found.{Colors.RESET}")
            print("Configure credentials via ~/.kaggle/kaggle.json or env variables:")
            print('  export KAGGLE_USERNAME="your_username"')
            print('  export KAGGLE_KEY="your_api_key"')
            return 1

        kaggle_bin = shutil.which("kaggle")
        if not kaggle_bin:
            print(f"{Colors.RED}❌ Error: 'kaggle' CLI not installed in environment.{Colors.RESET}")
            print("Install via: pip install kaggle")
            return 1

        # Check if dataset already exists on Kaggle
        status_cmd = [kaggle_bin, "datasets", "status", self.dataset_slug]
        check_proc = subprocess.run(status_cmd, capture_output=True, text=True)

        if check_proc.returncode == 0:
            print(
                f"{Colors.YELLOW}⚡ Dataset '{self.dataset_slug}' exists. "
                f"Creating new version...{Colors.RESET}"
            )
            push_cmd = [
                kaggle_bin,
                "datasets",
                "version",
                "-p",
                str(staging_path),
                "-m",
                version_message,
                "--dir-mode",
                "zip",
            ]
        else:
            print(
                f"{Colors.YELLOW}⚡ Dataset '{self.dataset_slug}' does not exist. "
                f"Creating dataset...{Colors.RESET}"
            )
            push_cmd = [
                kaggle_bin,
                "datasets",
                "create",
                "-p",
                str(staging_path),
                "--public",
                "--dir-mode",
                "zip",
            ]

        print(f"Executing: {' '.join(push_cmd)}")
        result = subprocess.run(push_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{Colors.GREEN}✔ Successfully synchronized dataset to Kaggle!{Colors.RESET}")
            if result.stdout:
                print(result.stdout)
            return 0

        print(
            f"{Colors.RED}❌ Kaggle sync command failed (code {result.returncode}):{Colors.RESET}"
        )
        if result.stderr:
            print(result.stderr)
        return result.returncode


def main() -> None:
    """CLI entrypoint for Kaggle dataset synchronization."""
    parser = argparse.ArgumentParser(
        description="Sync codebase components to a Kaggle Dataset for offline GPU execution.",
    )
    parser.add_argument(
        "--dataset-slug",
        type=str,
        default=None,
        help="Kaggle dataset slug (default: <username>/gemma-agent-code)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Human-readable dataset title",
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        default=None,
        help="Version update description for Kaggle Dataset",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate staging and packaging without executing Kaggle API calls",
    )

    args = parser.parse_args()

    sync_service = KaggleDatasetSync(
        dataset_slug=args.dataset_slug,
        title=args.title,
        dry_run=args.dry_run,
    )
    sys.exit(sync_service.sync(message=args.message))


if __name__ == "__main__":
    main()
