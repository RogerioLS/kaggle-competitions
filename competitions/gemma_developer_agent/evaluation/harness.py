"""Local SWE-bench Evaluation Harness & Benchmark Engine.

Orchestrates two-phase execution and verification lifecycles for SWE-bench instances,
applying candidate agent patches and hermetic test patches inside ephemeral sandboxes
to compute Pass@1 resolution scores and detailed execution diagnostics.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from competitions.gemma_developer_agent.evaluation.dataset_loader import SWEInstance
from competitions.gemma_developer_agent.evaluation.metrics import (
    BenchmarkSummary,
    InstanceMetric,
)
from competitions.gemma_developer_agent.evaluation.sandbox import (
    SubprocessSandbox,
)


class LocalSWEHarness:
    """Local evaluation harness for SWE-bench benchmark tasks.

    Executes candidate agent patches against repository snapshots and verifies
    them against task test patches using hermetic test suites.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        default_timeout: int = 120,
    ) -> None:
        """Initializes the evaluation harness.

        Args:
            base_dir: Optional root directory for storing persistent benchmark artifacts.
            default_timeout: Maximum timeout in seconds for test executions.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / "artifacts" / "benchmarks"
        self.default_timeout = default_timeout
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_instance(
        self,
        instance: SWEInstance,
        agent_patch: str,
        base_files: Optional[Dict[str, str]] = None,
        test_cmd: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> InstanceMetric:
        """Evaluates a single SWEInstance with candidate agent patch.

        Lifecycle:
        1. Spawn ephemeral verification sandbox.
        2. Populate baseline files & commit baseline.
        3. Apply candidate agent patch.
        4. Apply instance test patch.
        5. Run verification test suite.
        6. Return computed InstanceMetric.

        Args:
            instance: Target SWEInstance task definition.
            agent_patch: Unified diff patch produced by the agent.
            base_files: Optional dict mapping relative file paths to content strings.
            test_cmd: Optional custom test execution command (default: ['pytest', '-q']).
            timeout: Optional per-test execution timeout override.

        Returns:
            InstanceMetric containing resolution status, exit code, and test outputs.
        """
        exec_timeout = timeout or self.default_timeout
        start_time = time.perf_counter()

        with SubprocessSandbox() as sandbox:
            # Step 1: Write baseline files if provided
            if base_files:
                for rel_path, content in base_files.items():
                    sandbox.write_file(rel_path, content)
                sandbox.commit_all("baseline")

            # Step 2: Validate candidate patch
            if not agent_patch or not agent_patch.strip():
                duration = time.perf_counter() - start_time
                return InstanceMetric(
                    instance_id=instance.instance_id,
                    resolved=False,
                    exit_code=1,
                    duration_seconds=round(duration, 3),
                    test_output="",
                    error_message="Empty or missing agent patch.",
                    patch_applied=False,
                )

            # Step 3: Apply agent patch
            applied = sandbox.apply_patch(agent_patch)
            if not applied:
                duration = time.perf_counter() - start_time
                return InstanceMetric(
                    instance_id=instance.instance_id,
                    resolved=False,
                    exit_code=1,
                    duration_seconds=round(duration, 3),
                    test_output="",
                    error_message="Agent patch failed to apply cleanly.",
                    patch_applied=False,
                )

            # Step 4: Apply task test patch if present
            if instance.test_patch and instance.test_patch.strip():
                test_applied = sandbox.apply_patch(instance.test_patch)
                if not test_applied:
                    duration = time.perf_counter() - start_time
                    return InstanceMetric(
                        instance_id=instance.instance_id,
                        resolved=False,
                        exit_code=1,
                        duration_seconds=round(duration, 3),
                        test_output="",
                        error_message="Verification test patch failed to apply.",
                        patch_applied=True,
                    )

            # Step 5: Execute verification test command
            cmd = test_cmd or ["pytest", "-q"]
            test_res = sandbox.execute(cmd, timeout=exec_timeout)

            duration = time.perf_counter() - start_time
            is_resolved = test_res.is_success

            output_log = f"{test_res.stdout}\n{test_res.stderr}".strip()

            err_msg = None if is_resolved else f"Tests failed with code {test_res.exit_code}"
            return InstanceMetric(
                instance_id=instance.instance_id,
                resolved=is_resolved,
                exit_code=test_res.exit_code,
                duration_seconds=round(duration, 3),
                test_output=output_log,
                error_message=err_msg,
                patch_applied=True,
            )

    def evaluate_benchmark(
        self,
        instances: List[SWEInstance],
        agent_patches: Dict[str, str],
        base_files_map: Optional[Dict[str, Dict[str, str]]] = None,
        test_cmd: Optional[List[str]] = None,
    ) -> BenchmarkSummary:
        """Evaluates multiple SWE-bench instances and aggregates results.

        Args:
            instances: List of SWEInstance tasks.
            agent_patches: Dict mapping instance_id to candidate patch string.
            base_files_map: Optional mapping of instance_id to base files dict.
            test_cmd: Optional custom test execution command.

        Returns:
            BenchmarkSummary containing aggregated Pass@1 rate and diagnostics.
        """
        results: List[InstanceMetric] = []
        base_map = base_files_map or {}

        for inst in instances:
            patch = agent_patches.get(inst.instance_id, "")
            base_files = base_map.get(inst.instance_id)
            metric = self.evaluate_instance(
                instance=inst,
                agent_patch=patch,
                base_files=base_files,
                test_cmd=test_cmd,
            )
            results.append(metric)

        return BenchmarkSummary.from_results(results)
