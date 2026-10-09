"""Unit Tests for Declarative Agent Architecture & Baseline Runtime.

Validates declarative YAML configurations, prompt resolution, sub-agent tool
authorizations, turn budget and timeout guardrails, and benchmark integration
with LocalSWEHarness.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from competitions.gemma_developer_agent.agent.runner import (
    AgentSessionResult,
    DeclarativeAgentRunner,
)
from competitions.gemma_developer_agent.agent.schema import (
    AgentConfig,
    ConfigValidationError,
    SubAgentConfig,
)
from competitions.gemma_developer_agent.evaluation.dataset_loader import (
    SWEInstance,
)
from competitions.gemma_developer_agent.evaluation.harness import (
    LocalSWEHarness,
)
from competitions.gemma_developer_agent.evaluation.sandbox import (
    SubprocessSandbox,
)


@pytest.fixture
def agent_yaml_path() -> Path:
    """Returns absolute path to repository's default agent.yaml."""
    path = (
        Path(__file__).parent.parent.parent
        / "competitions"
        / "gemma_developer_agent"
        / "agent"
        / "agent.yaml"
    )
    return path.resolve()


@pytest.fixture
def default_agent_config(agent_yaml_path: Path) -> AgentConfig:
    """Loads default repository AgentConfig."""
    return AgentConfig.from_yaml(agent_yaml_path)


class TestAgentSchemaValidation:
    """Tests declarative YAML parsing and constraint validation."""

    def test_load_default_agent_yaml(self, default_agent_config: AgentConfig) -> None:
        """Verifies default agent.yaml and its sub-agents load correctly."""
        cfg = default_agent_config
        assert cfg.name == "gemma-4-developer-agent"
        assert cfg.version == "1.0.0"
        assert cfg.model == "gemma-4-31b-it-qat-w4a16-ct"
        assert cfg.budget.max_turns == 20
        assert cfg.budget.timeout_seconds == 300
        assert len(cfg.system_prompt_content) > 50

        # Sub-agents
        assert set(cfg.sub_agents.keys()) == {"explorer", "locator", "drafter", "validator"}
        assert cfg.sub_agents["explorer"].role == "Codebase Navigator"
        assert "read_file" in cfg.sub_agents["explorer"].allowed_tools
        assert "edit_file" not in cfg.sub_agents["explorer"].allowed_tools
        assert "submit_patch" in cfg.sub_agents["validator"].allowed_tools

        # Workflow
        assert cfg.workflow.sequence == ["explorer", "locator", "drafter", "validator"]
        assert cfg.workflow.fallback_on_failure == "locator"

    def test_subagent_unsupported_tool_raises_error(self) -> None:
        """Verifies declaring an unsupported tool raises ConfigValidationError."""
        sa = SubAgentConfig(
            name="hacker",
            role="Attacker",
            description="Tries to access root shell",
            prompt_path="prompts/dummy.md",
            allowed_tools=["sudo_rm_rf", "read_file"],
        )
        with pytest.raises(ConfigValidationError) as exc:
            sa.validate()
        assert "unsupported tool 'sudo_rm_rf'" in str(exc.value)

    def test_invalid_workflow_sequence_raises_error(self, tmp_path: Path) -> None:
        """Verifies workflow referencing undeclared sub-agent raises error."""
        agent_file = tmp_path / "agent.yaml"
        prompt_file = tmp_path / "system.md"
        prompt_file.write_text("Hello", encoding="utf-8")

        data = {
            "name": "test-agent",
            "system_prompt": "system.md",
            "sub_agents": {},
            "workflow": {
                "sequence": ["non_existent_agent"],
                "fallback_on_failure": "non_existent_agent",
            },
        }
        agent_file.write_text(yaml.safe_dump(data), encoding="utf-8")

        with pytest.raises(ConfigValidationError) as exc:
            AgentConfig.from_yaml(agent_file)
        assert "is not declared in sub_agents" in str(exc.value)

    def test_missing_prompt_file_raises_error(self, tmp_path: Path) -> None:
        """Verifies referencing non-existent prompt raises ConfigValidationError."""
        agent_file = tmp_path / "agent.yaml"
        data = {
            "name": "test-agent",
            "system_prompt": "does_not_exist.md",
            "sub_agents": {},
        }
        agent_file.write_text(yaml.safe_dump(data), encoding="utf-8")

        with pytest.raises(ConfigValidationError) as exc:
            AgentConfig.from_yaml(agent_file)
        assert "System prompt file not found" in str(exc.value)


