"""Integrity and test suite for Kaggle Competitions Hub."""

import subprocess
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent


def test_sync_submodules_status() -> None:
    """Verifies sync_submodules.py --status executes with exit code 0."""
    res = subprocess.run(
        [sys.executable, str(HUB_ROOT / "scripts" / "sync_submodules.py"), "--status"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "SUBMODULE HEALTH MATRIX" in res.stdout
    assert "01_kaggle-gemma4-developer-agent" in res.stdout


def test_add_competition_dry_run() -> None:
    """Verifies add_competition.py calculates next index and dry-runs successfully."""
    res = subprocess.run(
        [
            sys.executable,
            str(HUB_ROOT / "scripts" / "add_competition.py"),
            "--repo",
            "kaggle-arc-prize-2024",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "REGISTERING COMPETITION SUBMODULE #02" in res.stdout
    assert "02_kaggle-arc-prize-2024" in res.stdout


def test_generate_summary_execution() -> None:
    """Verifies generate_summary.py produces summary.md with cyberpunk signature."""
    res = subprocess.run(
        [sys.executable, str(HUB_ROOT / "scripts" / "generate_summary.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    summary_path = HUB_ROOT / "summary.md"
    assert summary_path.is_file()
    content = summary_path.read_text(encoding="utf-8")
    assert "foto_little.png" in content


def test_github_workflows_and_templates_exist() -> None:
    """Verifies required GitHub Actions workflows and templates exist."""
    workflows_dir = HUB_ROOT / ".github" / "workflows"
    assert (workflows_dir / "audit.yml").is_file()
    assert (workflows_dir / "branch_lint.yml").is_file()
    assert (workflows_dir / "submodule_sync.yml").is_file()
    assert (workflows_dir / "auto_discover.yml").is_file()
    assert (HUB_ROOT / ".github" / "dependabot.yml").is_file()
    assert (HUB_ROOT / ".github" / "pull_request_template.md").is_file()


def test_auto_discover_dry_run() -> None:
    """Verifies auto_discover_competitions.py executes with code 0 in dry-run mode."""
    res = subprocess.run(
        [
            sys.executable,
            str(HUB_ROOT / "scripts" / "auto_discover_competitions.py"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "KAGGLE HUB AUTONOMOUS DISCOVERY ENGINE" in res.stdout
    assert "Git hooks installed and verified" in res.stdout


def test_governance_documentation_files_exist() -> None:
    """Verifies standard governance files exist in the repository root."""
    assert (HUB_ROOT / "SECURITY.md").is_file()
    assert (HUB_ROOT / "CODE_OF_CONDUCT.md").is_file()
    assert (HUB_ROOT / "CONTRIBUTING.md").is_file()
    assert (HUB_ROOT / "CHANGELOG.md").is_file()


def test_update_changelog_check() -> None:
    """Verifies update_changelog.py --check scans submodules and exits 0."""
    res = subprocess.run(
        [sys.executable, str(HUB_ROOT / "scripts" / "update_changelog.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "AI CHANGELOG & MILESTONE SYNTHESIZER" in res.stdout
