"""Unit tests for Gemma Developer Agent notebook builder."""

from __future__ import annotations

import ast
from pathlib import Path

import nbformat as nbf
import pytest

from competitions.gemma_developer_agent.notebooks.build_notebook import (
    DEFAULT_NOTEBOOK_PATH,
    build_gemma_agent_evaluation_notebook,
    main,
    save_notebook,
)


def test_build_notebook_generates_valid_v4_notebook() -> None:
    """Verifies notebook builder creates a valid nbformat v4 structure."""
    nb = build_gemma_agent_evaluation_notebook()
    assert nb.nbformat == 4
    assert nb.nbformat_minor >= 0
    # Must pass standard schema validation
    nbf.validate(nb)


def test_notebook_metadata_contains_kaggle_gpu_config() -> None:
    """Verifies metadata declares Python 3 kernel and Kaggle GPU accelerator."""
    nb = build_gemma_agent_evaluation_notebook()
    assert nb.metadata.kernelspec.name == "python3"
    assert "kaggle" in nb.metadata
    assert nb.metadata.kaggle.accelerator == "nvidia-l4-x4"
    assert nb.metadata.kaggle.isInternetEnabled is False


def test_notebook_cell_structure_and_syntax() -> None:
    """Verifies all 8 cells exist, their types, and code cells compile with ast."""
    nb = build_gemma_agent_evaluation_notebook()
    assert len(nb.cells) == 8

    # Cell 0: Header markdown
    assert nb.cells[0].cell_type == "markdown"
    assert "Google Gemma 4 Developer Agent" in nb.cells[0].source
    has_decision_loop = (
        "ReAct Decision Loop" in nb.cells[0].source or "Agent Decision Loop" in nb.cells[0].source
    )
    assert has_decision_loop

    # Cells 1 to 7: Code cells
    expected_snippets = [
        "torch.cuda.is_available()",  # Cell 1: GPU check
        "DatasetLoader.load_tasks",  # Cell 2: Ingestion & mounting
        "AgentConfig.from_yaml",  # Cell 3: Engine initialization
        "orchestrator.solve",  # Cell 4: Single instance run
        "RichTelemetryVisualizer.render_diff_html",  # Cell 5: Patch diff viewer
        "runner.benchmark_on_dataset",  # Cell 6: Batch benchmark
        "SubmissionValidator",  # Cell 7: Export submission
    ]

    for idx, snippet in enumerate(expected_snippets, start=1):
        cell = nb.cells[idx]
        assert cell.cell_type == "code"
        assert snippet in cell.source
        # Must be valid Python syntax
        ast.parse(cell.source)


def test_save_and_reload_notebook(tmp_path: Path) -> None:
    """Verifies saving notebook to disk produces valid JSON and reloads cleanly."""
    nb = build_gemma_agent_evaluation_notebook()
    out_file = tmp_path / "test_eval.ipynb"
    saved = save_notebook(nb, out_file)

    assert saved.is_file()
    reloaded = nbf.read(str(saved), as_version=4)
    nbf.validate(reloaded)
    assert len(reloaded.cells) == 8


def test_default_notebook_exists() -> None:
    """Verifies that the default gemma_agent_evaluation.ipynb exists and is valid."""
    assert DEFAULT_NOTEBOOK_PATH.is_file()
    nb = nbf.read(str(DEFAULT_NOTEBOOK_PATH), as_version=4)
    nbf.validate(nb)
    assert len(nb.cells) == 8


def test_cli_main_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies build_notebook CLI main() runs without error."""
    target_out = tmp_path / "cli_eval.ipynb"
    monkeypatch.setattr("sys.argv", ["build_notebook", "--output", str(target_out)])
    exit_code = main()
    assert exit_code == 0
    assert target_out.is_file()
