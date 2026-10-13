"""Unit tests for Kaggle competition submission CLI and offline kernel runner.

Validates credential discovery, pre-submission validation, CLI dispatch, and
offline kernel prediction generation.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import patch

from competitions.gemma_developer_agent.evaluation.dataset_loader import (
    SWEInstance,
)
from competitions.gemma_developer_agent.submission.kaggle_kernel import (
    KaggleOfflineKernelRunner,
    KernelPrediction,
)
from competitions.gemma_developer_agent.submission.packager import (
    package_submission,
)
from scripts.submit_kaggle import (
    compute_file_sha256,
    execute_kaggle_submission,
    find_kaggle_credentials,
    query_submission_status,
    validate_submission_package,
)


class TestKaggleCredentials:
    """Verifies Kaggle API credential discovery mechanisms."""

    def test_find_credentials_from_env(self, monkeypatch) -> None:
        """Discovers credentials when KAGGLE_USERNAME and KAGGLE_KEY are set."""
        monkeypatch.setenv("KAGGLE_USERNAME", "test_user")
        monkeypatch.setenv("KAGGLE_KEY", "test_key_123")

        creds = find_kaggle_credentials()
        assert creds == ("test_user", "test_key_123")

    def test_find_credentials_from_file(self, tmp_path, monkeypatch) -> None:
        """Discovers credentials from ~/.kaggle/kaggle.json when env is empty."""
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        kaggle_dir = tmp_path / ".kaggle"
        kaggle_dir.mkdir(parents=True, exist_ok=True)
        kaggle_file = kaggle_dir / "kaggle.json"
        kaggle_file.write_text(
            json.dumps({"username": "file_user", "key": "file_key_456"}),
            encoding="utf-8",
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            creds = find_kaggle_credentials()
            assert creds == ("file_user", "file_key_456")

    def test_find_credentials_none_found(self, tmp_path, monkeypatch) -> None:
        """Returns None when no credentials are configured in env or home directory."""
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        with patch("pathlib.Path.home", return_value=tmp_path):
            creds = find_kaggle_credentials()
            assert creds is None


class TestSubmitKaggleCLI:
    """Verifies Kaggle CLI submission and validation workflows."""

    def test_sha256_computation(self, tmp_path) -> None:
        """Verifies accurate SHA-256 calculation."""
        sample_file = tmp_path / "sample.txt"
        sample_file.write_text("Clean Chassis Testing", encoding="utf-8")

        sha = compute_file_sha256(sample_file)
        assert len(sha) == 64
        assert isinstance(sha, str)

    def test_validate_package_nonexistent(self, tmp_path) -> None:
        """Validator reports error for non-existent file path."""
        nonexistent = tmp_path / "does_not_exist.zip"
        is_valid, errors = validate_submission_package(nonexistent)

        assert is_valid is False
        assert any("not found" in e for e in errors)

    def test_validate_package_valid(self, tmp_path) -> None:
        """Validator passes for standard packaged submission."""
        zip_path = tmp_path / "valid_submission.zip"
        package_submission(output_path=zip_path)

        is_valid, errors = validate_submission_package(zip_path)
        assert is_valid is True
        assert len(errors) == 0

    def test_execute_submission_dry_run(self, tmp_path) -> None:
        """Dry-run execution outputs payload preview and exits cleanly with 0."""
        zip_path = tmp_path / "submission.zip"
        package_submission(output_path=zip_path)

        code = execute_kaggle_submission(
            competition="gemma-4-developer-agent",
            package_path=zip_path,
            message="Test dry-run submission",
            dry_run=True,
        )
        assert code == 0

    def test_execute_submission_missing_credentials(self, tmp_path, monkeypatch) -> None:
        """Live submission without credentials halts with exit code 1."""
        monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
        monkeypatch.delenv("KAGGLE_KEY", raising=False)

        zip_path = tmp_path / "submission.zip"
        package_submission(output_path=zip_path)

        with patch("pathlib.Path.home", return_value=tmp_path):
            code = execute_kaggle_submission(
                competition="gemma-4-developer-agent",
                package_path=zip_path,
                message="Live submission without creds",
                dry_run=False,
            )
            assert code == 1

    def test_query_submission_status_dry_run(self) -> None:
        """Status query returns 0 in dry-run mode."""
        code = query_submission_status(competition="gemma-4-developer-agent", dry_run=True)
        assert code == 0


class TestKaggleOfflineKernel:
    """Verifies offline execution kernel inside Kaggle sandbox environment."""

    def test_kernel_initialization_and_offline_verification(self, tmp_path) -> None:
        """Verifies runner initializes agent config and passes offline checks."""
        agent_yaml = (
            Path(__file__).resolve().parent.parent.parent
            / "competitions/gemma_developer_agent/agent/agent.yaml"
        )
        out_dir = tmp_path / "kernel_output"

        runner = KaggleOfflineKernelRunner(
            agent_config_path=agent_yaml,
            output_dir=out_dir,
            dry_run=True,
        )
        assert runner.verify_offline_environment() is True
        assert runner.agent_config.name == "gemma-4-developer-agent"

    def test_kernel_run_and_export_predictions(self, tmp_path) -> None:
        """Verifies predictions.jsonl and submission.csv artifacts generation."""
        agent_yaml = (
            Path(__file__).resolve().parent.parent.parent
            / "competitions/gemma_developer_agent/agent/agent.yaml"
        )
        out_dir = tmp_path / "kernel_output"

        runner = KaggleOfflineKernelRunner(
            agent_config_path=agent_yaml,
            output_dir=out_dir,
            dry_run=True,
        )

        sample_instances = [
            SWEInstance(
                instance_id="sample-inst-1",
                repo="sample/repo",
                base_commit="commit-1",
                problem_statement="Fix crash on none data",
            ),
            SWEInstance(
                instance_id="sample-inst-2",
                repo="sample/repo2",
                base_commit="commit-2",
                problem_statement="Handle missing key in dictionary",
            ),
        ]

        predictions = runner.run_on_instances(sample_instances, max_instances=2)
        assert len(predictions) == 2
        assert isinstance(predictions[0], KernelPrediction)
        assert predictions[0].instance_id == "sample-inst-1"
        assert "diff --git" in predictions[0].model_patch

        jsonl_path, csv_path = runner.export_submission_artifacts(predictions)
        assert jsonl_path.is_file()
        assert csv_path.is_file()

        # Validate JSONL content
        lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        entry = json.loads(lines[0])
        assert entry["instance_id"] == "sample-inst-1"

        # Validate CSV content
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            assert reader[0] == ["instance_id", "model_patch"]
            assert len(reader) == 3  # Header + 2 rows
            assert reader[1][0] == "sample-inst-1"
