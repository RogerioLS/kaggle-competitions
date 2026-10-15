"""Unit tests for telemetry recording and RichTelemetryVisualizer."""

from __future__ import annotations

import pytest

from competitions.gemma_developer_agent.agent.runner import (
    AgentSessionResult,
    ToolCall,
    TurnRecord,
)
from competitions.gemma_developer_agent.evaluation.metrics import (
    BenchmarkSummary,
    InstanceMetric,
)
from competitions.gemma_developer_agent.telemetry import (
    RichTelemetryVisualizer,
    TurnTelemetry,
)


@pytest.fixture
def sample_turn_telemetry() -> TurnTelemetry:
    """Fixture providing a standard TurnTelemetry instance."""
    return TurnTelemetry(
        turn_index=1,
        sub_agent="explorer",
        tool_name="read_file",
        thought="I should inspect the repository structure first.",
        arguments={"filepath": "requests/models.py", "start_line": 1, "end_line": 50},
        observation="class Response(object):\n    def __init__(self):\n        pass",
        duration_seconds=0.45,
        is_error=False,
    )


@pytest.fixture
def error_turn_telemetry() -> TurnTelemetry:
    """Fixture providing an error TurnTelemetry instance."""
    return TurnTelemetry(
        turn_index=2,
        sub_agent="editor",
        tool_name="edit_file",
        thought="Attempting to replace invalid target text.",
        arguments={"filepath": "main.py", "old_str": "target", "new_str": "replacement"},
        observation="FileNotFoundError: main.py does not exist.",
        duration_seconds=0.12,
        is_error=True,
    )


@pytest.fixture
def sample_session_result() -> AgentSessionResult:
    """Fixture providing a sample AgentSessionResult."""
    history = [
        TurnRecord(
            turn_index=1,
            sub_agent="explorer",
            tool_call=ToolCall(tool_name="read_file", arguments={"filepath": "foo.py"}),
            observation="print('hello')",
        ),
        TurnRecord(
            turn_index=2,
            sub_agent="validator",
            tool_call=ToolCall(tool_name="submit_patch", arguments={}),
            observation="patch generated",
        ),
    ]
    return AgentSessionResult(
        instance_id="psf__requests-101",
        patch=(
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1 +1 @@\n"
            "-hello\n"
            "+world\n"
        ),
        turns_used=2,
        duration_seconds=3.42,
        success=True,
        sub_agent_trace=["explorer", "validator"],
        history=history,
    )


@pytest.fixture
def sample_benchmark_summary() -> BenchmarkSummary:
    """Fixture providing an aggregated BenchmarkSummary."""
    metrics = [
        InstanceMetric(
            instance_id="task-001",
            resolved=True,
            exit_code=0,
            duration_seconds=12.5,
            tool_calls_count=4,
            test_output="=== test session starts ===\ntest_one PASSED\n",
        ),
        InstanceMetric(
            instance_id="task-002",
            resolved=False,
            exit_code=1,
            duration_seconds=8.2,
            tool_calls_count=2,
            test_output="test_two FAILED\n",
            error_message="AssertionError: 1 != 2",
        ),
    ]
    return BenchmarkSummary.from_results(metrics)


class TestTurnTelemetry:
    """Test suite for TurnTelemetry data model."""

    def test_turn_telemetry_fields(self, sample_turn_telemetry: TurnTelemetry) -> None:
        """Verifies TurnTelemetry attributes and serialization."""
        assert sample_turn_telemetry.turn_index == 1
        assert sample_turn_telemetry.sub_agent == "explorer"
        assert sample_turn_telemetry.tool_name == "read_file"
        assert "inspect" in sample_turn_telemetry.thought
        assert sample_turn_telemetry.arguments["filepath"] == "requests/models.py"
        assert sample_turn_telemetry.duration_seconds == 0.45
        assert not sample_turn_telemetry.is_error

        data = sample_turn_telemetry.to_dict()
        assert isinstance(data, dict)
        assert data["turn_index"] == 1
        assert data["tool_name"] == "read_file"
        assert data["is_error"] is False

    def test_turn_telemetry_error_default(self) -> None:
        """Verifies is_error defaults to False."""
        record = TurnTelemetry(
            turn_index=3,
            sub_agent="drafter",
            tool_name="write_file",
            thought="Drafting code",
            arguments={"path": "a.py"},
            observation="saved",
            duration_seconds=1.0,
        )
        assert record.is_error is False