class TestDeclarativeAgentRunner:
    """Tests runtime execution, tool permissions, and budget guardrails."""

    def test_tool_permission_enforcement(self, default_agent_config: AgentConfig) -> None:
        """Verifies unauthorized tool calls by a sub-agent are blocked."""
        runner = DeclarativeAgentRunner(config=default_agent_config)
        session = AgentSessionResult(instance_id="test-001")

        # Explorer tries to edit_file (which is only allowed for drafter/validator)
        record = runner.execute_turn(
            sub_agent_name="explorer",
            tool_name="edit_file",
            arguments={"filepath": "main.py", "old_string": "a", "new_string": "b"},
            session=session,
        )

        assert record.is_error is True
        assert "Permission denied" in record.observation
        assert session.turns_used == 1

    def test_turn_budget_exhaustion(self, default_agent_config: AgentConfig) -> None:
        """Verifies runner halts when turn budget is exceeded."""
        cfg = default_agent_config
        cfg.budget.max_turns = 2
        runner = DeclarativeAgentRunner(config=cfg)
        session = AgentSessionResult(instance_id="test-002")

        # Turn 1
        runner.execute_turn("explorer", "get_status", {}, session)
        # Turn 2
        runner.execute_turn("explorer", "get_status", {}, session)
        assert session.turns_used == 2
        assert session.budget_exhausted is False

        # Turn 3 (exceeds max_turns)
        record = runner.execute_turn("explorer", "get_status", {}, session)
        assert record.is_error is True
        assert "budget exhausted" in record.observation.lower()
        assert session.budget_exhausted is True

    def test_timeout_guardrail_enforcement(self, default_agent_config: AgentConfig) -> None:
        """Verifies runner halts when timeout guardrail is breached."""
        import time

        cfg = default_agent_config
        cfg.budget.timeout_seconds = 1  # 1 second timeout
        runner = DeclarativeAgentRunner(config=cfg)
        session = AgentSessionResult(instance_id="test-003")

        # Start time set 10 seconds in the past to trigger timeout
        simulated_start = time.perf_counter() - 10.0
        record = runner.execute_turn(
            "explorer", "get_status", {}, session, start_time=simulated_start
        )
        assert record.is_error is True
        assert session.timed_out is True
        assert "timed out" in record.observation.lower()

    def test_run_workflow_plan_execution(
        self, default_agent_config: AgentConfig, tmp_path: Path
    ) -> None:
        """Verifies sequential sub-agent execution against a sandbox."""
        inst = SWEInstance(
            instance_id="calc-fix-01",
            repo="test/calc",
            base_commit="abc123",
            problem_statement="fix add function",
            patch="",
            test_patch="",
        )

        with SubprocessSandbox() as sandbox:
            sandbox.write_file("calc.py", "def add(a, b):\n    return a - b\n")
            sandbox.commit_all("baseline")

            runner = DeclarativeAgentRunner(config=default_agent_config, sandbox=sandbox)

            plan = [
                {
                    "sub_agent": "explorer",
                    "tool": "read_file",
                    "arguments": {"filepath": "calc.py"},
                },
                {
                    "sub_agent": "locator",
                    "tool": "get_status",
                    "arguments": {},
                },
                {
                    "sub_agent": "drafter",
                    "tool": "edit_file",
                    "arguments": {
                        "filepath": "calc.py",
                        "old_string": "return a - b",
                        "new_string": "return a + b",
                    },
                },
                {
                    "sub_agent": "validator",
                    "tool": "submit_patch",
                    "arguments": {},
                },
            ]

            session = runner.run_workflow_plan(inst, plan)
            assert session.success is True
            assert session.turns_used == 4
            assert "return a + b" in session.patch
            assert "-    return a - b" in session.patch
            assert "+    return a + b" in session.patch
            assert session.sub_agent_trace == ["explorer", "locator", "drafter", "validator"]


