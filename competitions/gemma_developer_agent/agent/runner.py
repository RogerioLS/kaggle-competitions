"""Declarative Agent Runtime & Sub-Agent Orchestrator.

Executes declarative multi-agent workflows across codebase exploration, bug
localization, patch drafting, and verification phases while strictly enforcing
turn budgets, timeout guardrails, and tool authorization permissions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from competitions.gemma_developer_agent.agent.schema import (
    AgentConfig,
)
from competitions.gemma_developer_agent.evaluation.dataset_loader import (
    SWEInstance,
)
from competitions.gemma_developer_agent.evaluation.harness import (
    LocalSWEHarness,
)
from competitions.gemma_developer_agent.evaluation.metrics import (
    BenchmarkSummary,
    InstanceMetric,
)
from competitions.gemma_developer_agent.evaluation.sandbox import (
    SubprocessSandbox,
)


@dataclass
class ToolCall:
    """Represents an atomic tool invocation."""

    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnRecord:
    """Records a single conversational/execution turn in an agent session."""

    turn_index: int
    sub_agent: str
    tool_call: Optional[ToolCall] = None
    observation: str = ""
    duration_seconds: float = 0.0
    is_error: bool = False


@dataclass
class AgentSessionResult:
    """Comprehensive result summary of an agent execution session."""

    instance_id: str
    patch: str = ""
    turns_used: int = 0
    duration_seconds: float = 0.0
    success: bool = False
    timed_out: bool = False
    budget_exhausted: bool = False
    active_sub_agent: str = ""
    sub_agent_trace: List[str] = field(default_factory=list)
    history: List[TurnRecord] = field(default_factory=list)
    error_message: Optional[str] = None


class ToolPermissionError(Exception):
    """Raised when a sub-agent calls a tool outside its allowed permissions."""


class BudgetExhaustedError(Exception):
    """Raised when turn or token budgets are exhausted."""


class DeclarativeAgentRunner:
    """Orchestrates declarative agents against isolated evaluation environments."""

    def __init__(
        self,
        config: AgentConfig,
        sandbox: Optional[SubprocessSandbox] = None,
        code_graph: Optional[Any] = None,
        code_embeddings: Optional[Any] = None,
    ) -> None:
        """Initializes the declarative runner.

        Args:
            config: Validated AgentConfig specification.
            sandbox: Optional SubprocessSandbox execution environment.
            code_graph: Optional CodeGraph instance for AST structural queries.
            code_embeddings: Optional CodeEmbeddings instance for vector search.
        """
        self.config = config
        self.sandbox = sandbox
        self.code_graph = code_graph
        self.code_embeddings = code_embeddings

        self._tools: Dict[str, Callable[..., Any]] = {
            "search_similar_code": self._tool_search_similar_code,
            "get_code_neighbors": self._tool_get_code_neighbors,
            "get_code_subgraph": self._tool_get_code_subgraph,
            "read_file": self._tool_read_file,
            "edit_file": self._tool_edit_file,
            "write_file": self._tool_write_file,
            "run_command": self._tool_run_command,
            "get_status": self._tool_get_status,
            "submit_patch": self._tool_submit_patch,
        }

    def execute_turn(
        self,
        sub_agent_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session: AgentSessionResult,
        start_time: Optional[float] = None,
    ) -> TurnRecord:
        """Executes a single gated tool turn for a specific sub-agent.

        Args:
            sub_agent_name: Key of the active sub-agent.
            tool_name: Name of tool to execute.
            arguments: Arguments payload for the tool.
            session: Current session state accumulator.
            start_time: Optional wall-clock session start timestamp.

        Returns:
            TurnRecord recording observation and turn metrics.
        """
        turn_start = time.perf_counter()
        turn_idx = session.turns_used + 1
        active_start = start_time if start_time is not None else turn_start

        # Check total budget
        if session.turns_used >= self.config.budget.max_turns:
            session.budget_exhausted = True
            return TurnRecord(
                turn_index=turn_idx,
                sub_agent=sub_agent_name,
                observation="Turn budget exhausted.",
                is_error=True,
            )

        # Check timeout guardrail
        if active_start > 0:
            elapsed = time.perf_counter() - active_start
            if elapsed >= self.config.budget.timeout_seconds:
                session.timed_out = True
                return TurnRecord(
                    turn_index=turn_idx,
                    sub_agent=sub_agent_name,
                    observation=f"Session timed out after {elapsed:.2f}s.",
                    is_error=True,
                )

        sub_agent = self.config.sub_agents.get(sub_agent_name)
        if not sub_agent:
            return TurnRecord(
                turn_index=turn_idx,
                sub_agent=sub_agent_name,
                observation=f"Unknown sub-agent: {sub_agent_name}",
                is_error=True,
            )

        # Enforce tool permissions
        if tool_name not in sub_agent.allowed_tools:
            obs = (
                f"Permission denied: Sub-agent '{sub_agent_name}' is not authorized "
                f"to call '{tool_name}'. Allowed: {sub_agent.allowed_tools}"
            )
            session.turns_used += 1
            return TurnRecord(
                turn_index=turn_idx,
                sub_agent=sub_agent_name,
                tool_call=ToolCall(tool_name, arguments),
                observation=obs,
                duration_seconds=round(time.perf_counter() - turn_start, 3),
                is_error=True,
            )

        handler = self._tools.get(tool_name)
        if not handler:
            obs = f"Unimplemented tool: {tool_name}"
            session.turns_used += 1
            return TurnRecord(
                turn_index=turn_idx,
                sub_agent=sub_agent_name,
                tool_call=ToolCall(tool_name, arguments),
                observation=obs,
                duration_seconds=round(time.perf_counter() - turn_start, 3),
                is_error=True,
            )

        try:
            obs = str(handler(**arguments))
            is_err = False
        except Exception as exc:
            obs = f"Tool execution failed: {exc}"
            is_err = True

        duration = round(time.perf_counter() - turn_start, 3)
        session.turns_used += 1

        record = TurnRecord(
            turn_index=turn_idx,
            sub_agent=sub_agent_name,
            tool_call=ToolCall(tool_name, arguments),
            observation=obs,
            duration_seconds=duration,
            is_error=is_err,
        )
        session.history.append(record)
        return record

    def run_workflow_plan(
        self,
        instance: SWEInstance,
        planned_steps: List[Dict[str, Any]],
    ) -> AgentSessionResult:
        """Executes a structured sequence of planned agent turns.

        Args:
            instance: SWEInstance being addressed.
            planned_steps: List of dicts specifying sub_agent, tool, and arguments.

        Returns:
            Populated AgentSessionResult.
        """
        start_time = time.perf_counter()
        session = AgentSessionResult(instance_id=instance.instance_id)

        current_agent = self.config.workflow.sequence[0]
        session.active_sub_agent = current_agent
        session.sub_agent_trace.append(current_agent)

        for step in planned_steps:
            target_agent = step.get("sub_agent", current_agent)
            if target_agent != current_agent:
                current_agent = target_agent
                session.active_sub_agent = current_agent
                session.sub_agent_trace.append(current_agent)

            tool_name = step.get("tool", "")
            args = step.get("arguments", {})

            record = self.execute_turn(
                sub_agent_name=current_agent,
                tool_name=tool_name,
                arguments=args,
                session=session,
                start_time=start_time,
            )

            # Check if submit_patch was called
            if tool_name == "submit_patch" and not record.is_error:
                session.patch = record.observation
                session.success = bool(session.patch.strip())
                break

            if session.budget_exhausted or session.timed_out:
                break

        # If submit_patch wasn't explicitly called, capture current git diff
        if not session.patch and self.sandbox:
            session.patch = self.sandbox.get_diff()
            session.success = bool(session.patch.strip())

        session.duration_seconds = round(time.perf_counter() - start_time, 3)
        return session

    def benchmark_on_instance(
        self,
        instance: SWEInstance,
        harness: LocalSWEHarness,
        planned_steps: List[Dict[str, Any]],
        base_files: Optional[Dict[str, str]] = None,
        test_cmd: Optional[List[str]] = None,
    ) -> Tuple[AgentSessionResult, InstanceMetric]:
        """Executes agent plan against an isolated sandbox and benchmarks outcome.

        Args:
            instance: Target SWEInstance task definition.
            harness: LocalSWEHarness evaluation engine.
            planned_steps: List of dicts specifying sub_agent, tool, and arguments.
            base_files: Optional dict mapping relative file paths to content strings.
            test_cmd: Optional custom test execution command.

        Returns:
            Tuple of (AgentSessionResult, InstanceMetric).
        """
        with SubprocessSandbox() as run_sandbox:
            if base_files:
                for rel_path, content in base_files.items():
                    run_sandbox.write_file(rel_path, content)
                run_sandbox.commit_all("baseline")

            orig_sandbox = self.sandbox
            self.sandbox = run_sandbox
            try:
                session = self.run_workflow_plan(instance, planned_steps)
            finally:
                self.sandbox = orig_sandbox

        metric = harness.evaluate_instance(
            instance=instance,
            agent_patch=session.patch,
            base_files=base_files,
            test_cmd=test_cmd,
        )
        return session, metric

    def benchmark_on_dataset(
        self,
        instances: List[SWEInstance],
        harness: LocalSWEHarness,
        plans_map: Dict[str, List[Dict[str, Any]]],
        base_files_map: Optional[Dict[str, Dict[str, str]]] = None,
        test_cmd: Optional[List[str]] = None,
    ) -> Tuple[List[AgentSessionResult], BenchmarkSummary]:
        """Executes agent workflow across multiple tasks and aggregates metrics.

        Args:
            instances: List of SWEInstance tasks.
            harness: LocalSWEHarness evaluation engine.
            plans_map: Dict mapping instance_id to list of planned execution steps.
            base_files_map: Optional mapping of instance_id to base files dict.
            test_cmd: Optional custom test execution command.

        Returns:
            Tuple of (List[AgentSessionResult], BenchmarkSummary).
        """
        sessions: List[AgentSessionResult] = []
        metrics: List[InstanceMetric] = []
        base_map = base_files_map or {}

        for inst in instances:
            plan = plans_map.get(inst.instance_id, [])
            base_files = base_map.get(inst.instance_id)
            session, metric = self.benchmark_on_instance(
                instance=inst,
                harness=harness,
                planned_steps=plan,
                base_files=base_files,
                test_cmd=test_cmd,
            )
            sessions.append(session)
            metrics.append(metric)

        summary = BenchmarkSummary.from_results(metrics)
        return sessions, summary

    # ---------------- Tool Handlers ----------------

    def _tool_search_similar_code(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        if self.code_embeddings:
            return self.code_embeddings.search_similar(query, k=k)
        return []

    def _tool_get_code_neighbors(
        self, node: str, edge_type: Optional[str] = None, max_neighbors: int = 50
    ) -> List[str]:
        if self.code_graph:
            return self.code_graph.get_neighbors(node, edge_type=edge_type)[:max_neighbors]
        return []

    def _tool_get_code_subgraph(self, nodes: List[str]) -> Dict[str, Any]:
        if self.code_graph:
            return self.code_graph.get_subgraph(nodes)
        return {"nodes": nodes, "edges": []}

    def _tool_read_file(
        self,
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> str:
        if self.sandbox:
            content = self.sandbox.read_file(filepath)
            lines = content.splitlines(keepends=True)
            s_idx = max(0, (start_line - 1)) if start_line is not None else 0
            e_idx = end_line if end_line is not None else len(lines)
            return "".join(lines[s_idx:e_idx])
        # Fallback to local filesystem if sandbox is absent
        target = Path(filepath)
        if target.is_file():
            content = target.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)
            s_idx = max(0, (start_line - 1)) if start_line is not None else 0
            e_idx = end_line if end_line is not None else len(lines)
            return "".join(lines[s_idx:e_idx])
        return f"File not found: {filepath}"

    def _tool_edit_file(
        self,
        filepath: str,
        old_string: str,
        new_string: str,
        allow_multiple: bool = False,
    ) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized for edits."
        content = self.sandbox.read_file(filepath)
        count = content.count(old_string)
        if count == 0:
            return f"Error: '{old_string}' not found in {filepath}."
        if count > 1 and not allow_multiple:
            return f"Error: '{old_string}' occurs {count} times in {filepath}."

        new_content = (
            content.replace(old_string, new_string)
            if allow_multiple
            else content.replace(old_string, new_string, 1)
        )
        self.sandbox.write_file(filepath, new_content)
        return f"Successfully modified {filepath}."

    def _tool_write_file(self, filepath: str, content: str) -> str:
        if self.sandbox:
            self.sandbox.write_file(filepath, content)
            return f"File written successfully: {filepath}"
        return "Error: Sandbox not initialized."

    def _tool_run_command(self, command: str) -> str:
        if self.sandbox:
            res = self.sandbox.execute(command)
            return f"Exit code: {res.exit_code}\nOutput:\n{res.stdout}\n{res.stderr}".strip()
        return "Error: Sandbox not initialized."

    def _tool_get_status(self) -> Dict[str, Any]:
        diff_str = self.sandbox.get_diff() if self.sandbox else ""
        return {
            "budget": {
                "max_turns": self.config.budget.max_turns,
                "timeout_seconds": self.config.budget.timeout_seconds,
            },
            "dirty": bool(diff_str.strip()),
        }

    def _tool_submit_patch(self) -> str:
        if self.sandbox:
            diff = self.sandbox.get_diff()
            return diff
        return ""
