"""Evaluation Metrics and Benchmark Reporting Engine.

Computes Pass@1 resolution rate, execution latency, and generates
structured JSON and Markdown diagnostic reports for SWE-bench evaluations.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class InstanceMetric:
    """Benchmark outcome for a single SWE-bench instance.

    Attributes:
        instance_id: Unique task identifier.
        resolved: Whether the patch resolved the issue (Pass@1).
        exit_code: Exit code of the verification test suite.
        duration_seconds: Evaluation time in seconds.
        tool_calls_count: Number of tool calls executed by agent.
        test_output: Captured stdout/stderr of verification tests.
        error_message: Optional error message if evaluation failed.
        patch_applied: Whether the agent patch applied cleanly.
    """

    instance_id: str
    resolved: bool
    exit_code: int
    duration_seconds: float
    tool_calls_count: int = 0
    test_output: str = ""
    error_message: Optional[str] = None
    patch_applied: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes metric to dictionary."""
        return asdict(self)


@dataclass
class BenchmarkSummary:
    """Aggregated benchmark statistics across multiple evaluation instances.

    Attributes:
        total_instances: Total number of evaluated tasks.
        resolved_count: Number of successfully resolved tasks.
        failed_count: Number of failed tasks.
        pass_at_1: Pass@1 resolution rate in range [0.0, 1.0].
        avg_duration_seconds: Average evaluation time per instance.
        results: Detailed instance evaluation metrics.
    """

    total_instances: int = 0
    resolved_count: int = 0
    failed_count: int = 0
    pass_at_1: float = 0.0
    avg_duration_seconds: float = 0.0
    results: List[InstanceMetric] = field(default_factory=list)

    @classmethod
    def from_results(cls, results: List[InstanceMetric]) -> BenchmarkSummary:
        """Constructs benchmark summary from a list of instance results.

        Args:
            results: List of InstanceMetric results.

        Returns:
            Computed BenchmarkSummary object.
        """
        total = len(results)
        if total == 0:
            return cls()

        resolved = sum(1 for r in results if r.resolved)
        failed = total - resolved
        pass_at_1 = resolved / total
        avg_dur = sum(r.duration_seconds for r in results) / total

        return cls(
            total_instances=total,
            resolved_count=resolved,
            failed_count=failed,
            pass_at_1=round(pass_at_1, 4),
            avg_duration_seconds=round(avg_dur, 2),
            results=results,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes summary to JSON-serializable dictionary."""
        return {
            "total_instances": self.total_instances,
            "resolved_count": self.resolved_count,
            "failed_count": self.failed_count,
            "pass_at_1": self.pass_at_1,
            "avg_duration_seconds": self.avg_duration_seconds,
            "results": [r.to_dict() for r in self.results],
        }

    def to_markdown(self) -> str:
        """Generates clean Markdown table diagnostic report."""
        status_icon = "🏆" if self.pass_at_1 >= 0.25 else "📊"
        lines = [
            f"# {status_icon} SWE-bench Evaluation Benchmark Summary",
            "",
            f"- **Total Instances**: `{self.total_instances}`",
            f"- **Resolved (Pass@1)**: `{self.resolved_count}` ({self.pass_at_1 * 100:.1f}%)",
            f"- **Failed**: `{self.failed_count}`",
            f"- **Avg Latency**: `{self.avg_duration_seconds}s`",
            "",
            "| Instance ID | Status | Applied? | Exit Code | Time (s) | Error |",
            "| :--- | :---: | :---: | :---: | :---: | :--- |",
        ]

        for r in self.results:
            st = "✅ PASS" if r.resolved else "❌ FAIL"
            app = "✔" if r.patch_applied else "✘"
            err = r.error_message or "-"
            if len(err) > 40:
                err = err[:37] + "..."
            lines.append(
                f"| `{r.instance_id}` | {st} | {app} | `{r.exit_code}` | "
                f"`{r.duration_seconds:.2f}` | {err} |"
            )

        return "\n".join(lines) + "\n"

    def save_reports(self, output_dir: Path, stem: str = "benchmark_report") -> None:
        """Saves JSON and Markdown reports to specified directory.

        Args:
            output_dir: Directory where reports should be written.
            stem: Base filename stem (e.g. 'benchmark_report').
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        json_file = output_dir / f"{stem}.json"
        md_file = output_dir / f"{stem}.md"

        json_file.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        md_file.write_text(self.to_markdown(), encoding="utf-8")
