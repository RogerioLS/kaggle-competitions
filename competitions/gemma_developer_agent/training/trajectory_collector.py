"""Trajectory collection and dataset formatting pipeline for Gemma 4 SFT.

Extracts multi-turn conversational trajectories from successful SWE-bench resolution runs
and formats them into Gemma 4 chat template turns:
<start_of_turn>user\n...<end_of_turn>\n<start_of_turn>model\n...<end_of_turn>\n
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from competitions.gemma_developer_agent.agent.runner import (  # noqa: E402
    AgentSessionResult,
)
from competitions.gemma_developer_agent.evaluation.dataset_loader import (  # noqa: E402
    SWEInstance,
)
from competitions.gemma_developer_agent.evaluation.harness import (  # noqa: E402
    InstanceMetric,
)


@dataclass
class ChatTurn:
    """Represents a single conversational turn in a fine-tuning trajectory."""

    role: str
    content: str

    def to_gemma_format(self) -> str:
        """Formats turn into official Gemma 4 special token string."""
        return f"<start_of_turn>{self.role}\n{self.content.strip()}<end_of_turn>\n"


@dataclass
class Trajectory:
    """Represents a full multi-turn problem-solving episode."""

    instance_id: str
    repo: str
    turns: List[ChatTurn] = field(default_factory=list)
    resolved: bool = True
    patch: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_gemma_chat(self) -> str:
        """Serializes entire episode into a single Gemma 4 formatted chat string."""
        return "".join(turn.to_gemma_format() for turn in self.turns)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes trajectory into dictionary format for JSONL export."""
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "resolved": self.resolved,
            "patch": self.patch,
            "turns": [asdict(t) for t in self.turns],
            "text": self.to_gemma_chat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Trajectory:
        """Reconstructs Trajectory from dictionary."""
        turns = [ChatTurn(role=t["role"], content=t["content"]) for t in data.get("turns", [])]
        return cls(
            instance_id=data.get("instance_id", ""),
            repo=data.get("repo", ""),
            turns=turns,
            resolved=data.get("resolved", False),
            patch=data.get("patch", ""),
            metadata=data.get("metadata", {}),
        )


