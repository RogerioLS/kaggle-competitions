"""Unit tests for GitHub-to-Kaggle Dataset synchronization utility.

Validates credential discovery, dataset metadata generation, file collection filtering,
staging area preparation, and CLI execution under dry-run simulation.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts.sync_kaggle_dataset import (
    KaggleDatasetSync,
    find_kaggle_credentials,
    generate_dataset_metadata,
)


class TestKaggleCredentials:
    """Verifies Kaggle API credential discovery mechanisms."""

    def test_find_credentials_from_env(self, monkeypatch) -> None:
        """Discovers credentials when KAGGLE_USERNAME and KAGGLE_KEY are set."""
        monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
        monkeypatch.setenv("KAGGLE_USERNAME", "sync_user")
        monkeypatch.setenv("KAGGLE_KEY", "sync_key_123")

        creds = find_kaggle_credentials()
        assert creds == ("sync_user", "sync_key_123")

    def test_find_credentials_from_api_token(self, monkeypatch) -> None:
        """Discovers credentials from KAGGLE_API_TOKEN."""
        monkeypatch.setenv("KAGGLE_API_TOKEN", "KGAT_test123")
        monkeypatch.setenv("KAGGLE_USERNAME", "token_user")

        creds = find_kaggle_credentials()
        assert creds == ("token_user", "KGAT_test123")

    def test_find_credentials_from_file(self, tmp_path, monkeypatch) -> None:
        """Discovers credentials from ~/.kaggle/kaggle.json when env is empty."""
        monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        kaggle_dir = tmp_path / ".kaggle"
        kaggle_dir.mkdir(parents=True, exist_ok=True)
        kaggle_file = kaggle_dir / "kaggle.json"
        kaggle_file.write_text(
            json.dumps({"username": "file_sync_user", "key": "file_sync_key_456"}),
            encoding="utf-8",
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            creds = find_kaggle_credentials()
            assert creds == ("file_sync_user", "file_sync_key_456")

    def test_find_credentials_none_found(self, tmp_path, monkeypatch) -> None:
        """Returns None when no credentials are configured in env or home directory."""
        monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        with patch("pathlib.Path.home", return_value=tmp_path):
            creds = find_kaggle_credentials()
            assert creds is None


class TestDatasetMetadata:
    """Verifies Kaggle dataset-metadata.json creation and structure."""

    def test_generate_dataset_metadata_valid(self, tmp_path) -> None:
        """Generates valid JSON with title, id, and Apache 2.0 license."""
        meta_path = generate_dataset_metadata(
            dataset_slug="rogeriols/gemma-agent-code",
            title="Gemma 4 Developer Agent Codebase",
            target_dir=tmp_path,
        )

        assert meta_path.is_file()
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        assert data["id"] == "rogeriols/gemma-agent-code"
        assert data["title"] == "Gemma 4 Developer Agent Codebase"
        assert data["licenses"] == [{"name": "Apache 2.0"}]


class TestKaggleDatasetSync:
    """Verifies file collection, exclusion filtering, and staging area orchestration."""

    def test_is_path_excluded(self) -> None:
        """Verifies exclusion rules for git, caches, artifacts, and temp files."""
        sync = KaggleDatasetSync(dry_run=True)

        assert sync.is_path_excluded(Path(".git")) is True
        assert sync.is_path_excluded(Path(".git/config")) is True
        assert sync.is_path_excluded(Path(".github/workflows")) is True
        assert sync.is_path_excluded(Path("src/__pycache__/mod.cpython-310.pyc")) is True
        assert sync.is_path_excluded(Path(".pytest_cache/v/cache")) is True
        assert sync.is_path_excluded(Path("artifacts/submission.zip")) is True
        assert (
            sync.is_path_excluded(Path("competitions/gemma_developer_agent/agent/runner.py"))
            is False
        )
        assert sync.is_path_excluded(Path("pyproject.toml")) is False

    def test_collect_source_files(self) -> None:
        """Ensures core competition modules are collected and exclusions honored."""
        sync = KaggleDatasetSync(dry_run=True)
        files = sync.collect_source_files()

        assert len(files) > 0
        rel_paths = [str(rel) for _, rel in files]

        # Verify key modules exist in collected files
        assert any("competitions/gemma_developer_agent/agent/runner.py" in p for p in rel_paths)
        assert any("pyproject.toml" in p for p in rel_paths)

        # Verify excluded items do NOT exist
        assert not any(".git" in p for p in rel_paths)
        assert not any("__pycache__" in p for p in rel_paths)
        assert not any("artifacts" in p for p in rel_paths)

    def test_prepare_staging_area(self, tmp_path) -> None:
        """Prepares staging directory containing files and dataset-metadata.json."""
        staging_dir = tmp_path / "staging"
        sync = KaggleDatasetSync(
            dataset_slug="rogeriols/gemma-agent-code",
            staging_dir=staging_dir,
            dry_run=True,
        )

        prepared_dir, count, total_bytes = sync.prepare_staging_area()

        assert prepared_dir == staging_dir
        assert count > 0
        assert total_bytes > 0
        assert (staging_dir / "dataset-metadata.json").is_file()
        assert (staging_dir / "pyproject.toml").is_file()

    def test_sync_dry_run(self, tmp_path) -> None:
        """Executes sync in dry-run mode without external network calls."""
        staging_dir = tmp_path / "staging"
        sync = KaggleDatasetSync(
            dataset_slug="rogeriols/gemma-agent-code",
            staging_dir=staging_dir,
            dry_run=True,
        )

        exit_code = sync.sync()
        assert exit_code == 0
        assert (staging_dir / "dataset-metadata.json").is_file()

    def test_sync_missing_credentials_fails(self, tmp_path, monkeypatch) -> None:
        """Live sync returns non-zero when credentials are absent."""
        monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        staging_dir = tmp_path / "staging"
        sync = KaggleDatasetSync(
            dataset_slug="rogeriols/gemma-agent-code",
            staging_dir=staging_dir,
            dry_run=False,
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            exit_code = sync.sync()
            assert exit_code == 1
