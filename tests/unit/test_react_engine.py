"""Unit tests for Gemma 4 Autonomous ReAct Engine and Inference Backends."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from competitions.gemma_developer_agent.agent.inference_engine import (
    END_OF_TURN,
    MODEL_ROLE,
    START_OF_TURN,
    USER_ROLE,
    ChatMessage,
    GemmaPromptFormatter,
    MockInferenceEngine,
)
from competitions.gemma_developer_agent.agent.react_orchestrator import (
    ReActOrchestrator,
    ReActParseError,
    ReActParser,
)
from competitions.gemma_developer_agent.agent.runner import (
    DeclarativeAgentRunner,
)
from competitions.gemma_developer_agent.agent.schema import (
    AgentConfig,
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
def sample_agent_config() -> AgentConfig:
    """Loads the repository default AgentConfig."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    agent_yaml = repo_root / "competitions" / "gemma_developer_agent" / "agent" / "agent.yaml"
    return AgentConfig.from_yaml(agent_yaml)


class TestGemmaPromptFormatter:
    """Verifies turn token structuring and chat rendering."""

    def test_chat_message_role_validation(self) -> None:
        """Valid roles succeed; invalid roles raise ValueError."""
        msg_user = ChatMessage(role=USER_ROLE, content="Hello")
        assert msg_user.role == USER_ROLE

        msg_model = ChatMessage(role=MODEL_ROLE, content="Hi")
        assert msg_model.role == MODEL_ROLE

        with pytest.raises(ValueError, match="Invalid role"):
            ChatMessage(role="system", content="not allowed")

    def test_render_tool_declarations(self) -> None:
        """Renders tool specifications into markdown with JSON schemas."""
        tools = {
            "read_file": {"description": "Reads a file", "parameters": {"filepath": "path"}},
            "submit_patch": {"description": "Submits final patch", "parameters": {}},
        }
        rendered = GemmaPromptFormatter.render_tool_declarations(tools)
        assert "### Available Tools" in rendered
        assert "- **`read_file`**: Reads a file" in rendered
        assert "- **`submit_patch`**: Submits final patch" in rendered
        assert "### Action Output Format" in rendered

    def test_format_conversation_single_and_multi_turn(self) -> None:
        """Renders Gemma 4 turn tokens in strict sequence."""
        messages = [
            ChatMessage(role=USER_ROLE, content="Fix bug in router"),
            ChatMessage(role=MODEL_ROLE, content='```json\n{"tool": "read_file"}\n```'),
            ChatMessage(role=USER_ROLE, content="Observation: file content"),
        ]
        prompt = GemmaPromptFormatter.format_conversation(
            messages=messages,
            system_prompt="System instructions.",
            add_generation_prompt=True,
        )

        assert f"{START_OF_TURN}{USER_ROLE}" in prompt
        assert "System instructions." in prompt
        assert "Fix bug in router" in prompt
        assert f"{END_OF_TURN}" in prompt
        assert f"{START_OF_TURN}{MODEL_ROLE}" in prompt
        assert prompt.endswith(f"{START_OF_TURN}{MODEL_ROLE}\n")