class TestDeclarativeAgentBenchmarking:
    """Tests end-to-end benchmarking of agent against LocalSWEHarness."""

    def test_benchmark_on_instance_pass(
        self, default_agent_config: AgentConfig, tmp_path: Path
    ) -> None:
        """Verifies benchmark_on_instance runs plan and scores Pass@1."""
        harness = LocalSWEHarness(base_dir=tmp_path / "benchmarks")
        runner = DeclarativeAgentRunner(config=default_agent_config)

        instance = SWEInstance(
            instance_id="bench-001",
            repo="simple/math",
            base_commit="init",
            problem_statement="Fix multiplication function",
            patch="diff --git a/math_mod.py b/math_mod.py\n",
            test_patch=(
                "diff --git a/test_math.py b/test_math.py\n"
                "new file mode 100644\n"
                "--- /dev/null\n"
                "+++ b/test_math.py\n"
                "@@ -0,0 +1,5 @@\n"
                "+from math_mod import multiply\n"
                "+def test_multiply():\n"
                "+    assert multiply(3, 4) == 12\n"
            ),
        )

        base_files = {
            "math_mod.py": "def multiply(a, b):\n    return a + b\n",
        }

        plan = [
            {
                "sub_agent": "explorer",
                "tool": "read_file",
                "arguments": {"filepath": "math_mod.py"},
            },
            {
                "sub_agent": "drafter",
                "tool": "edit_file",
                "arguments": {
                    "filepath": "math_mod.py",
                    "old_string": "return a + b",
                    "new_string": "return a * b",
                },
            },
            {
                "sub_agent": "validator",
                "tool": "submit_patch",
                "arguments": {},
            },
        ]

        session, metric = runner.benchmark_on_instance(
            instance=instance,
            harness=harness,
            planned_steps=plan,
            base_files=base_files,
        )

        assert session.success is True
        assert metric.resolved is True
        assert metric.exit_code == 0
        assert metric.instance_id == "bench-001"
        assert metric.patch_applied is True

    def test_benchmark_on_dataset_aggregation(
        self, default_agent_config: AgentConfig, tmp_path: Path
    ) -> None:
        """Verifies benchmark_on_dataset aggregates metrics across tasks."""
        harness = LocalSWEHarness(base_dir=tmp_path / "benchmarks")
        runner = DeclarativeAgentRunner(config=default_agent_config)

        inst1 = SWEInstance(
            instance_id="task-1",
            repo="r1",
            base_commit="c1",
            problem_statement="p1",
            patch="",
            test_patch=(
                "diff --git a/test_t1.py b/test_t1.py\n"
                "new file mode 100644\n"
                "--- /dev/null\n"
                "+++ b/test_t1.py\n"
                "@@ -0,0 +1,3 @@\n"
                "+from m1 import f\n"
                "+def test_f():\n"
                "+    assert f() == 1\n"
            ),
        )

        inst2 = SWEInstance(
            instance_id="task-2",
            repo="r2",
            base_commit="c2",
            problem_statement="p2",
            patch="",
            test_patch=(
                "diff --git a/test_t2.py b/test_t2.py\n"
                "new file mode 100644\n"
                "--- /dev/null\n"
                "+++ b/test_t2.py\n"
                "@@ -0,0 +1,3 @@\n"
                "+from m2 import g\n"
                "+def test_g():\n"
                "+    assert g() == 2\n"
            ),
        )

        base_map = {
            "task-1": {"m1.py": "def f(): return 1\n"},
            "task-2": {"m2.py": "def g(): return 0\n"},
        }

        # Plan for task-1 submits empty change (already passing), task-2 fixes g()
        plans = {
            "task-1": [{"sub_agent": "validator", "tool": "submit_patch", "arguments": {}}],
            "task-2": [
                {
                    "sub_agent": "drafter",
                    "tool": "edit_file",
                    "arguments": {
                        "filepath": "m2.py",
                        "old_string": "return 0",
                        "new_string": "return 2",
                    },
                },
                {"sub_agent": "validator", "tool": "submit_patch", "arguments": {}},
            ],
        }

        sessions, summary = runner.benchmark_on_dataset(
            instances=[inst1, inst2],
            harness=harness,
            plans_map=plans,
            base_files_map=base_map,
        )

        assert len(sessions) == 2
        assert summary.total_instances == 2
        # task-2 has patch applied and resolved
        assert summary.resolved_count >= 1
