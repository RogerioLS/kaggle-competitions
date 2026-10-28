"""Unit tests for Kaggle submission packaging and validation pipeline."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
import yaml

from competitions.gemma_developer_agent.submission.packager import (
    SubmissionPackager,
    package_submission,
)
from competitions.gemma_developer_agent.submission.validator import (
    SubmissionValidator,
    validate_submission,
    verify_submission_dry_run,
)


@pytest.fixture
def clean_artifacts_zip(tmp_path: Path) -> Path:
    """Creates a valid submission package in a temporary directory for tests."""
    zip_target = tmp_path / "test_submission.zip"
    target, manifest = package_submission(output_path=zip_target)
    assert target.is_file()
    assert manifest.total_files > 0
    return target


class TestSubmissionPackaging:
    """Verifies packaging logic, file inclusions, and manifest generation."""

    def test_package_creation_structure(self, clean_artifacts_zip: Path) -> None:
        """Verifies all mandatory files exist in generated submission.zip."""
        with zipfile.ZipFile(clean_artifacts_zip, "r") as zf:
            namelist = zf.namelist()

        assert "agent.yaml" in namelist
        assert "eval_config.yaml" in namelist
        assert "configs/sampling.yaml" in namelist
        assert "sub_agents/explorer.yaml" in namelist
        assert "sub_agents/locator.yaml" in namelist
        assert "sub_agents/drafter.yaml" in namelist
        assert "sub_agents/validator.yaml" in namelist
        assert "prompts/system.md" in namelist
        assert "prompts/explorer.md" in namelist
        assert "prompts/locator.md" in namelist
        assert "prompts/drafter.md" in namelist
        assert "prompts/validator.md" in namelist
        assert "skills/reproducer_writer/SKILL.md" in namelist
        assert "skills/git_diff_sanitizer/SKILL.md" in namelist

    def test_package_dry_run(self, tmp_path: Path) -> None:
        """Verifies dry-run does not write archive to disk."""
        target = tmp_path / "dry_run.zip"
        packager = SubmissionPackager(output_path=target)
        manifest = packager.create_package(dry_run=True)

        assert not target.exists()
        assert manifest.total_files >= 10
        assert manifest.archive_sha256 == "dry-run-skipped"

    def test_manifest_metadata_correctness(self, clean_artifacts_zip: Path) -> None:
        """Verifies manifest json file is created alongside zip."""
        manifest_file = clean_artifacts_zip.parent / "submission_manifest.json"
        assert manifest_file.is_file()
        content = manifest_file.read_text(encoding="utf-8")
        assert "submission_name" in content
        assert "archive_sha256" in content
        assert "files" in content

    def test_pre_packaging_prohibited_entrypoint_raises(self, tmp_path: Path) -> None:
        """Verifies packager aborts if prohibited agent.py is included."""
        packager = SubmissionPackager(output_path=tmp_path / "bad.zip")
        entries = [(tmp_path / "agent.yaml", "agent.yaml"), (tmp_path / "agent.py", "agent.py")]
        with pytest.raises(ValueError, match="Prohibited entrypoint"):
            packager.validate_pre_packaging(entries)

    def test_pre_packaging_prohibited_extension_raises(self, tmp_path: Path) -> None:
        """Verifies packager aborts if .sh or .exe is in root."""
        packager = SubmissionPackager(output_path=tmp_path / "bad.zip")
        entries = [(tmp_path / "agent.yaml", "agent.yaml"), (tmp_path / "run.sh", "run.sh")]
        with pytest.raises(ValueError, match="Prohibited file extension"):
            packager.validate_pre_packaging(entries)


class TestSubmissionValidator:
    """Verifies static and dynamic submission validation checks."""

    def test_valid_submission_passes(self, clean_artifacts_zip: Path) -> None:
        """Ensures a clean packaged submission passes all validator checks."""
        result = validate_submission(clean_artifacts_zip)
        assert result.passed is True
        assert len(result.errors) == 0
        assert result.checks["file_exists"] is True
        assert result.checks["archive_integrity"] is True
        assert result.checks["size_within_limits"] is True
        assert result.checks["no_prohibited_entrypoints"] is True
        assert result.checks["root_agent_yaml_present"] is True
        assert result.checks["schema_and_references"] is True
        assert result.checks["offline_compliance"] is True

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        """Validator reports error when archive file does not exist."""
        result = validate_submission(tmp_path / "non_existent.zip")
        assert result.passed is False
        assert result.checks["file_exists"] is False
        assert any("not found" in err for err in result.errors)

    def test_corrupt_zip_fails(self, tmp_path: Path) -> None:
        """Validator reports error when archive is not a valid zip."""
        bad_zip = tmp_path / "corrupt.zip"
        bad_zip.write_text("not a zip", encoding="utf-8")
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert result.checks["archive_integrity"] is False

    def test_missing_root_agent_yaml_fails(self, tmp_path: Path) -> None:
        """Validator reports error when root agent.yaml is missing."""
        bad_zip = tmp_path / "missing_agent.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("configs/sampling.yaml", "temp: 0.1\n")
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert result.checks["root_agent_yaml_present"] is False
        assert any("agent.yaml' is missing" in err for err in result.errors)

    def test_prohibited_agent_py_in_root_fails(self, tmp_path: Path) -> None:
        """Validator reports error if raw agent.py is included in root."""
        bad_zip = tmp_path / "has_agent_py.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("agent.yaml", "name: test\n")
            zf.writestr("agent.py", "print('hello')\n")
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert result.checks["no_prohibited_entrypoints"] is False
        assert any("agent.py" in err for err in result.errors)

    def test_prohibited_arbitrary_python_file_in_root_fails(self, tmp_path: Path) -> None:
        """Validator reports error if any .py script is present in root."""
        bad_zip = tmp_path / "has_script_py.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("agent.yaml", "name: test\n")
            zf.writestr("custom_script.py", "# code\n")
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert result.checks["no_prohibited_entrypoints"] is False

    def test_missing_referenced_prompt_fails(self, tmp_path: Path) -> None:
        """Validator reports error if agent.yaml references a nonexistent prompt."""
        bad_zip = tmp_path / "missing_prompt.zip"
        agent_spec = {
            "name": "agent",
            "version": "1.0",
            "model": "gemma",
            "budget": {"max_turns": 10, "timeout_seconds": 60},
            "system_prompt": "prompts/missing.md",
            "sub_agents": {"sub1": "sub_agents/sub1.yaml"},
            "workflow": {"sequence": ["sub1"]},
        }
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("agent.yaml", yaml.dump(agent_spec))
            zf.writestr("sub_agents/sub1.yaml", yaml.dump({"name": "sub1"}))
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert any("prompts/missing.md" in err for err in result.errors)

    def test_unsupported_tool_in_subagent_fails(self, tmp_path: Path) -> None:
        """Validator reports error if sub-agent config specifies invalid tool."""
        bad_zip = tmp_path / "bad_tool.zip"
        agent_spec = {
            "name": "agent",
            "version": "1.0",
            "model": "gemma",
            "budget": {"max_turns": 10, "timeout_seconds": 60},
            "system_prompt": "prompts/sys.md",
            "sub_agents": {"sub1": "sub_agents/sub1.yaml"},
            "workflow": {"sequence": ["sub1"]},
        }
        sub1_spec = {
            "name": "sub1",
            "prompt": "prompts/sub1.md",
            "allowed_tools": ["disallowed_network_call"],
        }
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("agent.yaml", yaml.dump(agent_spec))
            zf.writestr("prompts/sys.md", "# Sys\n")
            zf.writestr("prompts/sub1.md", "# Sub1\n")
            zf.writestr("sub_agents/sub1.yaml", yaml.dump(sub1_spec))
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert any("disallowed_network_call" in err for err in result.errors)

    def test_offline_url_violation_fails(self, tmp_path: Path) -> None:
        """Validator reports error if any config/prompt contains remote URLs."""
        bad_zip = tmp_path / "offline_violation.zip"
        agent_spec = {
            "name": "agent",
            "version": "1.0",
            "model": "gemma",
            "budget": {"max_turns": 10, "timeout_seconds": 60},
            "system_prompt": "prompts/sys.md",
            "sub_agents": {"sub1": "sub_agents/sub1.yaml"},
            "workflow": {"sequence": ["sub1"]},
        }
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("agent.yaml", yaml.dump(agent_spec))
            zf.writestr("prompts/sys.md", "Fetch remote telemetry from https://evil.com/leak\n")
            zf.writestr(
                "sub_agents/sub1.yaml",
                yaml.dump({"name": "sub1", "prompt": "prompts/sub1.md", "allowed_tools": []}),
            )
            zf.writestr("prompts/sub1.md", "Sub prompt\n")
        result = validate_submission(bad_zip)
        assert result.passed is False
        assert result.checks["offline_compliance"] is False
        assert any("https://evil.com/leak" in err for err in result.errors)

    def test_archive_size_limit_exceeded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Validator flags archive when compressed size exceeds limit."""
        target = tmp_path / "oversize.zip"
        with zipfile.ZipFile(target, "w") as zf:
            zf.writestr("agent.yaml", "name: test\n")
        target_mod = "competitions.gemma_developer_agent.submission.validator"
        monkeypatch.setattr(f"{target_mod}.MAX_CODE_SUBMISSION_SIZE_BYTES", 10)
        validator = SubmissionValidator(target)
        result = validator.validate()
        assert result.passed is False
        assert result.checks["size_within_limits"] is False

    def test_dry_run_execution_passes(self, clean_artifacts_zip: Path) -> None:
        """Executes sandbox dry-run against the packaged submission archive."""
        dry_run_success = verify_submission_dry_run(clean_artifacts_zip)
        assert dry_run_success is True
