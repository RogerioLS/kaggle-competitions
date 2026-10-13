"""Submission packaging, validation, and dry-run pipeline for Gemma 4 Developer Agent."""

from typing import Any

__all__ = [
    "SubmissionPackager",
    "package_submission",
    "SubmissionValidator",
    "ValidationResult",
    "validate_submission",
    "verify_submission_dry_run",
]


def __getattr__(name: str) -> Any:
    """Lazy-load module members to avoid runpy circular execution warnings."""
    if name in {"SubmissionPackager", "package_submission"}:
        from competitions.gemma_developer_agent.submission import packager

        return getattr(packager, name)
    if name in {
        "SubmissionValidator",
        "ValidationResult",
        "validate_submission",
        "verify_submission_dry_run",
    }:
        from competitions.gemma_developer_agent.submission import validator

        return getattr(validator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