class TrajectoryCollector:
    """Collects and formats agent execution sessions into high-quality SFT trajectories."""

    @staticmethod
    def format_initial_prompt(instance: SWEInstance) -> str:
        """Constructs initial user instruction with problem statement and repository context."""
        parts = [
            (
                f"You are working on the repository '{instance.repo}' "
                f"at commit '{instance.base_commit}'."
            ),
            "Please investigate and resolve the following issue:",
            "",
            "## Problem Statement",
            instance.problem_statement.strip(),
        ]
        if instance.hints_text:
            parts.extend(["", "## Hints & Context", instance.hints_text.strip()])
        parts.extend(
            [
                "",
                "Analyze the problem, inspect the codebase using AST graph and file tools,",
                "reproduce the issue, draft a surgical patch, and submit it.",
            ]
        )
        return "\n".join(parts)

    def collect_from_session(
        self,
        session: AgentSessionResult,
        instance: SWEInstance,
        resolved: bool = True,
    ) -> Optional[Trajectory]:
        """Converts an AgentSessionResult into a structured multi-turn Trajectory.

        Args:
            session: AgentSessionResult containing turn history.
            instance: Target SWEInstance task definition.
            resolved: Whether the patch actually passed verification.

        Returns:
            Trajectory object if session was valid, None otherwise.
        """
        if not session.success and resolved:
            return None

        turns: List[ChatTurn] = []

        # 1. Initial user request
        initial_user_msg = self.format_initial_prompt(instance)
        turns.append(ChatTurn(role="user", content=initial_user_msg))

        # 2. Iterate over execution history
        for turn_record in session.history:
            if not turn_record.tool_call:
                continue

            sub_agent = turn_record.sub_agent
            tool_name = turn_record.tool_call.tool_name
            tool_args = turn_record.tool_call.arguments

            # Model action turn
            model_thought = (
                f"[{sub_agent.upper()}] Investigating issue and invoking tool '{tool_name}'."
            )
            model_payload = json.dumps({"tool": tool_name, "arguments": tool_args}, indent=2)
            model_content = f"{model_thought}\n```json\n{model_payload}\n```"
            turns.append(ChatTurn(role="model", content=model_content))

            # Tool observation returned to agent
            obs_content = f"Observation from {tool_name}:\n{turn_record.observation}"
            turns.append(ChatTurn(role="user", content=obs_content))

        # 3. Final model confirmation if patch was created
        if session.patch:
            final_model = (
                f"[VALIDATOR] Patch generated and verified successfully.\n"
                f"Unified Diff:\n```diff\n{session.patch.strip()}\n```"
            )
            turns.append(ChatTurn(role="model", content=final_model))

        return Trajectory(
            instance_id=instance.instance_id,
            repo=instance.repo,
            turns=turns,
            resolved=resolved,
            patch=session.patch,
            metadata={
                "turns_used": session.turns_used,
                "duration_seconds": session.duration_seconds,
            },
        )

    def collect_from_benchmarks(
        self,
        results: List[Tuple[AgentSessionResult, InstanceMetric, SWEInstance]],
        filter_resolved_only: bool = True,
    ) -> List[Trajectory]:
        """Batches and extracts trajectories from a list of benchmark evaluation tuples."""
        trajectories: List[Trajectory] = []
        for session, metric, instance in results:
            if filter_resolved_only and not metric.resolved:
                continue
            traj = self.collect_from_session(
                session=session, instance=instance, resolved=metric.resolved
            )
            if traj:
                trajectories.append(traj)
        return trajectories

    @staticmethod
    def save_to_jsonl(trajectories: List[Trajectory], output_path: Path) -> Path:
        """Serializes list of trajectories to JSONL format."""
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for traj in trajectories:
                f.write(json.dumps(traj.to_dict()) + "\n")
        return out

    @staticmethod
    def load_from_jsonl(path: Path) -> List[Trajectory]:
        """Reads trajectories from a JSONL file."""
        target = Path(path).resolve()
        if not target.is_file():
            raise FileNotFoundError(f"Trajectory file not found: {target}")

        trajectories: List[Trajectory] = []
        with open(target, "r", encoding="utf-8") as f:
            for line in f:
                clean = line.strip()
                if clean:
                    trajectories.append(Trajectory.from_dict(json.loads(clean)))
        return trajectories

    @staticmethod
    def _extract_hunks_from_patch(patch_str: str) -> List[Dict[str, Any]]:
        """Parses unified diff patch into structured file replacement hunks."""
        results: List[Dict[str, Any]] = []
        current_file: Optional[str] = None
        lines = patch_str.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("--- a/"):
                current_file = line[6:].strip()
                i += 1
                continue
            elif line.startswith("+++ b/") and current_file is None:
                current_file = line[6:].strip()
                i += 1
                continue
            elif line.startswith("@@"):
                m = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if m:
                    old_start = int(m.group(1))
                    old_len = int(m.group(2)) if m.group(2) else 1
                    hunk_lines = []
                    i += 1
                    while i < len(lines) and not (
                        lines[i].startswith("--- a/") or lines[i].startswith("@@")
                    ):
                        hunk_lines.append(lines[i])
                        i += 1

                    old_lines = [
                        hl[1:] for hl in hunk_lines if hl.startswith(" ") or hl.startswith("-")
                    ]
                    new_lines = [
                        hl[1:] for hl in hunk_lines if hl.startswith(" ") or hl.startswith("+")
                    ]

                    results.append(
                        {
                            "file": current_file or "unknown.py",
                            "old_start": old_start,
                            "is_new_file": (old_start == 0 and old_len == 0),
                            "old_string": "\n".join(old_lines),
                            "new_string": "\n".join(new_lines),
                        }
                    )
                    continue
            i += 1
        return results

    @classmethod
    def collect_from_tasks_jsonl(cls, tasks_path: Path) -> List[Trajectory]:
        """Extracts ground-truth SFT trajectories directly from SWE-bench tasks.jsonl."""
        collector = cls()
        path = Path(tasks_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"tasks.jsonl not found at {path}")

        trajectories: List[Trajectory] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                task = json.loads(raw)
                instance = SWEInstance(
                    instance_id=task.get("instance_id", ""),
                    repo=task.get("repo", ""),
                    base_commit=task.get("base_commit", ""),
                    problem_statement=task.get("problem_statement", ""),
                    hints_text=task.get("hints_text", ""),
                )
                patch = task.get("patch", "")
                hunks = collector._extract_hunks_from_patch(patch)
                if not hunks:
                    continue

                turns: List[ChatTurn] = []
                # 1. Initial user request
                turns.append(
                    ChatTurn(role="user", content=collector.format_initial_prompt(instance))
                )

                # 2. Explorer reads target file around bug
                first_hunk = hunks[0]
                read_start = max(1, first_hunk["old_start"] - 5)
                read_end = first_hunk["old_start"] + 35
                model_read_payload = json.dumps(
                    {
                        "tool": "read_file",
                        "arguments": {
                            "filepath": first_hunk["file"],
                            "start_line": read_start,
                            "end_line": read_end,
                        },
                    },
                    indent=2,
                )
                turns.append(
                    ChatTurn(
                        role="model",
                        content=(
                            f"[EXPLORER] Inspecting target file '{first_hunk['file']}'.\n"
                            f"```json\n{model_read_payload}\n```"
                        ),
                    )
                )
                turns.append(
                    ChatTurn(
                        role="user",
                        content=f"Observation from read_file:\n{first_hunk['old_string']}\n",
                    )
                )

                # 3. Drafter applies surgical edit
                for hunk in hunks:
                    if hunk["is_new_file"]:
                        tool_name = "write_file"
                        args = {"filepath": hunk["file"], "content": hunk["new_string"]}
                    else:
                        tool_name = "edit_file"
                        args = {
                            "filepath": hunk["file"],
                            "old_string": hunk["old_string"],
                            "new_string": hunk["new_string"],
                        }

                    model_edit_payload = json.dumps(
                        {"tool": tool_name, "arguments": args}, indent=2
                    )
                    turns.append(
                        ChatTurn(
                            role="model",
                            content=(
                                f"[DRAFTER] Applying surgical fix in '{hunk['file']}'.\n"
                                f"```json\n{model_edit_payload}\n```"
                            ),
                        )
                    )
                    turns.append(
                        ChatTurn(
                            role="user",
                            content=(
                                f"Observation from {tool_name}:\n"
                                f"File {hunk['file']} modified successfully."
                            ),
                        )
                    )

                # 4. Validator seals patch
                model_submit_payload = json.dumps(
                    {"tool": "submit_patch", "arguments": {}}, indent=2
                )
                turns.append(
                    ChatTurn(
                        role="model",
                        content=(
                            "[VALIDATOR] Staging final verified patch.\n"
                            f"```json\n{model_submit_payload}\n```"
                        ),
                    )
                )
                turns.append(
                    ChatTurn(
                        role="user",
                        content="Observation from submit_patch:\nPatch staged successfully.",
                    )
                )

                trajectories.append(
                    Trajectory(
                        instance_id=instance.instance_id,
                        repo=instance.repo,
                        turns=turns,
                        resolved=True,
                        patch=patch,
                        metadata={
                            "files_changed": len(set(h["file"] for h in hunks)),
                            "hunks_count": len(hunks),
                        },
                    )
                )

        return trajectories

    @classmethod
    def create_synthetic_trajectories(cls, count: int = 3) -> List[Trajectory]:
        """Generates realistic synthetic trajectories for offline bootstrapping and testing."""
        collector = cls()
        trajectories: List[Trajectory] = []

        for idx in range(1, count + 1):
            inst = SWEInstance(
                instance_id=f"synth_task_{idx:03d}",
                repo=f"organization/project_{idx}",
                base_commit=f"commit_{idx:08d}",
                problem_statement=f"Bug report {idx}: unexpected ValueError on empty payload.",
                hints_text="Ensure return None if payload is empty.",
            )
            turns = [
                ChatTurn(role="user", content=collector.format_initial_prompt(inst)),
                ChatTurn(
                    role="model",
                    content=(
                        "[EXPLORER] Locating entrypoint.\n```json\n"
                        '{"tool": "read_file", "arguments": {"filepath": "core/api.py"}}\n```'
                    ),
                ),
                ChatTurn(
                    role="user",
                    content="Observation from read_file:\ndef parse(data):\n    return data[0]\n",
                ),
                ChatTurn(
                    role="model",
                    content=(
                        "[DRAFTER] Applying safety check.\n```json\n"
                        '{"tool": "edit_file", "arguments": {"filepath": "core/api.py", '
                        '"old_string": "    return data[0]", '
                        '"new_string": "    return data[0] if data else None"}}\n```'
                    ),
                ),
                ChatTurn(
                    role="user",
                    content="Observation from edit_file:\nFile core/api.py modified successfully.",
                ),
                ChatTurn(
                    role="model",
                    content=(
                        "[VALIDATOR] Staging patch.\n```json\n"
                        '{"tool": "submit_patch", "arguments": {}}\n```'
                    ),
                ),
                ChatTurn(
                    role="user",
                    content="Observation from submit_patch:\nPatch staged successfully.",
                ),
            ]
            diff_patch = (
                "diff --git a/core/api.py b/core/api.py\n"
                "--- a/core/api.py\n"
                "+++ b/core/api.py\n"
                "@@ -1,2 +1,2 @@\n"
                " def parse(data):\n"
                "-    return data[0]\n"
                "+    return data[0] if data else None\n"
            )
            trajectories.append(
                Trajectory(
                    instance_id=inst.instance_id,
                    repo=inst.repo,
                    turns=turns,
                    resolved=True,
                    patch=diff_patch,
                    metadata={"turns_used": 3, "duration_seconds": 1.25},
                )
            )

        return trajectories