class TestReActParser:
    """Tests action parsing from diverse LLM output representations."""

    def test_parse_fenced_json(self) -> None:
        """Parses standard ```json code fence block."""
        output = """
Here is my reasoning: I should read the target module first.
```json
{
  "thought": "Need to view the router implementation",
  "sub_agent": "locator",
  "tool": "read_file",
  "arguments": {"filepath": "app/router.py"}
}
```
"""
        action = ReActParser.parse(output)
        assert action.thought == "Need to view the router implementation"
        assert action.sub_agent == "locator"
        assert action.tool == "read_file"
        assert action.arguments == {"filepath": "app/router.py"}
        assert action.is_final is False

    def test_parse_raw_json_without_code_fence(self) -> None:
        """Parses plain JSON without markdown blocks."""
        output = json.dumps(
            {
                "thought": "Run verification",
                "sub_agent": "validator",
                "tool": "run_command",
                "arguments": {"command": "pytest"},
            }
        )
        action = ReActParser.parse(output)
        assert action.sub_agent == "validator"
        assert action.tool == "run_command"
        assert action.arguments == {"command": "pytest"}

    def test_parse_nested_action_dict(self) -> None:
        """Parses action dictionary structure."""
        output = """
```json
{
  "thought": "Check AST structure",
  "action": {
    "tool": "get_code_neighbors",
    "arguments": {"node": "FastAPI"}
  }
}
```
"""
        action = ReActParser.parse(output)
        assert action.tool == "get_code_neighbors"
        assert action.arguments == {"node": "FastAPI"}
        assert action.sub_agent == "explorer"  # Default heuristic

    def test_parse_submit_patch_is_final(self) -> None:
        """Calling submit_patch marks action as final."""
        output = """
```json
{
  "thought": "All tests pass. Finished.",
  "sub_agent": "validator",
  "tool": "submit_patch",
  "arguments": {}
}
```
"""
        action = ReActParser.parse(output)
        assert action.tool == "submit_patch"
        assert action.is_final is True

    def test_parse_trailing_commas_cleaned(self) -> None:
        """Tolerates trailing commas in JSON object."""
        output = """
```json
{
  "thought": "Trailing comma test",
  "tool": "read_file",
  "arguments": {
    "filepath": "main.py",
  },
}
```
"""
        action = ReActParser.parse(output)
        assert action.tool == "read_file"
        assert action.arguments == {"filepath": "main.py"}

    def test_parse_missing_tool_raises_error(self) -> None:
        """JSON missing 'tool' field raises ReActParseError."""
        output = '```json\n{"thought": "Only thought without tool"}\n```'
        with pytest.raises(ReActParseError, match="Missing required field 'tool'"):
            ReActParser.parse(output)

    def test_parse_no_json_raises_error(self) -> None:
        """Free-form text with no JSON raises ReActParseError."""
        output = "I think the bug is in main.py, let's change line 4."
        with pytest.raises(ReActParseError, match="No JSON action block found"):
            ReActParser.parse(output)


