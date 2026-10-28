"""Declarative Agent Schema and Specification Parser.

Validates declarative YAML configurations, prompt templates, tool allowances,
and execution budgets for the Gemma 4 Developer Agent challenge.
Supports both the official Google ADK `adk-submission` (`SandboxedAgentConfig`)
schema (with `!include` tags, `instruction`, `tools`, `agent_tool`,
`generate_content_config`, and `eval_config.yaml`) and legacy test schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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

ALLOWED_MODEL_NAMES: Set[str] = {
    "gemma-4-31b-it-qat-w4a16-ct",
    "gemma-4-12b-it-qat-w4a16-ct",
    "gemma-4-e4b-it-qat-w4a16-ct",
    "gemma-4-e2b-it-qat-w4a16-ct",
}

DEFAULT_SUBAGENT_BUDGETS: Dict[str, Dict[str, int]] = {
    "explorer": {"max_turns": 4, "timeout_seconds": 90},
    "locator": {"max_turns": 6, "timeout_seconds": 120},
    "drafter": {"max_turns": 8, "timeout_seconds": 180},
    "validator": {"max_turns": 6, "timeout_seconds": 180},
}


class ConfigValidationError(Exception):
    """Raised when declarative agent configuration fails validation."""


class IncludeRef(str):
    """String subclass representing a YAML `!include <path>` tag."""


class SandboxedYamlLoader(yaml.SafeLoader):
    """YAML SafeLoader that supports the `!include` directive used by `adk-submission`."""


def _include_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> IncludeRef:
    value = loader.construct_scalar(node)  # type: ignore[arg-type]
    return IncludeRef(str(value).strip())


SandboxedYamlLoader.add_constructor("!include", _include_constructor)


def safe_load_yaml_with_includes(content: str) -> Any:
    """Parses YAML content while preserving `!include` directives as `IncludeRef`."""
    return yaml.load(content, Loader=SandboxedYamlLoader)  # nosec B506


@dataclass
class BudgetConfig:
    """Resource constraints and guardrails."""

    max_turns: int = 30
    timeout_seconds: int = 120
    max_tokens_per_turn: int = 4096
    max_tool_calls: int = 25
    max_time_minutes: int = 5


@dataclass
class SamplingConfig:
    """Decoding and sampling parameters aligned with ADK `GenerateContentConfig`."""

    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 40
    repetition_penalty: float = 1.05
    max_tokens_per_turn: int = 4096
    max_output_tokens: int = 16384
    thinking_config: Optional[Dict[str, Any]] = None
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
    model: str = "gemma-4-31b-it-qat-w4a16-ct"

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
    tools: List[str] = field(default_factory=list)
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
        base_search_dirs = [agent_dir, agent_dir.parent]

        try:
            raw_text = agent_path.read_text(encoding="utf-8")
            raw = safe_load_yaml_with_includes(raw_text)
        except Exception as exc:
            raise ConfigValidationError(f"Failed to parse YAML from {agent_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigValidationError("Root agent.yaml must define a mapping.")

        name = raw.get("name", "gemma_4_developer_agent")
        version = raw.get("version", "1.0.0")
        model = raw.get("model", "gemma-4-31b-it-qat-w4a16-ct")
        description = raw.get("description", "")

        # Resolve instruction (!include prompts/system.md) or legacy system_prompt
        if "instruction" in raw:
            instr_val = raw["instruction"]
            if isinstance(instr_val, IncludeRef) or str(instr_val).endswith((".md", ".txt")):
                sys_prompt_rel = str(instr_val)
                sys_prompt_file = cls._resolve_path(sys_prompt_rel, base_search_dirs)
                if not sys_prompt_file.is_file():
                    raise ConfigValidationError(f"System prompt file not found: {sys_prompt_rel}")
                system_prompt_content = sys_prompt_file.read_text(encoding="utf-8")
            else:
                sys_prompt_rel = "inline"
                system_prompt_content = str(instr_val)
        else:
            sys_prompt_rel = raw.get("system_prompt", "prompts/system.md")
            sys_prompt_file = cls._resolve_path(sys_prompt_rel, base_search_dirs)
            if not sys_prompt_file.is_file():
                raise ConfigValidationError(f"System prompt file not found: {sys_prompt_rel}")
            system_prompt_content = sys_prompt_file.read_text(encoding="utf-8")

        # Parse budget from legacy `budget:` or official `eval_config.yaml`
        raw_budget = raw.get("budget")
        if isinstance(raw_budget, dict):
            budget = BudgetConfig(
                max_turns=int(raw_budget.get("max_turns", 20)),
                timeout_seconds=int(raw_budget.get("timeout_seconds", 300)),
                max_tokens_per_turn=int(raw_budget.get("max_tokens_per_turn", 4096)),
            )
        else:
            eval_cfg_file = cls._resolve_path("eval_config.yaml", base_search_dirs)
            eval_section: Dict[str, Any] = {}
            if eval_cfg_file.is_file():
                raw_eval = safe_load_yaml_with_includes(eval_cfg_file.read_text(encoding="utf-8"))
                if isinstance(raw_eval, dict) and isinstance(raw_eval.get("evaluation"), dict):
                    eval_section = raw_eval["evaluation"]
            budget = BudgetConfig(
                max_turns=int(eval_section.get("max_turns", 20)),
                timeout_seconds=int(eval_section.get("timeout_seconds", 300)),
                max_tokens_per_turn=4096,
                max_tool_calls=int(eval_section.get("max_tool_calls", 25)),
                max_time_minutes=int(eval_section.get("max_time_minutes", 5)),
            )

        # Parse sampling config from `generate_content_config` or legacy `sampling_config`
        raw_sampling: Dict[str, Any] = {}
        gen_cfg = raw.get("generate_content_config")
        if isinstance(gen_cfg, IncludeRef) or (
            isinstance(gen_cfg, str) and gen_cfg.endswith((".yaml", ".yml"))
        ):
            sampling_file = cls._resolve_path(str(gen_cfg), base_search_dirs)
            if sampling_file.is_file():
                raw_sampling = (
                    safe_load_yaml_with_includes(sampling_file.read_text(encoding="utf-8")) or {}
                )
        elif isinstance(gen_cfg, dict):
            raw_sampling = gen_cfg
        else:
            sampling_rel = raw.get("sampling_config", "configs/sampling.yaml")
            sampling_file = cls._resolve_path(str(sampling_rel), base_search_dirs)
            if sampling_file.is_file():
                raw_sampling = (
                    safe_load_yaml_with_includes(sampling_file.read_text(encoding="utf-8")) or {}
                )

        if raw_sampling:
            thinking_cfg = raw_sampling.get("thinking_config")
            thinking_budget = (
                int(thinking_cfg.get("thinking_budget", 4096))
                if isinstance(thinking_cfg, dict)
                else int(raw_sampling.get("max_tokens_per_turn", 4096))
            )
            sampling = SamplingConfig(
                temperature=float(raw_sampling.get("temperature", 0.2)),
                top_p=float(raw_sampling.get("top_p", 0.95)),
                top_k=int(raw_sampling.get("top_k", 40)),
                repetition_penalty=float(raw_sampling.get("repetition_penalty", 1.05)),
                max_tokens_per_turn=thinking_budget,
                max_output_tokens=int(raw_sampling.get("max_output_tokens", thinking_budget)),
                thinking_config=thinking_cfg if isinstance(thinking_cfg, dict) else None,
                stop_sequences=list(raw_sampling.get("stop_sequences", ["<end_of_turn>", "<eos>"])),
            )
        else:
            sampling = SamplingConfig()

        # Parse root tools and sub-agent references (supports agent_tool, list, or dict)
        root_tools: List[str] = []
        sub_agent_refs: Dict[str, str] = {}

        raw_tools = raw.get("tools", [])
        if isinstance(raw_tools, list):
            for entry in raw_tools:
                if isinstance(entry, str):
                    if entry not in SUPPORTED_TOOLS:
                        raise ConfigValidationError(
                            f"Root agent declares unsupported tool '{entry}'."
                        )
                    root_tools.append(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("agent_tool"), dict):
                    cfg_path = entry["agent_tool"].get("config_path", "")
                    if cfg_path:
                        sa_key = Path(str(cfg_path)).stem
                        sub_agent_refs[sa_key] = str(cfg_path)

        raw_sub_agents = raw.get("sub_agents")
        if isinstance(raw_sub_agents, dict):
            for sa_key, sa_rel in raw_sub_agents.items():
                sub_agent_refs[str(sa_key)] = str(sa_rel)
        elif isinstance(raw_sub_agents, list):
            for item in raw_sub_agents:
                if isinstance(item, dict) and item.get("config_path"):
                    cfg_path = str(item["config_path"])
                    sub_agent_refs[Path(cfg_path).stem] = cfg_path

        sub_agents: Dict[str, SubAgentConfig] = {}
        for sa_key, sa_rel in sub_agent_refs.items():
            sa_file = cls._resolve_path(sa_rel, base_search_dirs)
            if not sa_file.is_file():
                raise ConfigValidationError(f"Sub-agent '{sa_key}' config not found: {sa_rel}")
            sa_data = safe_load_yaml_with_includes(sa_file.read_text(encoding="utf-8")) or {}

            sa_search_dirs = [sa_file.parent, *base_search_dirs]
            prompt_rel = sa_data.get("instruction") or sa_data.get("prompt", "")
            prompt_file = cls._resolve_path(str(prompt_rel), sa_search_dirs)
            if prompt_file.is_file():
                prompt_content = prompt_file.read_text(encoding="utf-8")
            else:
                raise ConfigValidationError(f"Sub-agent '{sa_key}' prompt not found: {prompt_rel}")

            sa_desc = str(sa_data.get("description", ""))
            sa_role = str(sa_data.get("role", "")).strip()
            if not sa_role and sa_desc:
                sa_role = sa_desc.split("—")[0].split(":")[0].strip()

            default_b = DEFAULT_SUBAGENT_BUDGETS.get(
                sa_key, {"max_turns": 5, "timeout_seconds": 60}
            )
            sa_tools = sa_data.get("tools")
            if sa_tools is None:
                sa_tools = sa_data.get("allowed_tools", [])
            allowed_tool_names = [t for t in sa_tools if isinstance(t, str)]

            sub_agent = SubAgentConfig(
                name=str(sa_data.get("name", sa_key)),
                role=sa_role,
                description=sa_desc,
                prompt_path=str(prompt_rel),
                prompt_content=prompt_content,
                max_turns=int(sa_data.get("max_turns", default_b["max_turns"])),
                timeout_seconds=int(sa_data.get("timeout_seconds", default_b["timeout_seconds"])),
                allowed_tools=allowed_tool_names,
                model=str(sa_data.get("model", model)),
            )
            sub_agent.validate()
            sub_agents[sa_key] = sub_agent

        # Parse workflow
        raw_wf = raw.get("workflow", {})
        wf_sequence = list(raw_wf.get("sequence", list(sub_agents.keys())))
        default_fallback = (
            "locator" if "locator" in sub_agents else (wf_sequence[0] if wf_sequence else "locator")
        )
        fallback = str(raw_wf.get("fallback_on_failure", default_fallback))
        max_cycles = int(raw_wf.get("max_routing_cycles", 2))

        for step in wf_sequence:
            if step not in sub_agents:
                raise ConfigValidationError(
                    f"Workflow sequence step '{step}' is not declared in sub_agents."
                )
        if wf_sequence and fallback not in sub_agents:
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
            tools=root_tools,
            root_dir=agent_dir,
        )

    @staticmethod
    def _resolve_path(rel_path: str, candidates: List[Path]) -> Path:
        """Finds the first existing candidate for a relative path (handling `../` includes)."""
        if not rel_path:
            return candidates[0] / "__missing__"
        for base in candidates:
            resolved = (base / rel_path).resolve()
            if resolved.is_file():
                return resolved
        # Fallback for `../prompts/foo.md` when prompts/ lives in a parent search dir
        cleaned = rel_path
        while cleaned.startswith("../") or cleaned.startswith("./"):
            cleaned = cleaned.split("/", 1)[1] if "/" in cleaned else cleaned
        if cleaned != rel_path:
            for base in candidates:
                resolved = (base / cleaned).resolve()
                if resolved.is_file():
                    return resolved
        return (candidates[0] / rel_path).resolve()