def main() -> int:
    """CLI entrypoint for collecting and inspecting SFT trajectories."""
    parser = argparse.ArgumentParser(
        description="Extract and format SFT training trajectories for Gemma 4."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="artifacts/trajectories.jsonl",
        help="Target output JSONL path (default: artifacts/trajectories.jsonl)",
    )
    parser.add_argument(
        "--generate-synthetic",
        type=int,
        default=0,
        help="Generate N synthetic trajectories for bootstrapping.",
    )
    parser.add_argument(
        "--from-tasks",
        type=str,
        default=None,
        help="Extract ground-truth SFT trajectories from tasks.jsonl path",
    )

    args = parser.parse_args()
    out_path = Path(args.output)

    if args.from_tasks:
        tasks_path = Path(args.from_tasks)
        trajectories = TrajectoryCollector.collect_from_tasks_jsonl(tasks_path)
        TrajectoryCollector.save_to_jsonl(trajectories, out_path)
        print(f"✔ Extracted {len(trajectories)} golden trajectories -> {out_path}")
        return 0

    if args.generate_synthetic > 0:
        trajectories = TrajectoryCollector.create_synthetic_trajectories(
            count=args.generate_synthetic
        )
        TrajectoryCollector.save_to_jsonl(trajectories, out_path)
        print(f"✔ Generated {len(trajectories)} synthetic trajectories -> {out_path}")
        return 0

    print("ℹ️ Specify --generate-synthetic N or invoke via python API from harness benchmarks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
