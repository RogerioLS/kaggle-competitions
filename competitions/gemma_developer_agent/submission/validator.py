"""Submission Validator and Dry-Run Verification for Gemma 4 Developer Agent.

Performs static and dynamic validation on Kaggle submission archives:
- Archive integrity and size bounds
- Absence of raw Python entrypoints (no agent.py in root)
- Mandatory declarative agent.yaml specification
- Prompt template and sub-agent reference completeness
- Tool permission enforcement (9 native sandbox tools)
- Offline sandbox compliance (zero external network URLs)
- Dynamic dry-run execution on synthetic SWE-bench instance
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from competitions.gemma_developer_agent.agent.schema import (  # noqa: E402
    SUPPORTED_TOOLS,
    AgentConfig,
)

MAX_CODE_SUBMISSION_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB max for code/prompts
MAX_ADAPTER_SUBMISSION_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB max when weights included
MAX_TURNS_UPPER_BOUND = 50
MAX_TIMEOUT_SECONDS_UPPER_BOUND = 1200


@dataclass
class ValidationResult:
    """Detailed results of submission validation."""

    passed: bool
    archive_path: str
    total_files: int
    uncompressed_size_bytes: int
    compressed_size_bytes: int
    checks: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        """Serializes result to formatted JSON string."""
        return json.dumps(asdict(self), indent=2)


class SubmissionValidator:
    """Enforces competition submission rules against a zip file or uncompressed directory."""

    NETWORK_URL_PATTERN = re.compile(
        r"\b(?:https?|ftp|ws|wss)://[^\s\"'>)]+",
        re.IGNORECASE,
    )

    DISALLOWED_ROOT_FILES = {"agent.py", "main.py", "runner.py", "submission.py"}
    DISALLOWED_OS_PATTERNS = {"__pycache__", ".DS_Store", "Thumbs.db", ".git"}

    def __init__(self, archive_path: Path) -> None:
        """Initializes validator for the specified submission archive path."""
        self.archive_path = Path(archive_path).resolve()

    def validate(self) -> ValidationResult:
        """Executes full suite of static verification checks on the submission archive.

        Returns:
            ValidationResult with detailed pass/fail status and messages.
        """
        checks: Dict[str, bool] = {}
        errors: List[str] = []
        warnings: List[str] = []

        if not self.archive_path.is_file():
            return ValidationResult(
                passed=False,
                archive_path=str(self.archive_path),
                total_files=0,
                uncompressed_size_bytes=0,
                compressed_size_bytes=0,
                checks={"file_exists": False},
                errors=[f"Submission archive not found: {self.archive_path}"],
            )

        checks["file_exists"] = True
        compressed_size = self.archive_path.stat().st_size

        # 1. Zip integrity check
        try:
            with zipfile.ZipFile(self.archive_path, "r") as zf:
                corrupt = zf.testzip()
                if corrupt is not None:
                    errors.append(f"Corrupt file detected in ZIP archive: {corrupt}")
                    checks["archive_integrity"] = False
                else:
                    checks["archive_integrity"] = True

                namelist = zf.namelist()
                infolist = zf.infolist()
                total_uncompressed = sum(info.file_size for info in infolist)
        except Exception as exc:
            return ValidationResult(
                passed=False,
                archive_path=str(self.archive_path),
                total_files=0,
                uncompressed_size_bytes=0,
                compressed_size_bytes=compressed_size,
                checks={"archive_integrity": False},
                errors=[f"Failed to read ZIP archive: {exc}"],
            )

        # 2. Size limit checks
        has_adapters = any(name.startswith("adapters/") for name in namelist)
        max_size = (
            MAX_ADAPTER_SUBMISSION_SIZE_BYTES if has_adapters else MAX_CODE_SUBMISSION_SIZE_BYTES
        )
        if compressed_size > max_size:
            errors.append(
                f"Archive size {compressed_size:,} bytes exceeds maximum limit "
                f"of {max_size:,} bytes."
            )
            checks["size_within_limits"] = False
        else:
            checks["size_within_limits"] = True

        # 3. Prohibited root entrypoints and OS junk
        has_prohibited = False
        for name in namelist:
            # Check OS junk
            for junk in self.DISALLOWED_OS_PATTERNS:
                if junk in name:
                    warnings.append(f"Detected OS artifact or cache in archive: '{name}'")

            # Check root files
            parts = name.split("/")
            if len(parts) == 1 and parts[0]:
                filename = parts[0]
                if filename in self.DISALLOWED_ROOT_FILES:
                    errors.append(
                        f"Prohibited executable entrypoint '{filename}' in root. "
                        "Kaggle requires declarative YAML agent execution."
                    )
                    has_prohibited = True
                if Path(filename).suffix.lower() == ".py":
                    errors.append(f"Python file '{filename}' found in archive root. Disallowed.")
                    has_prohibited = True

        checks["no_prohibited_entrypoints"] = not has_prohibited

        # 4. Mandatory root agent.yaml
        if "agent.yaml" not in namelist:
            errors.append("Mandatory root 'agent.yaml' is missing from submission archive.")
            checks["root_agent_yaml_present"] = False
        else:
            checks["root_agent_yaml_present"] = True

        # 5. Declarative schema and referenced file verification
        if checks.get("root_agent_yaml_present"):
            schema_ok, schema_errors = self._validate_declarative_schema(namelist)
            checks["schema_and_references"] = schema_ok
            errors.extend(schema_errors)

        # 6. Offline sandbox compliance (scan text files for remote URLs)
        offline_ok, offline_errors = self._validate_offline_compliance()
        checks["offline_compliance"] = offline_ok
        errors.extend(offline_errors)

        overall_passed = len(errors) == 0

        return ValidationResult(
            passed=overall_passed,
            archive_path=str(self.archive_path),
            total_files=len(namelist),
            uncompressed_size_bytes=total_uncompressed,
            compressed_size_bytes=compressed_size,
            checks=checks,
            errors=errors,
            warnings=warnings,
        )

    def _validate_declarative_schema(self, namelist: List[str]) -> Tuple[bool, List[str]]:
        """Extracts and verifies agent.yaml, sub-agent configs, and prompt templates."""
        errors: List[str] = []
        available_files: Set[str] = set(namelist)

        with zipfile.ZipFile(self.archive_path, "r") as zf:
            try:
                raw_yaml = zf.read("agent.yaml").decode("utf-8")
                agent_data = yaml.safe_load(raw_yaml)
            except Exception as exc:
                return False, [f"Failed to parse agent.yaml from archive: {exc}"]

            if not isinstance(agent_data, dict):
                return False, ["agent.yaml must contain a YAML mapping."]

            # Check required fields
            for req in ("name", "version", "model", "budget", "workflow", "sub_agents"):
                if req not in agent_data:
                    errors.append(f"Missing required field '{req}' in agent.yaml.")

            # Check budget limits
            budget = agent_data.get("budget", {})
            if isinstance(budget, dict):
                max_turns = budget.get("max_turns", 0)
                timeout = budget.get("timeout_seconds", 0)
                if max_turns > MAX_TURNS_UPPER_BOUND:
                    errors.append(
                        f"agent.yaml max_turns ({max_turns}) exceeds upper bound "
                        f"({MAX_TURNS_UPPER_BOUND})."
                    )
                if timeout > MAX_TIMEOUT_SECONDS_UPPER_BOUND:
                    errors.append(
                        f"agent.yaml timeout_seconds ({timeout}) exceeds upper bound "
                        f"({MAX_TIMEOUT_SECONDS_UPPER_BOUND})."
                    )

            # Check system prompt reference
            sys_prompt = agent_data.get("system_prompt", "prompts/system.md")
            if sys_prompt not in available_files:
                errors.append(f"Referenced system prompt '{sys_prompt}' not found in archive.")

            # Check sampling config
            sampling_cfg = agent_data.get("sampling_config")
            if sampling_cfg and sampling_cfg not in available_files:
                errors.append(f"Referenced sampling config '{sampling_cfg}' not found in archive.")

            # Check sub-agents
            sub_agents = agent_data.get("sub_agents", {})
            if not isinstance(sub_agents, dict) or not sub_agents:
                errors.append("agent.yaml must declare at least one sub-agent in 'sub_agents'.")
            else:
                for sa_name, sa_path in sub_agents.items():
                    if sa_path not in available_files:
                        errors.append(
                            f"Sub-agent '{sa_name}' config file '{sa_path}' missing in archive."
                        )
                        continue

                    # Read sub-agent config
                    try:
                        sa_raw = zf.read(sa_path).decode("utf-8")
                        sa_data = yaml.safe_load(sa_raw)
                        if isinstance(sa_data, dict):
                            # Validate prompt file
                            prompt_ref = sa_data.get("prompt", "")
                            if prompt_ref and prompt_ref not in available_files:
                                errors.append(
                                    f"Sub-agent '{sa_name}' prompt '{prompt_ref}' missing."
                                )

                            # Validate tools
                            tools = sa_data.get("allowed_tools", [])
                            for t in tools:
                                if t not in SUPPORTED_TOOLS:
                                    errors.append(
                                        f"Sub-agent '{sa_name}' references unsupported tool '{t}'."
                                    )
                    except Exception as e:
                        errors.append(f"Error parsing sub-agent '{sa_name}' config: {e}")

            # Check workflow
            workflow = agent_data.get("workflow", {})
            if isinstance(workflow, dict):
                sequence = workflow.get("sequence", [])
                for step in sequence:
                    if step not in sub_agents:
                        errors.append(
                            f"Workflow sequence step '{step}' not in declared sub_agents."
                        )

            # Check adapters if present in archive
            adapter_configs = [
                f
                for f in available_files
                if f.startswith("adapters/") and f.endswith("adapter_config.json")
            ]
            for ac_path in adapter_configs:
                try:
                    ac_raw = zf.read(ac_path).decode("utf-8")
                    ac_data = json.loads(ac_raw)
                    if not isinstance(ac_data, dict):
                        errors.append(f"Invalid JSON format in adapter config '{ac_path}'.")
                    elif ac_data.get("peft_type") != "LORA":
                        errors.append(
                            f"Adapter in '{ac_path}' has non-LoRA peft_type: "
                            f"{ac_data.get('peft_type')}"
                        )

                    # Check companion weights
                    adapter_dir = "/".join(ac_path.split("/")[:-1])
                    weight_found = any(
                        f.startswith(adapter_dir)
                        and (f.endswith(".safetensors") or f.endswith(".bin"))
                        for f in available_files
                    )
                    if not weight_found:
                        errors.append(
                            f"LoRA adapter in '{adapter_dir}' is missing weights "
                            "(.safetensors or .bin)."
                        )
                except Exception as e:
                    errors.append(f"Failed to validate adapter config '{ac_path}': {e}")

        return len(errors) == 0, errors

    def _validate_offline_compliance(self) -> Tuple[bool, List[str]]:
        """Ensures text configuration files do not reference external network URLs."""
        errors: List[str] = []
        text_extensions = {".yaml", ".yml", ".md", ".json", ".txt"}

        with zipfile.ZipFile(self.archive_path, "r") as zf:
            for info in zf.infolist():
                ext = Path(info.filename).suffix.lower()
                if ext in text_extensions:
                    try:
                        content = zf.read(info.filename).decode("utf-8")
                        matches = self.NETWORK_URL_PATTERN.findall(content)
                        if matches:
                            errors.append(
                                f"File '{info.filename}' contains remote network URLs: "
                                f"{matches}. Strict offline sandbox forbids external URLs."
                            )
                    except Exception:
                        pass

        return len(errors) == 0, errors


def validate_submission(archive_path: Path) -> ValidationResult:
    """Convenience function to run validation on a submission zip archive."""
    validator = SubmissionValidator(archive_path=archive_path)
    return validator.validate()


def verify_submission_dry_run(archive_path: Path) -> bool:
    """Unpacks submission archive into isolated sandbox and executes end-to-end dry-run.

    Args:
        archive_path: Path to submission.zip archive.

    Returns:
        True if dry-run executes cleanly and produces a patch, False otherwise.
    """
    from competitions.gemma_developer_agent.agent.runner import (
        DeclarativeAgentRunner,
    )
    from competitions.gemma_developer_agent.evaluation.dataset_loader import (
        DatasetLoader,
    )
    from competitions.gemma_developer_agent.evaluation.harness import (
        LocalSWEHarness,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Unpack archive
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(tmp_path)

        agent_yaml = tmp_path / "agent.yaml"
        if not agent_yaml.is_file():
            raise FileNotFoundError("Unpacked submission missing root agent.yaml.")

        # Load declarative configuration
        config = AgentConfig.from_yaml(agent_yaml)
        runner = DeclarativeAgentRunner(config=config)
        harness = LocalSWEHarness(base_dir=tmp_path / "harness")

        # Create temporary mock instance
        mock_data_dir = tmp_path / "mock_data"
        DatasetLoader.create_mock_fixtures(mock_data_dir)
        instances = DatasetLoader.load_tasks(mock_data_dir / "tasks.jsonl")
        if not instances:
            raise RuntimeError("Failed to generate mock SWE instances for dry-run.")

        instance = instances[0]
        base_files = {
            "requests/models.py": "def handle_redirect():\n    pass\n",
        }
        plan = [
            {
                "sub_agent": "explorer",
                "tool": "read_file",
                "arguments": {"filepath": "requests/models.py"},
            },
            {
                "sub_agent": "drafter",
                "tool": "edit_file",
                "arguments": {
                    "filepath": "requests/models.py",
                    "old_string": "    pass",
                    "new_string": "    # fixed\n    pass",
                },
            },
            {
                "sub_agent": "validator",
                "tool": "submit_patch",
                "arguments": {},
            },
        ]

        session, _ = runner.benchmark_on_instance(
            instance=instance,
            harness=harness,
            planned_steps=plan,
            base_files=base_files,
        )

        if not session.success:
            print(f"❌ Dry-run workflow failed: {session.error_message}")
            return False

        if not session.patch:
            print("❌ Dry-run produced an empty patch.")
            return False

        return True


def main() -> int:
    """CLI entrypoint for validating submission.zip."""
    parser = argparse.ArgumentParser(
        description="Validates Kaggle submission.zip for Gemma 4 Developer Agent."
    )
    parser.add_argument(
        "archive",
        type=str,
        help="Path to submission.zip file to validate.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute simulated agent evaluation on synthetic instance.",
    )

    args = parser.parse_args()
    archive_path = Path(args.archive)

    result = validate_submission(archive_path)

    print("==================================================")
    print(" KAGGLE SUBMISSION VALIDATION REPORT              ")
    print("==================================================")
    print(f"Archive: {result.archive_path}")
    print(f"Files  : {result.total_files}")
    print(f"Size   : {result.compressed_size_bytes:,} bytes (compressed)")
    print("Checks :")
    for check_name, check_ok in result.checks.items():
        symbol = "✔" if check_ok else "❌"
        print(f"  {symbol} {check_name}")

    if result.warnings:
        print("\nWarnings:")
        for w in result.warnings:
            print(f"  ⚠️ {w}")

    if result.errors:
        print("\nErrors:")
        for err in result.errors:
            print(f"  ❌ {err}")

    if not result.passed:
        print("\n❌ VALIDATION RESULT: FAILED")
        return 1

    print("\n✅ VALIDATION RESULT: PASSED (100% Compliant)")

    if args.dry_run:
        print("\n🚀 Running dry-run agent execution in sandbox...")
        try:
            ok = verify_submission_dry_run(archive_path)
            if ok:
                print("✅ Dry-run evaluation: PASSED (Valid patch generated)")
            else:
                print("❌ Dry-run evaluation: FAILED")
                return 1
        except Exception as exc:
            print(f"❌ Dry-run execution error: {exc}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
