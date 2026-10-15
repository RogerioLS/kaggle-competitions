"""Telemetry recording and rich visualizer for Gemma Developer Agent.

Provides TurnTelemetry for structured trace collection and RichTelemetryVisualizer
for rendering styled HTML cards, diff viewers, ANSI terminal output, and benchmark tables.
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from competitions.gemma_developer_agent.agent.runner import (
    AgentSessionResult,
)
from competitions.gemma_developer_agent.evaluation.metrics import (
    BenchmarkSummary,
    InstanceMetric,
)

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_BLUE = "\033[94m"
ANSI_MAGENTA = "\033[95m"
ANSI_CYAN = "\033[96m"


CSS_BASE = """
.gemma-telemetry-container {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
  color: #f1f5f9;
  background-color: #0f172a;
  border-radius: 10px;
  padding: 16px;
  margin: 12px 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}
.gemma-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
}
.gemma-card.error {
  border-color: #ef4444;
}
.gemma-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.gemma-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 6px;
}
.gemma-badge-turn {
  background-color: rgba(148, 163, 184, 0.2);
  color: #94a3b8;
  border: 1px solid #475569;
}
.gemma-badge-subagent {
  background-color: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  border: 1px solid #38bdf8;
}
.gemma-badge-tool {
  background-color: rgba(192, 132, 252, 0.2);
  color: #c084fc;
  border: 1px solid #c084fc;
}
.gemma-badge-resolved, .gemma-badge-ok {
  background-color: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  border: 1px solid #4ade80;
}
.gemma-badge-failed, .gemma-badge-error {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid #f87171;
}
.gemma-chip-duration {
  font-size: 12px;
  font-weight: 600;
  color: #facc15;
  background: #334155;
  padding: 3px 8px;
  border-radius: 6px;
}
.gemma-accordion {
  margin-top: 10px;
  border: 1px solid #334155;
  border-radius: 6px;
  background: #0f172a;
}
.gemma-accordion summary {
  padding: 8px 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  user-select: none;
}
.gemma-accordion-body {
  padding: 10px 12px;
  border-top: 1px solid #334155;
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.5;
}
.gemma-section-title {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin: 10px 0 4px 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.gemma-code-block {
  background: #090d16;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 10px;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  color: #e2e8f0;
  margin: 4px 0 0 0;
  line-height: 1.45;
}
.gemma-diff-viewer {
  background: #090d16;
  border: 1px solid #334155;
  border-radius: 6px;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.45;
  padding: 8px 0;
}
.gemma-diff-line {
  display: block;
  padding: 1px 12px;
  white-space: pre;
}
.gemma-diff-file { color: #94a3b8; font-weight: 600; }
.gemma-diff-meta { color: #64748b; font-style: italic; }
.gemma-diff-hunk {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  font-weight: 600;
}
.gemma-diff-add {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}
.gemma-diff-del {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}
.gemma-diff-context { color: #cbd5e1; }
.gemma-diff-empty {
  padding: 16px;
  text-align: center;
  color: #64748b;
  font-style: italic;
}
.gemma-alert {
  padding: 10px 14px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
}
.gemma-alert-error {
  background-color: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #fca5a5;
}
.gemma-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}
.gemma-meta-item {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 8px 12px;
}
.gemma-meta-label {
  font-size: 11px;
  color: #94a3b8;
  text-transform: uppercase;
}
.gemma-meta-value {
  font-size: 16px;
  font-weight: 700;
  color: #f8fafc;
  margin-top: 2px;
}
.gemma-trace-pill {
  display: inline-block;
  background: #334155;
  color: #38bdf8;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.gemma-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.gemma-kpi-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px 16px;
}
.gemma-kpi-label {
  font-size: 11px;
  color: #94a3b8;
  text-transform: uppercase;
  font-weight: 600;
}
.gemma-kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: #f8fafc;
  margin: 4px 0;
}
.gemma-progress-track {
  width: 100%;
  height: 8px;
  background: #334155;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 6px;
}
.gemma-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #22c55e);
  border-radius: 4px;
  transition: width 0.3s ease;
}
.gemma-table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}
.gemma-search-input {
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 6px;
  color: #f1f5f9;
  padding: 6px 12px;
  font-size: 12px;
  outline: none;
  min-width: 220px;
}
.gemma-search-input:focus {
  border-color: #38bdf8;
}
.gemma-filter-btn {
  background: #334155;
  border: 1px solid #475569;
  color: #cbd5e1;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}
.gemma-filter-btn.active, .gemma-filter-btn:hover {
  background: #38bdf8;
  color: #0f172a;
  font-weight: 600;
}
.gemma-report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}
.gemma-report-table th {
  background: #1e293b;
  color: #94a3b8;
  padding: 8px 10px;
  border-bottom: 1px solid #475569;
  font-weight: 600;
}
.gemma-report-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #334155;
}
.gemma-report-table tbody tr:hover {
  background: rgba(51, 65, 85, 0.4);
}
""".strip()


@dataclass
class TurnTelemetry:
    """Telemetry data captured during a single ReAct conversational turn.

    Attributes:
        turn_index: 1-based sequential index of the turn.
        sub_agent: Identifier of the active specialized subagent.
        tool_name: Name of the invoked tool function.
        thought: Internal chain-of-thought reasoning before action.
        arguments: Keyword arguments passed to the tool invocation.
        observation: Output/result returned from the environment or tool.
        duration_seconds: Execution wall-clock latency of the turn.
        is_error: Whether the turn encountered a tool execution or parsing error.
    """

    turn_index: int
    sub_agent: str
    tool_name: str
    thought: str
    arguments: Dict[str, Any]
    observation: str
    duration_seconds: float
    is_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes telemetry record to a dictionary."""
        return asdict(self)


