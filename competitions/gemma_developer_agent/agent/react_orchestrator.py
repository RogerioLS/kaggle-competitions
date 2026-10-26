"""Autonomous ReAct Orchestrator & Multi-Turn Reasoning Loop.

Drives autonomous SWE-bench bug resolution by querying Gemma 4, parsing structured
JSON tool calls, enforcing sub-agent authorization, executing operations inside
the isolated sandbox, and feeding observations back into the conversation until
the patch is verified and submitted.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from competitions.gemma_developer_agent.agent.inference_engine import (
    MODEL_ROLE,
    USER_ROLE,
    ChatMessage,
    GemmaPromptFormatter,
    InferenceEngine,
)
from competitions.gemma_developer_agent.agent.runner import (
    AgentSessionResult,
    DeclarativeAgentRunner,
    TurnRecord,
)
from competitions.gemma_developer_agent.evaluation.dataset_loader import (
    SWEInstance,
)

logger = logging.getLogger(__name__)


class ReActParseError(Exception):
    """Raised when model output cannot be parsed into a valid ReActAction."""


@dataclass
class ReActAction:
    """Represents a structured action emitted by the reasoning model."""

    thought: str
    sub_agent: str
    tool: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    raw_json: Optional[str] = None
    is_final: bool = False


class ReActParser:
    """Robust parser for extracting structured thoughts and tool actions from LLM output."""

    JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
    RAW_JSON_PATTERN = re.compile(r"(\{[\s\S]*\})", re.DOTALL)

    DEFAULT_TOOL_SUBAGENT_MAP: Dict[str, str] = {
        "search_similar_code": "explorer",
        "get_code_neighbors": "explorer",
        "get_code_subgraph": "explorer",
        "read_file": "locator",
        "edit_file": "drafter",
        "write_file": "drafter",
        "run_command": "validator",
        "get_status": "validator",
        "submit_patch": "validator",
    }

    @staticmethod
    def _unescape_json_fragment(val: str) -> str:
        """Unescapes common JSON string escape sequences in regex-extracted values."""
        return (
            val.replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\\t", "\t")
            .replace("\\\\", "\\")
        )

    @classmethod
    def _fallback_regex_extract(cls, candidate: str) -> Optional[Dict[str, Any]]:
        """Extracts ReAct fields via key boundaries when unescaped quotes break json.loads."""
        tool_m = re.search(r'"(?:tool|action)"\s*:\s*"([^"]+)"', candidate)
        if not tool_m:
            return None
        tool = tool_m.group(1).strip()

        sa_m = re.search(r'"sub_agent"\s*:\s*"([^"]+)"', candidate)
        sub_agent = (
            sa_m.group(1).strip() if sa_m else cls.DEFAULT_TOOL_SUBAGENT_MAP.get(tool, "locator")
        )

        thought_m = re.search(
            r'"thought"\s*:\s*"(.*?)"\s*,\s*"(?:sub_agent|tool|action|arguments)"',
            candidate,
            re.DOTALL,
        )
        thought = cls._unescape_json_fragment(thought_m.group(1).strip()) if thought_m else ""

        args: Dict[str, Any] = {}
        fp_m = re.search(r'"(?:filepath|path|file)"\s*:\s*"([^"]+)"', candidate)
        if fp_m:
            args["filepath"] = fp_m.group(1).strip()

        if tool == "edit_file":
            edit_m = re.search(
                r'"(?:old_string|old_str|target)"\s*:\s*"(.*?)"\s*,\s*'
                r'"(?:new_string|new_str|replacement)"\s*:\s*"(.*?)"\s*'
                r'(?:,\s*"allow_multiple"\s*:\s*(true|false))?\s*\}',
                candidate,
                re.DOTALL,
            )
            if edit_m:
                args["old_string"] = cls._unescape_json_fragment(edit_m.group(1))
                args["new_string"] = cls._unescape_json_fragment(edit_m.group(2))
                if edit_m.group(3):
                    args["allow_multiple"] = edit_m.group(3).lower() == "true"
        elif tool == "read_file":
            s_m = re.search(r'"start_line"\s*:\s*(\d+)', candidate)
            e_m = re.search(r'"end_line"\s*:\s*(\d+)', candidate)
            if s_m:
                args["start_line"] = int(s_m.group(1))
            if e_m:
                args["end_line"] = int(e_m.group(1))
        elif tool == "run_command":
            cmd_m = re.search(r'"(?:command|cmd)"\s*:\s*"(.*?)"\s*\}', candidate, re.DOTALL)
            if cmd_m:
                args["command"] = cls._unescape_json_fragment(cmd_m.group(1))
        elif tool == "write_file":
            content_m = re.search(r'"content"\s*:\s*"(.*?)"\s*\}', candidate, re.DOTALL)
            if content_m:
                args["content"] = cls._unescape_json_fragment(content_m.group(1))
        elif tool == "search_similar_code":
            q_m = re.search(
                r'"(?:query|search_query|text)"\s*:\s*"(.*?)"\s*(?:,\s*"k"\s*:\s*(\d+))?\s*\}',
                candidate,
                re.DOTALL,
            )
            if q_m:
                args["query"] = cls._unescape_json_fragment(q_m.group(1))
                if q_m.group(2):
                    args["k"] = int(q_m.group(2))

        return {
            "thought": thought,
            "sub_agent": sub_agent,
            "tool": tool,
            "arguments": args,
        }

    @classmethod
    def _load_json_resilient(cls, candidate: str) -> Any:
        """Parses candidate JSON, repairing unescaped inner quotes, raw newlines, and commas."""
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        cleaned = re.sub(r",\s*([\]}])", r"\1", candidate)
        current = cleaned
        last_exc: Optional[json.JSONDecodeError] = None

        for _ in range(40):
            try:
                return json.loads(current)
            except json.JSONDecodeError as exc:
                last_exc = exc
                pos = exc.pos
                if "Invalid control character" in exc.msg and 0 <= pos < len(current):
                    ch = current[pos]
                    rep = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}.get(ch, " ")
                    next_pos = pos + 1
                    current = current[:pos] + rep + current[next_pos:]
                    continue
                if exc.msg.startswith("Expecting ',' delimiter") or exc.msg.startswith(
                    "Expecting ':' delimiter"
                ):
                    q_idx = current.rfind('"', 0, pos)
                    if q_idx > 0 and current[q_idx - 1] != "\\":
                        next_q = q_idx + 1
                        current = current[:q_idx] + '\\"' + current[next_q:]
                        continue
                break

        fallback = cls._fallback_regex_extract(cleaned)
        if fallback is not None:
            return fallback

        raise ReActParseError(f"Malformed JSON in action block: {last_exc}") from last_exc

    @classmethod
    def parse(cls, model_output: str) -> ReActAction:
        """Parses model generation into a ReActAction object.

        Args:
            model_output: Raw string produced by the inference engine.

        Returns:
            ReActAction with thought, sub_agent, tool name, and arguments.

        Raises:
            ReActParseError: If no valid JSON action block can be extracted.
        """
        text = model_output.strip()

        # Try extracting fenced JSON block first
        match = cls.JSON_BLOCK_PATTERN.search(text)
        candidate = match.group(1).strip() if match else None

        # Fallback to searching for the outermost bracketed JSON structure
        if not candidate:
            match = cls.RAW_JSON_PATTERN.search(text)
            candidate = match.group(1).strip() if match else None

        if not candidate:
            raise ReActParseError(
                "No JSON action block found in model output. "
                "Ensure your response includes a ```json {...} ``` block."
            )

        data = cls._load_json_resilient(candidate)

        if not isinstance(data, dict):
            raise ReActParseError(f"Action block must be a JSON object, got {type(data).__name__}.")

        thought = str(data.get("thought", "")).strip()

        # Handle nested action structure: {"action": {"tool": "...", "arguments": {...}}}
        if "action" in data and isinstance(data["action"], dict):
            action_dict = data["action"]
            tool = str(action_dict.get("tool", action_dict.get("name", ""))).strip()
            args = action_dict.get("arguments", action_dict.get("parameters", {}))
        else:
            tool = str(data.get("tool", data.get("action", ""))).strip()
            args = data.get("arguments", data.get("parameters", {}))

        if not tool:
            raise ReActParseError("Missing required field 'tool' in action block.")

        if not isinstance(args, dict):
            args = {}

        sub_agent = str(data.get("sub_agent", "")).strip()
        if not sub_agent:
            # Heuristic default based on tool if model omitted sub_agent
            sub_agent = cls.DEFAULT_TOOL_SUBAGENT_MAP.get(tool, "locator")

        is_final = tool == "submit_patch" or bool(data.get("is_final", False))

        return ReActAction(
            thought=thought,
            sub_agent=sub_agent,
            tool=tool,
            arguments=args,
            raw_json=candidate,
            is_final=is_final,
        )


class ReActOrchestrator:
    """Manages the closed-loop autonomous reasoning and tool execution loop."""

    def __init__(
        self,
        runner: DeclarativeAgentRunner,
        inference_engine: InferenceEngine,
        max_turns: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        """Initializes the orchestrator.

        Args:
            runner: DeclarativeAgentRunner handling tool invocation and sandbox access.
            inference_engine: InferenceEngine backend for Gemma 4 completions.
            max_turns: Optional override for max conversation turns.
            timeout_seconds: Optional override for session timeout.
        """
        self.runner = runner
        self.inference_engine = inference_engine
        self.max_turns = max_turns if max_turns is not None else runner.config.budget.max_turns
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else runner.config.budget.timeout_seconds
        )
        self.parser = ReActParser()

    def _build_tool_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Constructs tool catalog and parameter specs from agent config and runner."""
        return {
            "search_similar_code": {
                "description": "Searches codebase vectors for semantically relevant code snippets.",
                "parameters": {
                    "query": "Search query string",
                    "k": "Max results count (default 10)",
                },
            },
            "get_code_neighbors": {
                "description": "Finds connected AST neighbor nodes in the structural code graph.",
                "parameters": {
                    "node": "Node name",
                    "edge_type": "Optional edge filter",
                    "max_neighbors": 50,
                },
            },
            "get_code_subgraph": {
                "description": "Extracts subgraph topology for a list of node identifiers.",
                "parameters": {"nodes": "List of node strings"},
            },
            "read_file": {
                "description": "Reads file contents in the repository (supports line range).",
                "parameters": {
                    "filepath": "Relative file path",
                    "start_line": "1-based start",
                    "end_line": "1-based end",
                },
            },
            "edit_file": {
                "description": "Surgically replaces old_string with new_string in the target file.",
                "parameters": {
                    "filepath": "Relative file path",
                    "old_string": "Exact target content",
                    "new_string": "Replacement content",
                    "allow_multiple": "Optional bool (default false)",
                },
            },
            "write_file": {
                "description": "Writes or overwrites a workspace file (e.g. reproducer script).",
                "parameters": {"filepath": "Relative file path", "content": "File string content"},
            },
            "run_command": {
                "description": "Executes shell commands in the repository sandbox.",
                "parameters": {"command": "Command string to execute"},
            },
            "get_status": {
                "description": "Queries workspace git status and remaining budget metrics.",
                "parameters": {},
            },
            "submit_patch": {
                "description": "Finalizes the resolution session and returns the git diff patch.",
                "parameters": {},
            },
        }

    def _build_initial_user_prompt(self, instance: SWEInstance) -> str:
        """Constructs initial problem statement prompt."""
        return (
            f"### SWE-bench Problem Resolution Request\n"
            f"Repository: {instance.repo}\n"
            f"Instance ID: {instance.instance_id}\n\n"
            f"#### Problem Statement:\n"
            f"{instance.problem_statement}\n\n"
            f"#### Instructions:\n"
            f"1. Explore and localize the bug using `read_file` or `search_similar_code`.\n"
            f"2. Edit the codebase surgically using `edit_file` to fix the root cause.\n"
            f"3. Optionally verify with `run_command` (`pytest`) and clean up any temp files.\n"
            f"4. Call `submit_patch` immediately once the fix is applied to seal the final patch.\n"
            f"5. CRITICAL: Respond ONLY with a valid ```json ... ``` tool call block. Do not chat."
        )

    def solve(
        self,
        instance: SWEInstance,
        base_files: Optional[Dict[str, str]] = None,
    ) -> AgentSessionResult:
        """Runs the autonomous closed-loop ReAct cycle to resolve a SWEInstance.

        Args:
            instance: SWEInstance containing repository context and issue description.
            base_files: Optional dictionary mapping relative paths to file contents.

        Returns:
            AgentSessionResult with recorded turns, git diff patch, and outcome metrics.
        """
        start_time = time.perf_counter()
        session = AgentSessionResult(instance_id=instance.instance_id)

        # Populate base files in sandbox if provided
        if base_files and self.runner.sandbox:
            for rel_path, content in base_files.items():
                self.runner.sandbox.write_file(rel_path, content)
            self.runner.sandbox.commit_all("baseline")

        tool_catalog = self._build_tool_catalog()
        tool_declarations = GemmaPromptFormatter.render_tool_declarations(tool_catalog)

        system_prompt = (
            self.runner.config.system_prompt_content or "You are an expert autonomous SWE agent."
        )
        initial_user_msg = self._build_initial_user_prompt(instance)

        messages: List[ChatMessage] = [ChatMessage(role=USER_ROLE, content=initial_user_msg)]

        logger.info(
            "Starting ReAct loop for instance %s (max_turns=%d)...",
            instance.instance_id,
            self.max_turns,
        )

        for turn_idx in range(1, self.max_turns + 1):
            elapsed = time.perf_counter() - start_time
            if elapsed >= self.timeout_seconds:
                logger.warning("Session timed out after %.2fs at turn %d.", elapsed, turn_idx)
                session.timed_out = True
                break

            prompt = GemmaPromptFormatter.format_conversation(
                messages=messages,
                system_prompt=system_prompt,
                tool_declarations=tool_declarations,
                add_generation_prompt=True,
            )

            # Generate model completion
            try:
                raw_completion = self.inference_engine.generate(
                    prompt=prompt,
                    max_tokens=self.runner.config.sampling.max_tokens_per_turn,
                    temperature=self.runner.config.sampling.temperature,
                    top_p=self.runner.config.sampling.top_p,
                    stop_sequences=self.runner.config.sampling.stop_sequences,
                )
            except Exception as exc:
                logger.error("Inference failure on turn %d: %s", turn_idx, exc)
                session.error_message = f"Inference engine failure: {exc}"
                break

            messages.append(ChatMessage(role=MODEL_ROLE, content=raw_completion))

            # Parse action
            try:
                action = self.parser.parse(raw_completion)
            except ReActParseError as parse_err:
                logger.warning("Action parse error on turn %d: %s", turn_idx, parse_err)
                messages[-1] = ChatMessage(
                    role=MODEL_ROLE, content="[Invalid JSON tool call omitted]"
                )
                observation = (
                    f"ActionParseError: {parse_err}\n"
                    'IMPORTANT: Do NOT use unescaped double quotes (") inside JSON strings '
                    "(use single quotes '...' inside thought/code, or escape as \\\"). "
                    "Provide a valid JSON action block specifying thought, "
                    "sub_agent, tool, and arguments."
                )
                session.history.append(
                    TurnRecord(
                        turn_index=turn_idx,
                        sub_agent=session.active_sub_agent or "locator",
                        duration_seconds=round(time.perf_counter() - start_time, 3),
                        observation=observation,
                        is_error=True,
                    )
                )
                messages.append(ChatMessage(role=USER_ROLE, content=f"Observation:\n{observation}"))
                continue

            # Execute tool action
            turn_record = self.runner.execute_turn(
                sub_agent_name=action.sub_agent,
                tool_name=action.tool,
                arguments=action.arguments,
                session=session,
                start_time=start_time,
            )

            # Check if patch was submitted
            if action.tool == "submit_patch" and not turn_record.is_error:
                session.patch = turn_record.observation
                session.success = bool(session.patch.strip())
                logger.info("Agent submitted patch at turn %d.", turn_idx)
                break

            if session.budget_exhausted or session.timed_out:
                break

            # Feed observation back as next user turn
            obs_feedback = (
                f"Observation ({action.tool}):\n{turn_record.observation}"
                if not turn_record.is_error
                else f"Error ({action.tool}):\n{turn_record.observation}"
            )
            if action.tool == "edit_file" and not turn_record.is_error:
                obs_feedback += (
                    "\n\n[Next Step: The edit was applied cleanly. Call `submit_patch` "
                    "in a ```json ... ``` block to finalize the patch.]"
                )
            elif turn_idx >= self.max_turns - 2:
                obs_feedback += (
                    f"\n\n[URGENT: Only {self.max_turns - turn_idx} turn(s) remaining! "
                    "Apply `edit_file` or call `submit_patch` immediately.]"
                )
            messages.append(ChatMessage(role=USER_ROLE, content=obs_feedback))

        # Capture final git diff if submit_patch was not explicitly called or returned empty
        if not session.patch and self.runner.sandbox:
            session.patch = self.runner.sandbox.get_diff()
            session.success = bool(session.patch.strip())

        session.duration_seconds = round(time.perf_counter() - start_time, 3)
        return session
