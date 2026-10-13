"""Declarative Agent Schema and Specification Parser.

Validates declarative YAML configurations, prompt templates, tool allowances,
and execution budgets for the Gemma 4 Developer Agent challenge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

import yaml

SUPPORTED_TOOLS: Set[str] = {
    "search_similar_code",
    "get_code_neighbors",
    "get_code_subgraph",
    "read_file",
    "edit_file",
    "write_file",
    "run_command",
    "get_status",
    "submit_patch",
}


class ConfigValidationError(Exception):
    """Raised when declarative agent configuration fails validation."""


@dataclass
class BudgetConfig:
    """Resource constraints and guardrails."""

    max_turns: int = 20
    timeout_seconds: int = 300
    max_tokens_per_turn: int = 4096


@dataclass
class SamplingConfig:
    """Decoding and sampling parameters."""

    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 40
    repetition_penalty: float = 1.05
    max_tokens_per_turn: int = 4096
    stop_sequences: List[str] = field(default_factory=lambda: ["<end_of_turn>", "<eos>"])


@dataclass
class SubAgentConfig:
    """Specialized sub-agent configuration."""

    name: str
    role: str
    description: str
    prompt_path: str
    prompt_content: str = ""
    max_turns: int = 5
    timeout_seconds: int = 60
    allowed_tools: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validates sub-agent parameters and tools against supported set."""
        if not self.name or not self.role:
            raise ConfigValidationError("Sub-agent must define name and role.")
        for tool in self.allowed_tools:
            if tool not in SUPPORTED_TOOLS:
                raise ConfigValidationError(
                    f"Sub-agent '{self.name}' declares unsupported tool '{tool}'. "
                    f"Supported tools: {sorted(SUPPORTED_TOOLS)}"
                )


@dataclass
class WorkflowConfig:
    """Sub-agent orchestration sequence and error fallback routing."""

    sequence: List[str] = field(
        default_factory=lambda: ["explorer", "locator", "drafter", "validator"]
    )
    fallback_on_failure: str = "locator"
    max_routing_cycles: int = 2