class TestRichTelemetryVisualizer:
    """Test suite for RichTelemetryVisualizer formatting and rendering."""

    def test_render_turn_html_success(self, sample_turn_telemetry: TurnTelemetry) -> None:
        """Verifies render_turn_html produces styled HTML with accordion and badges."""
        html_out = RichTelemetryVisualizer.render_turn_html(sample_turn_telemetry)
        assert "<style>" in html_out
        assert "Turn #1" in html_out
        assert "explorer" in html_out
        assert "read_file" in html_out
        assert "0.45s" in html_out
        assert "gemma-badge-ok" in html_out
        assert "<details" in html_out
        assert "requests/models.py" in html_out
        assert "class Response" in html_out

    def test_render_turn_html_error(self, error_turn_telemetry: TurnTelemetry) -> None:
        """Verifies render_turn_html applies error styling and badge for failed turns."""
        html_out = RichTelemetryVisualizer.render_turn_html(error_turn_telemetry)
        assert "gemma-badge-error" in html_out
        assert "FileNotFoundError" in html_out
        assert "error" in html_out

    def test_render_turn_html_with_diff_observation(self) -> None:
        """Verifies observation containing git diff is rendered with diff highlighting."""
        telemetry = TurnTelemetry(
            turn_index=1,
            sub_agent="validator",
            tool_name="git_diff",
            thought="Reviewing patch",
            arguments={},
            observation="diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n+new_code\n",
            duration_seconds=0.2,
        )
        html_out = RichTelemetryVisualizer.render_turn_html(telemetry)
        assert "gemma-diff-viewer" in html_out
        assert "gemma-diff-add" in html_out

    def test_render_turn_html_with_pytest_observation(self) -> None:
        """Verifies observation containing pytest results highlights PASSED/FAILED."""
        telemetry = TurnTelemetry(
            turn_index=2,
            sub_agent="validator",
            tool_name="run_command",
            thought="Running test suite",
            arguments={"command": "pytest"},
            observation="=== test session starts ===\ntest_mod.py::test_pass PASSED\n",
            duration_seconds=1.1,
        )
        html_out = RichTelemetryVisualizer.render_turn_html(telemetry)
        assert "PASSED" in html_out
        assert "#4ade80" in html_out  # Green color highlight

    def test_render_turn_terminal(
        self,
        sample_turn_telemetry: TurnTelemetry,
        error_turn_telemetry: TurnTelemetry,
    ) -> None:
        """Verifies render_turn_terminal returns ANSI-colored formatted string."""
        term_out = RichTelemetryVisualizer.render_turn_terminal(sample_turn_telemetry)
        assert "\033[" in term_out
        assert "Turn #1" in term_out
        assert "explorer" in term_out
        assert "read_file" in term_out
        assert "[OK]" in term_out

        err_out = RichTelemetryVisualizer.render_turn_terminal(error_turn_telemetry)
        assert "[ERROR]" in err_out
        assert "FileNotFoundError" in err_out

    def test_render_diff_html_valid_and_empty(self) -> None:
        """Verifies diff viewer renders additions, deletions, and empty placeholder."""
        raw_diff = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -10,3 +10,3 @@\n"
            "-old_line\n"
            "+new_line\n"
        )
        diff_html = RichTelemetryVisualizer.render_diff_html(raw_diff)
        assert "gemma-diff-viewer" in diff_html
        assert "gemma-diff-add" in diff_html
        assert "new_line" in diff_html
        assert "gemma-diff-del" in diff_html
        assert "old_line" in diff_html
        assert "gemma-diff-hunk" in diff_html

        empty_html = RichTelemetryVisualizer.render_diff_html("")
        assert "No git diff changes" in empty_html

    def test_render_session_summary_html(
        self,
        sample_session_result: AgentSessionResult,
    ) -> None:
        """Verifies session summary card renders status, turns, trace, and patch diff."""
        metric = InstanceMetric(
            instance_id="psf__requests-101",
            resolved=True,
            exit_code=0,
            duration_seconds=3.42,
            tool_calls_count=2,
            test_output="test_connection PASSED\n",
        )
        html_out = RichTelemetryVisualizer.render_session_summary_html(
            sample_session_result,
            metric=metric,
        )
        assert "psf__requests-101" in html_out
        assert "RESOLVED" in html_out
        assert "Turns Used" in html_out
        assert "explorer" in html_out
        assert "validator" in html_out
        assert "gemma-diff-viewer" in html_out
        assert "test_connection PASSED" in html_out

    def test_render_session_summary_html_failure(self) -> None:
        """Verifies session summary card renders failure status and error alert."""
        session = AgentSessionResult(
            instance_id="fail__repo-001",
            patch="",
            turns_used=5,
            duration_seconds=10.0,
            success=False,
            timed_out=True,
            budget_exhausted=False,
            error_message="Agent execution exceeded turn budget.",
        )
        html_out = RichTelemetryVisualizer.render_session_summary_html(session)
        assert "fail__repo-001" in html_out
        assert "FAILED" in html_out
        assert "TIMED OUT" in html_out
        assert "exceeded turn budget" in html_out

    def test_render_benchmark_report_html(
        self,
        sample_benchmark_summary: BenchmarkSummary,
    ) -> None:
        """Verifies benchmark report renders Pass@1 progress bar and searchable table."""
        report = RichTelemetryVisualizer.render_benchmark_report_html(sample_benchmark_summary)
        assert "SWE-bench Evaluation Benchmark Report" in report
        assert "Pass@1 Resolution Rate" in report
        assert "50.0%" in report
        assert "gemma-progress-fill" in report
        assert "task-001" in report
        assert "task-002" in report
        assert "RESOLVED" in report
        assert "FAILED" in report
        assert "gemmaFilterRows" in report
        assert "gemmaSearchRows" in report
