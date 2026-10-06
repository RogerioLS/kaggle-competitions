"""Unit Tests for Local SWE-bench Evaluation Harness, Sandbox, and Metrics."""

import tempfile
from pathlib import Path

from competitions.gemma_developer_agent.evaluation.dataset_loader import SWEInstance
from competitions.gemma_developer_agent.evaluation.harness import LocalSWEHarness
from competitions.gemma_developer_agent.evaluation.metrics import (
    BenchmarkSummary,
    InstanceMetric,
)
from competitions.gemma_developer_agent.evaluation.sandbox import (
    SubprocessSandbox,
)


class TestSubprocessSandbox:
    """Tests for SubprocessSandbox execution and file/patch isolation."""

    def test_sandbox_execute_command(self) -> None:
        with SubprocessSandbox() as sb:
            res = sb.execute(["echo", "hello world"])
            assert res.is_success
            assert res.exit_code == 0
            assert "hello world" in res.stdout
            assert res.duration_seconds >= 0.0

    def test_sandbox_write_and_read_file(self) -> None:
        with SubprocessSandbox() as sb:
            sb.write_file("src/foo.py", "x = 42\n")
            content = sb.read_file("src/foo.py")
            assert content == "x = 42\n"

    def test_sandbox_apply_patch_and_diff(self) -> None:
        with SubprocessSandbox() as sb:
            sb.write_file("hello.txt", "line1\nline2\n")
            sb.commit_all("initial")

            patch = (
                "diff --git a/hello.txt b/hello.txt\n"
                "--- a/hello.txt\n"
                "+++ b/hello.txt\n"
                "@@ -1,2 +1,3 @@\n"
                " line1\n"
                "+added_line\n"
                " line2\n"
            )
            applied = sb.apply_patch(patch)
            assert applied is True
            content = sb.read_file("hello.txt")
            assert "added_line" in content

    def test_sandbox_apply_invalid_patch(self) -> None:
        with SubprocessSandbox() as sb:
            applied = sb.apply_patch("not a valid unified diff")
            assert applied is False


class TestEvaluationMetrics:
    """Tests for InstanceMetric and BenchmarkSummary."""

    def test_instance_metric_dict(self) -> None:
        metric = InstanceMetric(
            instance_id="task-1",
            resolved=True,
            exit_code=0,
            duration_seconds=1.23,
        )
        data = metric.to_dict()
        assert data["instance_id"] == "task-1"
        assert data["resolved"] is True
        assert data["exit_code"] == 0

    def test_benchmark_summary_computation(self) -> None:
        m1 = InstanceMetric("t1", resolved=True, exit_code=0, duration_seconds=1.0)
        m2 = InstanceMetric("t2", resolved=False, exit_code=1, duration_seconds=2.0)
        summary = BenchmarkSummary.from_results([m1, m2])

        assert summary.total_instances == 2
        assert summary.resolved_count == 1
        assert summary.failed_count == 1
        assert summary.pass_at_1 == 0.5
        assert summary.avg_duration_seconds == 1.5

        md = summary.to_markdown()
        assert "SWE-bench Evaluation Benchmark Summary" in md
        assert "t1" in md
        assert "t2" in md

    def test_save_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            summary = BenchmarkSummary.from_results([])
            summary.save_reports(out_path, stem="test_rep")
            assert (out_path / "test_rep.json").exists()
            assert (out_path / "test_rep.md").exists()


class TestLocalSWEHarness:
    """Tests for LocalSWEHarness evaluation lifecycle."""

    def test_evaluate_instance_success(self) -> None:
        harness = LocalSWEHarness()

        # Baseline: buggy code where add(a, b) returns a - b
        base_files = {
            "calc.py": "def add(a: int, b: int) -> int:\n    return a - b\n",
            "test_calc.py": (
                "from calc import add\n\n" "def test_add():\n" "    assert add(2, 3) == 5\n"
            ),
        }

        # Gold patch that fixes add(a, b) to return a + b
        fix_patch = (
            "diff --git a/calc.py b/calc.py\n"
            "--- a/calc.py\n"
            "+++ b/calc.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def add(a: int, b: int) -> int:\n"
            "-    return a - b\n"
            "+    return a + b\n"
        )

        instance = SWEInstance(
            instance_id="calc__bug-1",
            repo="dummy/calc",
            base_commit="abc001",
            problem_statement="add function returns subtraction instead of addition",
            patch=fix_patch,
        )

        # 1. With the fix patch, test passes
        metric = harness.evaluate_instance(
            instance=instance,
            agent_patch=fix_patch,
            base_files=base_files,
            test_cmd=["python3", "-m", "pytest", "-q", "test_calc.py"],
        )
        assert metric.resolved is True
        assert metric.exit_code == 0
        assert metric.patch_applied is True

    def test_evaluate_instance_empty_patch(self) -> None:
        harness = LocalSWEHarness()
        instance = SWEInstance(
            instance_id="calc__bug-2",
            repo="dummy/calc",
            base_commit="abc002",
            problem_statement="fix needed",
        )
        metric = harness.evaluate_instance(
            instance=instance,
            agent_patch="",
        )
        assert metric.resolved is False
        assert metric.patch_applied is False
        assert "Empty or missing" in (metric.error_message or "")

    def test_evaluate_instance_failing_patch(self) -> None:
        harness = LocalSWEHarness()
        base_files = {
            "calc.py": "def add(a: int, b: int) -> int:\n    return a - b\n",
            "test_calc.py": (
                "from calc import add\n\n" "def test_add():\n" "    assert add(2, 3) == 5\n"
            ),
        }

        # Bad patch that leaves it wrong
        bad_patch = (
            "diff --git a/calc.py b/calc.py\n"
            "--- a/calc.py\n"
            "+++ b/calc.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def add(a: int, b: int) -> int:\n"
            "-    return a - b\n"
            "+    return a * b\n"
        )

        instance = SWEInstance(
            instance_id="calc__bug-3",
            repo="dummy/calc",
            base_commit="abc003",
            problem_statement="bug in calc",
        )

        metric = harness.evaluate_instance(
            instance=instance,
            agent_patch=bad_patch,
            base_files=base_files,
            test_cmd=["python3", "-m", "pytest", "-q", "test_calc.py"],
        )
        assert metric.resolved is False
        assert metric.exit_code != 0
        assert metric.patch_applied is True

    def test_evaluate_benchmark_aggregation(self) -> None:
        harness = LocalSWEHarness()
        instance = SWEInstance(
            instance_id="task-agg",
            repo="dummy/agg",
            base_commit="abc004",
            problem_statement="dummy",
        )
        summary = harness.evaluate_benchmark(
            instances=[instance],
            agent_patches={"task-agg": ""},
        )
        assert summary.total_instances == 1
        assert summary.resolved_count == 0
        assert summary.pass_at_1 == 0.0
