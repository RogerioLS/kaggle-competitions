"""Unit tests for the Kaggle Gemma Developer Agent evaluation notebook.

Validates that the notebook exists, satisfies Jupyter Notebook v4 JSON schema,
and contains all required workflow cells and architectural component references.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

try:
    import nbformat as nbf
except ImportError:
    nbf = None

NOTEBOOK_RELATIVE_PATH = Path(
    "competitions/gemma_developer_agent/notebooks/gemma_agent_evaluation.ipynb"
)


@pytest.fixture
def repo_root() -> Path:
    """Returns the repository root path."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "competitions").is_dir() and (current / "setup.py").is_file():
            return current
        if (current / "competitions").is_dir() and (current / "pyproject.toml").is_file():
            return current
        current = current.parent
    return Path.cwd()


@pytest.fixture
def evaluation_notebook_path(repo_root: Path) -> Path:
    """Returns the absolute path to gemma_agent_evaluation.ipynb."""
    nb_path = repo_root / NOTEBOOK_RELATIVE_PATH
    return nb_path


@pytest.fixture
def notebook_data(evaluation_notebook_path: Path) -> Dict[str, Any]:
    """Parses and returns notebook json content."""
    raw = evaluation_notebook_path.read_text(encoding="utf-8")
    return json.loads(raw)


def _cell_source(cell: Dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def test_notebook_file_exists(evaluation_notebook_path: Path) -> None:
    """Verifies that the evaluation notebook file exists on disk."""
    assert (
        evaluation_notebook_path.is_file()
    ), f"Evaluation notebook missing at: {evaluation_notebook_path}"


def test_notebook_valid_json_and_v4_schema(
    evaluation_notebook_path: Path, notebook_data: Dict[str, Any]
) -> None:
    """Verifies that the notebook is valid JSON and adheres to nbformat v4 schema."""
    assert isinstance(notebook_data, dict)
    assert "cells" in notebook_data
    assert "metadata" in notebook_data
    assert notebook_data.get("nbformat") == 4
    assert notebook_data.get("nbformat_minor", 0) >= 0

    if nbf is not None:
        raw_content = evaluation_notebook_path.read_text(encoding="utf-8")
        nb_node = nbf.reads(raw_content, as_version=4)
        nbf.validate(nb_node)


def test_notebook_metadata_kaggle_compatibility(notebook_data: Dict[str, Any]) -> None:
    """Verifies notebook metadata configures Kaggle environment and kernel correctly."""
    metadata = notebook_data.get("metadata", {})

    # Kernel specification check
    assert "kernelspec" in metadata
    kernelspec = metadata["kernelspec"]
    assert kernelspec.get("name") == "python3"

    # Kaggle air-gapped GPU settings
    assert "kaggle" in metadata
    kaggle = metadata["kaggle"]
    assert kaggle.get("accelerator") == "nvidia-l4-x4"
    assert kaggle.get("isInternetEnabled") is False


def test_notebook_contains_all_required_workflow_cells(notebook_data: Dict[str, Any]) -> None:
    """Verifies the notebook contains all required workflow cells."""
    cells = notebook_data.get("cells", [])
    sources: List[str] = [_cell_source(c) for c in cells]

    # 1. Environment check
    assert any(
        "torch.cuda.is_available()" in s or "System Platform" in s for s in sources
    ), "Missing environment / GPU check cell."

    # 2. Dataset ingestion
    assert any(
        "DatasetLoader" in s or "load_tasks" in s for s in sources
    ), "Missing dataset ingestion cell."

    # 3. ReAct runner
    assert any(
        "ReActOrchestrator" in s or "orchestrator.solve" in s for s in sources
    ), "Missing ReAct runner cell."

    # 4. Diff viewer
    assert any(
        "render_diff_html" in s or "Patch Diff Viewer" in s for s in sources
    ), "Missing patch diff viewer cell."

    # 5. Benchmark summary
    assert any(
        "benchmark_on_dataset" in s or "render_benchmark_report_html" in s for s in sources
    ), "Missing benchmark summary cell."

    # 6. Submission packager
    assert any(
        "SubmissionPackager" in s or "SubmissionValidator" in s for s in sources
    ), "Missing submission packager cell."

    # Ensure all code cells compile without Python syntax errors
    for idx, cell in enumerate(cells):
        if cell.get("cell_type") == "code":
            source = _cell_source(cell)
            try:
                ast.parse(source)
            except SyntaxError as exc:
                pytest.fail(f"Cell {idx} contains invalid Python syntax: {exc}")


def test_notebook_references_core_architectural_components(
    notebook_data: Dict[str, Any],
) -> None:
    """Verifies the notebook references the 4 core components required by specification."""
    cells = notebook_data.get("cells", [])
    all_code_sources = "\n".join(_cell_source(c) for c in cells if c.get("cell_type") == "code")

    required_components = [
        "RichTelemetryVisualizer",
        "ReActOrchestrator",
        "LocalSWEHarness",
        "SubmissionValidator",
    ]

    for component in required_components:
        assert (
            component in all_code_sources
        ), f"Required architectural component '{component}' is not referenced in notebook cells."