class RichTelemetryVisualizer:
    """Visualizer for agent telemetry, execution diffs, and benchmark reports."""

    def __init__(self, theme: str = "dark") -> None:
        """Initializes the visualizer.

        Args:
            theme: Color theme mode ('dark' or 'light').
        """
        self.theme = theme

    @staticmethod
    def _wrap_with_style(content_html: str) -> str:
        """Wraps HTML content with scoped style definitions."""
        return f"<style>{CSS_BASE}</style>\n{content_html}"

    @classmethod
    def render_diff_html(cls, git_diff: str) -> str:
        """Renders a unified git diff with green additions and red deletions.

        Args:
            git_diff: Raw unified diff string.

        Returns:
            Styled HTML representation with colored lines.
        """
        if not git_diff or not git_diff.strip():
            empty_html = '<div class="gemma-diff-empty">' "No git diff changes recorded." "</div>"
            return cls._wrap_with_style(empty_html)

        rendered_lines: List[str] = []
        for line in git_diff.splitlines():
            escaped = html.escape(line)
            if line.startswith("+++") or line.startswith("---"):
                line_cls = "gemma-diff-file"
            elif line.startswith("+"):
                line_cls = "gemma-diff-add"
            elif line.startswith("-"):
                line_cls = "gemma-diff-del"
            elif line.startswith("@@"):
                line_cls = "gemma-diff-hunk"
            elif line.startswith(("diff --git", "index ", "new file", "deleted file")):
                line_cls = "gemma-diff-meta"
            else:
                line_cls = "gemma-diff-context"

            rendered_lines.append(f'<span class="gemma-diff-line {line_cls}">{escaped}</span>')

        diff_body = "\n".join(rendered_lines)
        diff_html = (
            f'<div class="gemma-diff-viewer">'
            f'<pre style="margin:0;"><code>{diff_body}</code></pre>'
            f"</div>"
        )
        return cls._wrap_with_style(diff_html)

    @classmethod
    def _render_pytest_output_html(cls, output: str) -> str:
        """Highlights pytest outputs with colorized test status lines."""
        lines: List[str] = []
        for line in output.splitlines():
            escaped = html.escape(line)
            if "PASSED" in line:
                lines.append(f'<span style="color: #4ade80; font-weight: 600;">{escaped}</span>')
            elif "FAILED" in line or "ERROR" in line:
                lines.append(f'<span style="color: #f87171; font-weight: 600;">{escaped}</span>')
            elif line.startswith("="):
                lines.append(f'<span style="color: #38bdf8; font-weight: 600;">{escaped}</span>')
            else:
                lines.append(f"<span>{escaped}</span>")

        body = "\n".join(lines)
        return f'<pre class="gemma-code-block"><code>{body}</code></pre>'

    @classmethod
    def _format_observation_html(cls, observation: str) -> str:
        """Formats observation with syntax-highlighted diff or test output."""
        if not observation:
            return '<pre class="gemma-code-block"><code>(empty observation)</code></pre>'
        if "diff --git" in observation or ("--- " in observation and "+++ " in observation):
            return cls.render_diff_html(observation)
        if "=== test session starts ===" in observation or (
            "PASSED" in observation or "FAILED" in observation
        ):
            return cls._render_pytest_output_html(observation)

        return f'<pre class="gemma-code-block"><code>' f"{html.escape(observation)}</code></pre>"

    @classmethod
    def render_turn_html(cls, telemetry: TurnTelemetry) -> str:
        """Generates a styled HTML card for a single turn.

        Includes collapsible accordion for thought reasoning, tool call badges,
        duration chip, and formatted arguments and observation blocks.

        Args:
            telemetry: TurnTelemetry instance.

        Returns:
            Rendered self-contained HTML component string.
        """
        error_class = " error" if telemetry.is_error else ""
        status_badge = (
            '<span class="gemma-badge gemma-badge-error">ERROR</span>'
            if telemetry.is_error
            else '<span class="gemma-badge gemma-badge-ok">OK</span>'
        )

        args_json = json.dumps(telemetry.arguments, indent=2, default=str)
        obs_html = cls._format_observation_html(telemetry.observation)

        turn_html = f"""
<div class="gemma-telemetry-container">
  <div class="gemma-card{error_class}">
    <div class="gemma-header">
      <div>
        <span class="gemma-badge gemma-badge-turn">Turn #{telemetry.turn_index}</span>
        <span class="gemma-badge gemma-badge-subagent">{html.escape(telemetry.sub_agent)}</span>
        <span class="gemma-badge gemma-badge-tool">{html.escape(telemetry.tool_name)}</span>
        {status_badge}
      </div>
      <span class="gemma-chip-duration">⏱ {telemetry.duration_seconds:.2f}s</span>
    </div>

    <details class="gemma-accordion" open>
      <summary>💭 Thought Reasoning</summary>
      <div class="gemma-accordion-body">
        {html.escape(telemetry.thought) if telemetry.thought else '<em>(no thought provided)</em>'}
      </div>
    </details>

    <div class="gemma-section-title">🔧 Tool Arguments</div>
    <pre class="gemma-code-block"><code>{html.escape(args_json)}</code></pre>

    <div class="gemma-section-title">👁 Observation</div>
    {obs_html}
  </div>
</div>
""".strip()
        return cls._wrap_with_style(turn_html)

    @staticmethod
    def render_turn_terminal(telemetry: TurnTelemetry) -> str:
        """Generates an ANSI-colored formatted summary for CLI/terminal.

        Args:
            telemetry: TurnTelemetry execution instance.

        Returns:
            ANSI formatted string suitable for terminal display.
        """
        status_label = (
            f"{ANSI_RED}{ANSI_BOLD}[ERROR]{ANSI_RESET}"
            if telemetry.is_error
            else f"{ANSI_GREEN}{ANSI_BOLD}[OK]{ANSI_RESET}"
        )

        border = f"{ANSI_CYAN}" + ("─" * 50) + ANSI_RESET
        lines = [
            border,
            (
                f"{ANSI_BOLD}{ANSI_CYAN}Turn #{telemetry.turn_index}{ANSI_RESET} │ "
                f"{ANSI_MAGENTA}SubAgent:{ANSI_RESET} {telemetry.sub_agent} │ "
                f"{ANSI_BLUE}Tool:{ANSI_RESET} {telemetry.tool_name} │ "
                f"{ANSI_YELLOW}{telemetry.duration_seconds:.2f}s{ANSI_RESET} │ "
                f"{status_label}"
            ),
            f"{ANSI_DIM}Thought:{ANSI_RESET}",
            f"  {telemetry.thought.strip() if telemetry.thought else '(no thought)'}",
            f"{ANSI_BLUE}Arguments:{ANSI_RESET}",
        ]

        args_str = json.dumps(telemetry.arguments, indent=2, default=str)
        for arg_line in args_str.splitlines():
            lines.append(f"  {arg_line}")

        obs_color = ANSI_RED if telemetry.is_error else ANSI_GREEN
        lines.append(f"{obs_color}Observation:{ANSI_RESET}")
        obs_lines = telemetry.observation.splitlines() or ["(empty)"]
        for obs_line in obs_lines:
            lines.append(f"  {obs_line}")

        lines.append(border)
        return "\n".join(lines)

    @classmethod
    def render_session_summary_html(
        cls,
        session: AgentSessionResult,
        metric: Optional[InstanceMetric] = None,
    ) -> str:
        """Generates a full session card with status, patch diff, turns, and duration.

        Args:
            session: AgentSessionResult execution record.
            metric: Optional InstanceMetric evaluation result.

        Returns:
            Styled HTML session card.
        """
        is_resolved = metric.resolved if metric is not None else session.success
        status_badge = (
            '<span class="gemma-badge gemma-badge-resolved">RESOLVED</span>'
            if is_resolved
            else '<span class="gemma-badge gemma-badge-failed">FAILED</span>'
        )

        duration = (
            session.duration_seconds
            if session.duration_seconds > 0
            else (metric.duration_seconds if metric else 0.0)
        )
        turns = session.turns_used if session.turns_used > 0 else len(session.history)

        trace = session.sub_agent_trace or [
            getattr(t, "sub_agent", "") for t in session.history if hasattr(t, "sub_agent")
        ]
        trace_steps = [s for s in trace if s]
        if trace_steps:
            trace_html = " &rarr; ".join(
                f'<span class="gemma-trace-pill">{html.escape(s)}</span>' for s in trace_steps
            )
        else:
            trace_html = (
                f'<span class="gemma-trace-pill">'
                f'{html.escape(session.active_sub_agent or "N/A")}'
                f"</span>"
            )

        flags: List[str] = []
        if getattr(session, "timed_out", False):
            flags.append('<span class="gemma-badge gemma-badge-error">TIMED OUT</span>')
        if getattr(session, "budget_exhausted", False):
            flags.append('<span class="gemma-badge gemma-badge-error">BUDGET EXHAUSTED</span>')
        if metric is not None and not getattr(metric, "patch_applied", True):
            flags.append('<span class="gemma-badge gemma-badge-error">PATCH REJECTED</span>')

        flags_html = " ".join(flags)

        err_msg = getattr(session, "error_message", None) or (
            getattr(metric, "error_message", None) if metric is not None else None
        )
        alert_html = (
            f'<div class="gemma-alert gemma-alert-error">'
            f"<strong>Error:</strong> {html.escape(err_msg)}</div>"
            if err_msg
            else ""
        )

        diff_view_html = cls.render_diff_html(session.patch)

        test_output_html = ""
        if metric is not None and metric.test_output:
            test_output_html = f"""
    <details class="gemma-accordion">
      <summary>🧪 Test Suite Output (Exit code: {metric.exit_code})</summary>
      <div class="gemma-accordion-body">
        <pre class="gemma-code-block"><code>{html.escape(metric.test_output)}</code></pre>
      </div>
    </details>
""".strip()

        session_html = f"""
<div class="gemma-telemetry-container">
  <div class="gemma-card">
    <div class="gemma-header">
      <div>
        <strong style="font-size:16px;">Instance: {html.escape(session.instance_id)}</strong>
        <span style="margin-left:8px;">{status_badge}</span>
        {flags_html}
      </div>
      <span class="gemma-chip-duration">⏱ {duration:.2f}s</span>
    </div>

    {alert_html}

    <div class="gemma-meta-grid">
      <div class="gemma-meta-item">
        <div class="gemma-meta-label">Turns Used</div>
        <div class="gemma-meta-value">{turns}</div>
      </div>
      <div class="gemma-meta-item">
        <div class="gemma-meta-label">Duration</div>
        <div class="gemma-meta-value">{duration:.2f}s</div>
      </div>
      <div class="gemma-meta-item">
        <div class="gemma-meta-label">SubAgent Flow</div>
        <div style="margin-top:4px;">{trace_html}</div>
      </div>
    </div>

    <details class="gemma-accordion" open>
      <summary>📄 Generated Patch Diff</summary>
      <div class="gemma-accordion-body" style="padding:0;">
        {diff_view_html}
      </div>
    </details>

    {test_output_html}
  </div>
</div>
""".strip()
        return cls._wrap_with_style(session_html)

    @classmethod
    def render_benchmark_report_html(cls, summary: BenchmarkSummary) -> str:
        """Generates an interactive HTML table showing benchmark evaluation results.

        Displays Pass@1 rate with visual percentage progress bar, summary counters,
        and searchable/filterable table of task instances.

        Args:
            summary: Aggregated BenchmarkSummary statistics.

        Returns:
            Complete HTML benchmark report with client-side interactivity.
        """
        pass_pct = summary.pass_at_1 * 100
        total = summary.total_instances
        resolved = summary.resolved_count
        failed = summary.failed_count
        avg_dur = summary.avg_duration_seconds

        table_rows: List[str] = []
        for idx, r in enumerate(summary.results, start=1):
            is_res = r.resolved
            badge = (
                '<span class="gemma-badge gemma-badge-resolved">RESOLVED</span>'
                if is_res
                else '<span class="gemma-badge gemma-badge-failed">FAILED</span>'
            )
            patch_text = "Yes" if r.patch_applied else '<span style="color:#f87171;">No</span>'

            detail_section = ""
            if r.error_message or r.test_output:
                detail_content = html.escape(r.error_message or r.test_output[:300])
                detail_section = (
                    f'<details><summary style="cursor:pointer; color:#38bdf8;">'
                    f"View</summary>"
                    f'<pre class="gemma-code-block" style="font-size:10px;">'
                    f"<code>{detail_content}</code></pre></details>"
                )
            else:
                detail_section = "-"

            row_html = f"""
  <tr data-resolved="{'true' if is_res else 'false'}" data-id="{html.escape(r.instance_id)}">
    <td style="color:#94a3b8;">{idx}</td>
    <td><code>{html.escape(r.instance_id)}</code></td>
    <td>{badge}</td>
    <td>{r.exit_code}</td>
    <td>{r.duration_seconds:.2f}s</td>
    <td>{r.tool_calls_count}</td>
    <td>{patch_text}</td>
    <td>{detail_section}</td>
  </tr>
""".strip()
            table_rows.append(row_html)

        rows_content = "\n".join(table_rows)

        report_html = f"""
<div class="gemma-telemetry-container">
  <h2 style="margin-top:0; color:#f8fafc; font-size:18px;">
    SWE-bench Evaluation Benchmark Report
  </h2>

  <div class="gemma-kpi-grid">
    <div class="gemma-kpi-card">
      <div class="gemma-kpi-label">Pass@1 Resolution Rate</div>
      <div class="gemma-kpi-value">{pass_pct:.1f}%</div>
      <div class="gemma-progress-track">
        <div class="gemma-progress-fill" style="width: {min(100.0, max(0.0, pass_pct)):.1f}%;">
        </div>
      </div>
    </div>
    <div class="gemma-kpi-card">
      <div class="gemma-kpi-label">Resolved / Total</div>
      <div class="gemma-kpi-value">{resolved} / {total}</div>
    </div>
    <div class="gemma-kpi-card">
      <div class="gemma-kpi-label">Failed Instances</div>
      <div class="gemma-kpi-value">{failed}</div>
    </div>
    <div class="gemma-kpi-card">
      <div class="gemma-kpi-label">Avg Latency / Task</div>
      <div class="gemma-kpi-value">{avg_dur:.2f}s</div>
    </div>
  </div>

  <div class="gemma-card" style="padding:10px;">
    <div class="gemma-table-controls">
      <div>
        <button class="gemma-filter-btn active" onclick="gemmaFilterRows('all', this)">
          All ({total})
        </button>
        <button class="gemma-filter-btn" onclick="gemmaFilterRows('resolved', this)">
          Resolved ({resolved})
        </button>
        <button class="gemma-filter-btn" onclick="gemmaFilterRows('failed', this)">
          Failed ({failed})
        </button>
      </div>
      <input
        type="text"
        id="gemma-table-search"
        class="gemma-search-input"
        placeholder="Filter by instance ID..."
        onkeyup="gemmaSearchRows()"
      />
    </div>

    <table class="gemma-report-table" id="gemma-benchmark-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Instance ID</th>
          <th>Status</th>
          <th>Exit</th>
          <th>Duration</th>
          <th>Tools</th>
          <th>Patch</th>
          <th>Diagnostics</th>
        </tr>
      </thead>
      <tbody>
{rows_content}
      </tbody>
    </table>
  </div>
</div>

<script>
function gemmaFilterRows(filter, btn) {{
  var rows = document.querySelectorAll('#gemma-benchmark-table tbody tr');
  var buttons = document.querySelectorAll('.gemma-filter-btn');
  buttons.forEach(function(b) {{ b.classList.remove('active'); }});
  if (btn) btn.classList.add('active');
  rows.forEach(function(r) {{
    var isResolved = r.getAttribute('data-resolved') === 'true';
    if (filter === 'all') {{
      r.style.display = '';
    }} else if (filter === 'resolved') {{
      r.style.display = isResolved ? '' : 'none';
    }} else if (filter === 'failed') {{
      r.style.display = !isResolved ? '' : 'none';
    }}
  }});
}}

function gemmaSearchRows() {{
  var q = document.getElementById('gemma-table-search').value.toLowerCase();
  var rows = document.querySelectorAll('#gemma-benchmark-table tbody tr');
  rows.forEach(function(r) {{
    var id = (r.getAttribute('data-id') || '').toLowerCase();
    r.style.display = id.indexOf(q) !== -1 ? '' : 'none';
  }});
}}
</script>
""".strip()
        return cls._wrap_with_style(report_html)
