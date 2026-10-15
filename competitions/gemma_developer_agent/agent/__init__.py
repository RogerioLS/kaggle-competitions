"""Declarative Agent Architecture Package for Gemma 4.

Exports schema definitions, declarative configuration loaders, and the
orchestration runtime for SWE-bench execution.
"""

from competitions.gemma_developer_agent.agent.inference_engine import (
    ChatMessage,
    GemmaPromptFormatter,
    InferenceEngine,
    MockInferenceEngine,
    TransformersInferenceEngine,
)
from competitions.gemma_developer_agent.agent.react_orchestrator import (
    ReActAction,
    ReActOrchestrator,
    ReActParseError,
    ReActParser,
)
from competitions.gemma_developer_agent.agent.runner import (
    AgentSessionResult,
    DeclarativeAgentRunner,
    ToolCall,
    ToolPermissionError,
    TurnRecord,
)
from competitions.gemma_developer_agent.agent.schema import (
    AgentConfig,
    BudgetConfig,
    ConfigValidationError,
    SamplingConfig,
    SubAgentConfig,
    WorkflowConfig,
)

__all__ = [
    "AgentConfig",
    "AgentSessionResult",
    "BudgetConfig",
    "ChatMessage",
    "ConfigValidationError",
    "DeclarativeAgentRunner",
    "GemmaPromptFormatter",
    "InferenceEngine",
    "MockInferenceEngine",
    "ReActAction",
    "ReActOrchestrator",
    "ReActParseError",
    "ReActParser",
    "SamplingConfig",
    "SubAgentConfig",
    "ToolCall",
    "ToolPermissionError",
    "TransformersInferenceEngine",
    "TurnRecord",
    "WorkflowConfig",
]