@dataclass
class AgentConfig:
    """Root declarative agent specification."""

    name: str
    version: str
    model: str
    description: str
    system_prompt_path: str
    system_prompt_content: str
    budget: BudgetConfig
    sampling: SamplingConfig
    sub_agents: Dict[str, SubAgentConfig]
    workflow: WorkflowConfig
    root_dir: Path = field(default_factory=Path.cwd)

    @classmethod
    def from_yaml(cls, agent_yaml_path: Path) -> AgentConfig:
        """Parses and validates an agent.yaml configuration and its referenced files.

        Args:
            agent_yaml_path: Path to the root agent.yaml file.

        Returns:
            Validated AgentConfig instance.

        Raises:
            ConfigValidationError: If syntax, paths, or constraints are violated.
        """
        agent_path = Path(agent_yaml_path).resolve()
        if not agent_path.is_file():
            raise ConfigValidationError(f"Agent config file not found: {agent_path}")

        agent_dir = agent_path.parent
        # Also check parent directory for prompts/ if not located in agent_dir
        base_search_dirs = [agent_dir, agent_dir.parent]

        try:
            with open(agent_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except Exception as exc:
            raise ConfigValidationError(f"Failed to parse YAML from {agent_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigValidationError("Root agent.yaml must define a mapping.")

        name = raw.get("name", "gemma-4-developer-agent")
        version = raw.get("version", "1.0.0")
        model = raw.get("model", "gemma-4-31b-it-qat-w4a16-ct")
        description = raw.get("description", "")
        sys_prompt_rel = raw.get("system_prompt", "prompts/system.md")

        # Resolve system prompt
        sys_prompt_file = cls._resolve_path(sys_prompt_rel, base_search_dirs)
        if not sys_prompt_file.is_file():
            raise ConfigValidationError(f"System prompt file not found: {sys_prompt_rel}")
        system_prompt_content = sys_prompt_file.read_text(encoding="utf-8")

        # Parse budget
        raw_budget = raw.get("budget", {})
        budget = BudgetConfig(
            max_turns=int(raw_budget.get("max_turns", 20)),
            timeout_seconds=int(raw_budget.get("timeout_seconds", 300)),
            max_tokens_per_turn=int(raw_budget.get("max_tokens_per_turn", 4096)),
        )

        # Parse sampling config
        sampling_rel = raw.get("sampling_config", "configs/sampling.yaml")
        sampling_file = cls._resolve_path(sampling_rel, base_search_dirs)
        if sampling_file.is_file():
            with open(sampling_file, "r", encoding="utf-8") as f:
                raw_sampling = yaml.safe_load(f) or {}
            sampling = SamplingConfig(
                temperature=float(raw_sampling.get("temperature", 0.2)),
                top_p=float(raw_sampling.get("top_p", 0.95)),
                top_k=int(raw_sampling.get("top_k", 40)),
                repetition_penalty=float(raw_sampling.get("repetition_penalty", 1.05)),
                max_tokens_per_turn=int(raw_sampling.get("max_tokens_per_turn", 4096)),
                stop_sequences=list(raw_sampling.get("stop_sequences", ["<end_of_turn>", "<eos>"])),
            )
        else:
            sampling = SamplingConfig()

        # Parse sub-agents
        raw_sub_agents = raw.get("sub_agents", {})
        sub_agents: Dict[str, SubAgentConfig] = {}

        for sa_key, sa_rel in raw_sub_agents.items():
            sa_file = cls._resolve_path(sa_rel, base_search_dirs)
            if not sa_file.is_file():
                raise ConfigValidationError(f"Sub-agent '{sa_key}' config not found: {sa_rel}")
            with open(sa_file, "r", encoding="utf-8") as f:
                sa_data = yaml.safe_load(f) or {}

            prompt_rel = sa_data.get("prompt", "")
            prompt_file = cls._resolve_path(prompt_rel, base_search_dirs)
            prompt_content = ""
            if prompt_file.is_file():
                prompt_content = prompt_file.read_text(encoding="utf-8")
            else:
                raise ConfigValidationError(f"Sub-agent '{sa_key}' prompt not found: {prompt_rel}")

            sub_agent = SubAgentConfig(
                name=sa_data.get("name", sa_key),
                role=sa_data.get("role", ""),
                description=sa_data.get("description", ""),
                prompt_path=prompt_rel,
                prompt_content=prompt_content,
                max_turns=int(sa_data.get("max_turns", 5)),
                timeout_seconds=int(sa_data.get("timeout_seconds", 60)),
                allowed_tools=list(sa_data.get("allowed_tools", [])),
            )
            sub_agent.validate()
            sub_agents[sa_key] = sub_agent

        # Parse workflow
        raw_wf = raw.get("workflow", {})
        wf_sequence = list(raw_wf.get("sequence", list(sub_agents.keys())))
        fallback = str(raw_wf.get("fallback_on_failure", "locator"))
        max_cycles = int(raw_wf.get("max_routing_cycles", 2))

        # Validate workflow references declared sub-agents
        for step in wf_sequence:
            if step not in sub_agents:
                raise ConfigValidationError(
                    f"Workflow sequence step '{step}' is not declared in sub_agents."
                )
        if fallback not in sub_agents:
            raise ConfigValidationError(
                f"Workflow fallback_on_failure '{fallback}' is not declared in sub_agents."
            )

        workflow = WorkflowConfig(
            sequence=wf_sequence,
            fallback_on_failure=fallback,
            max_routing_cycles=max_cycles,
        )

        return cls(
            name=name,
            version=version,
            model=model,
            description=description,
            system_prompt_path=sys_prompt_rel,
            system_prompt_content=system_prompt_content,
            budget=budget,
            sampling=sampling,
            sub_agents=sub_agents,
            workflow=workflow,
            root_dir=agent_dir,
        )

    @staticmethod
    def _resolve_path(rel_path: str, candidates: List[Path]) -> Path:
        """Finds the first existing candidate for a relative path."""
        for base in candidates:
            resolved = (base / rel_path).resolve()
            if resolved.exists():
                return resolved
        # Return first resolved path even if not existing for clean error reporting
        return (candidates[0] / rel_path).resolve()
