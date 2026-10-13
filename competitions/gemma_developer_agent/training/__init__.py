"""Gemma 4 Supervised Fine-Tuning and LoRA Post-Training Pipeline."""

from typing import Any

__all__ = [
    "ChatTurn",
    "Trajectory",
    "TrajectoryCollector",
    "LoRAConfig",
    "TrainingHyperparameters",
    "TrainingConfig",
    "TrainingMetrics",
    "LoRATrainer",
    "InstanceComparison",
    "ComparisonResult",
    "ComparativeEvaluator",
]


def __getattr__(name: str) -> Any:
    """Lazy-load module members to avoid runpy circular execution warnings."""
    if name in {"ChatTurn", "Trajectory", "TrajectoryCollector"}:
        from competitions.gemma_developer_agent.training import trajectory_collector

        return getattr(trajectory_collector, name)
    if name in {
        "LoRAConfig",
        "TrainingHyperparameters",
        "TrainingConfig",
        "TrainingMetrics",
        "LoRATrainer",
    }:
        from competitions.gemma_developer_agent.training import lora_trainer

        return getattr(lora_trainer, name)
    if name in {"InstanceComparison", "ComparisonResult", "ComparativeEvaluator"}:
        from competitions.gemma_developer_agent.training import evaluator

        return getattr(evaluator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