class TestReActOrchestrator:
    """Verifies multi-turn execution, sandbox integration, and closed-loop testing."""

    def test_autonomous_closed_loop_bug_resolution(self, sample_agent_config: AgentConfig) -> None:
        """Simulates full autonomous closed-loop debugging flow:
        read -> write reproducer -> run test (fails) -> edit -> verify -> submit.
        """
        reproducer_script = (
            "import pytest\n"
            "from app.calculator import add\n\n"
            "def test_add():\n"
            "    assert add(2, 2) == 4\n"
        )

        canned_dialogue = [
            # Turn 1: Inspect file
            json.dumps(
                {
                    "thought": "Read the calculator implementation",
                    "sub_agent": "locator",
                    "tool": "read_file",
                    "arguments": {"filepath": "app/calculator.py"},
                }
            ),
            # Turn 2: Write reproducer test
            json.dumps(
                {
                    "thought": "Write reproducer test for add function",
                    "sub_agent": "drafter",
                    "tool": "write_file",
                    "arguments": {"filepath": "reproducer.py", "content": reproducer_script},
                }
            ),
            # Turn 3: Run reproducer (observe failure)
            json.dumps(
                {
                    "thought": "Run pytest on reproducer to observe failure",
                    "sub_agent": "validator",
                    "tool": "run_command",
                    "arguments": {
                        "command": "python3 -c 'import pytest; print(\"FAILED: 2+2=5\")'"
                    },
                }
            ),
            # Turn 4: Edit buggy function
            json.dumps(
                {
                    "thought": "Fix calculation in calculator.py",
                    "sub_agent": "drafter",
                    "tool": "edit_file",
                    "arguments": {
                        "filepath": "app/calculator.py",
                        "old_string": "return a + b + 1",
                        "new_string": "return a + b",
                    },
                }
            ),
            # Turn 5: Run reproducer again (passes)
            json.dumps(
                {
                    "thought": "Verify fix with pytest",
                    "sub_agent": "validator",
                    "tool": "run_command",
                    "arguments": {"command": "python3 -c 'print(\"1 passed\")'"},
                }
            ),
            # Turn 6: Submit final patch
            json.dumps(
                {
                    "thought": "Fix verified. Submit patch.",
                    "sub_agent": "validator",
                    "tool": "submit_patch",
                    "arguments": {},
                }
            ),
        ]

        engine = MockInferenceEngine(canned_responses=canned_dialogue)

        with SubprocessSandbox() as sandbox:
            sandbox.write_file(
                "app/calculator.py",
                "def add(a: int, b: int) -> int:\n    return a + b + 1\n",
            )
            sandbox.commit_all("initial buggy commit")

            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            orchestrator = ReActOrchestrator(runner=runner, inference_engine=engine)

            instance = SWEInstance(
                instance_id="calc-bug-1",
                repo="math/calc",
                base_commit="hash123",
                problem_statement="add(2, 2) returns 5 instead of 4",
            )

            session = orchestrator.solve(instance=instance)

            assert session.success is True
            assert session.turns_used == 6
            assert "diff --git" in session.patch
            assert "-    return a + b + 1" in session.patch
            assert "+    return a + b" in session.patch

    def test_parse_error_recovery_turn(self, sample_agent_config: AgentConfig) -> None:
        """When model emits invalid format, orchestrator feeds back error observation."""
        canned_dialogue = [
            "This is not JSON at all!",  # Turn 1 invalid
            json.dumps(
                {
                    "thought": "Correcting format to JSON",
                    "sub_agent": "validator",
                    "tool": "submit_patch",
                    "arguments": {},
                }
            ),  # Turn 2 valid
        ]

        engine = MockInferenceEngine(canned_responses=canned_dialogue)

        with SubprocessSandbox() as sandbox:
            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            orchestrator = ReActOrchestrator(runner=runner, inference_engine=engine)

            instance = SWEInstance(
                instance_id="err-recov-1",
                repo="sample/repo",
                base_commit="hash",
                problem_statement="Fix parser recovery",
            )

            session = orchestrator.solve(instance=instance)
            assert len(session.history) == 2
            assert session.history[0].is_error is True
            assert "ActionParseError" in session.history[0].observation
            assert session.history[1].is_error is False

    def test_solve_instance_runner_integration(self, sample_agent_config: AgentConfig) -> None:
        """DeclarativeAgentRunner.solve_instance operates autonomously."""
        engine = MockInferenceEngine()  # Default submits patch immediately

        with SubprocessSandbox() as sandbox:
            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            instance = SWEInstance(
                instance_id="test-runner-solve",
                repo="sample/repo",
                base_commit="hash",
                problem_statement="Test solve_instance API",
            )
            session = runner.solve_instance(instance=instance, inference_engine=engine)
            assert session.instance_id == "test-runner-solve"
            assert session.turns_used == 1

    def test_benchmark_on_instance_with_inference_engine(
        self, tmp_path: Path, sample_agent_config: AgentConfig
    ) -> None:
        """Harness benchmarks autonomous ReAct engine without planned_steps."""
        engine = MockInferenceEngine(
            canned_responses=[
                json.dumps(
                    {
                        "thought": "Make fix",
                        "sub_agent": "drafter",
                        "tool": "edit_file",
                        "arguments": {
                            "filepath": "main.py",
                            "old_string": "def run(): pass",
                            "new_string": "def run(): return 42",
                        },
                    }
                ),
                json.dumps(
                    {
                        "thought": "Submit",
                        "sub_agent": "validator",
                        "tool": "submit_patch",
                        "arguments": {},
                    }
                ),
            ]
        )

        harness = LocalSWEHarness(base_dir=tmp_path / "harness")
        runner = DeclarativeAgentRunner(config=sample_agent_config)

        instance = SWEInstance(
            instance_id="harness-test-1",
            repo="sample/repo",
            base_commit="hash",
            problem_statement="Return 42 from run()",
        )

        base_files = {"main.py": "def run(): pass\n"}
        session, metric = runner.benchmark_on_instance(
            instance=instance,
            harness=harness,
            inference_engine=engine,
            base_files=base_files,
        )

        assert session.turns_used == 2
        assert "diff --git" in session.patch
        assert "return 42" in session.patch
        assert metric.instance_id == "harness-test-1"

    def test_budget_exhaustion(self, sample_agent_config: AgentConfig) -> None:
        """When turns exceed max_turns budget, session stops."""
        # Engine always loops reading file
        infinite_dialogue = [
            json.dumps(
                {
                    "thought": f"Turn {i}",
                    "sub_agent": "locator",
                    "tool": "read_file",
                    "arguments": {"filepath": "main.py"},
                }
            )
            for i in range(10)
        ]
        engine = MockInferenceEngine(canned_responses=infinite_dialogue)

        with SubprocessSandbox() as sandbox:
            sandbox.write_file("main.py", "content\n")
            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            orchestrator = ReActOrchestrator(runner=runner, inference_engine=engine, max_turns=3)

            instance = SWEInstance(
                instance_id="budget-test",
                repo="sample/repo",
                base_commit="hash",
                problem_statement="Budget test",
            )
            session = orchestrator.solve(instance=instance)
            assert session.turns_used == 3
            assert session.success is False

    def test_timeout_guardrail(self, sample_agent_config: AgentConfig) -> None:
        """When session exceeds timeout limit, timed_out flag is set."""
        engine = MockInferenceEngine(
            canned_responses=[
                json.dumps(
                    {
                        "thought": "Thinking slowly",
                        "sub_agent": "locator",
                        "tool": "read_file",
                        "arguments": {"filepath": "main.py"},
                    }
                )
            ]
        )
        with SubprocessSandbox() as sandbox:
            sandbox.write_file("main.py", "data\n")
            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            orchestrator = ReActOrchestrator(
                runner=runner,
                inference_engine=engine,
                timeout_seconds=0,
            )
            instance = SWEInstance(
                instance_id="timeout-test",
                repo="sample/repo",
                base_commit="hash",
                problem_statement="Timeout test",
            )
            session = orchestrator.solve(instance=instance)
            assert session.timed_out is True

    def test_unauthorized_tool_handled_as_error(self, sample_agent_config: AgentConfig) -> None:
        """When subagent tries to call a disallowed tool, turn records error."""
        dialogue = [
            # explorer is not allowed to run edit_file
            json.dumps(
                {
                    "thought": "Explorer attempting edit_file illegally",
                    "sub_agent": "explorer",
                    "tool": "edit_file",
                    "arguments": {"filepath": "main.py", "old_string": "a", "new_string": "b"},
                }
            ),
            # Then validator submits patch
            json.dumps(
                {
                    "thought": "Finish",
                    "sub_agent": "validator",
                    "tool": "submit_patch",
                    "arguments": {},
                }
            ),
        ]
        engine = MockInferenceEngine(canned_responses=dialogue)
        with SubprocessSandbox() as sandbox:
            sandbox.write_file("main.py", "a = 1\n")
            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            orchestrator = ReActOrchestrator(runner=runner, inference_engine=engine)

            instance = SWEInstance(
                instance_id="auth-test",
                repo="sample/repo",
                base_commit="hash",
                problem_statement="Test tool permissions",
            )
            session = orchestrator.solve(instance=instance)
            assert len(session.history) == 2
            assert session.history[0].is_error is True
            assert "Permission denied" in session.history[0].observation

    def test_dynamic_handler_mock_engine(self, sample_agent_config: AgentConfig) -> None:
        """MockInferenceEngine supports dynamic callable handler."""

        def dynamic_solver(prompt: str) -> str:
            if "Observation" in prompt:
                return json.dumps(
                    {
                        "thought": "Seen observation, now submitting",
                        "sub_agent": "validator",
                        "tool": "submit_patch",
                        "arguments": {},
                    }
                )
            return json.dumps(
                {
                    "thought": "Initial step",
                    "sub_agent": "locator",
                    "tool": "read_file",
                    "arguments": {"filepath": "main.py"},
                }
            )

        engine = MockInferenceEngine(dynamic_handler=dynamic_solver)
        with SubprocessSandbox() as sandbox:
            sandbox.write_file("main.py", "print('hello')\n")
            runner = DeclarativeAgentRunner(config=sample_agent_config, sandbox=sandbox)
            orchestrator = ReActOrchestrator(runner=runner, inference_engine=engine)

            instance = SWEInstance(
                instance_id="dynamic-test",
                repo="sample/repo",
                base_commit="hash",
                problem_statement="Dynamic solver test",
            )
            session = orchestrator.solve(instance=instance)
            assert session.turns_used == 2
            assert len(engine.prompts_received) == 2
