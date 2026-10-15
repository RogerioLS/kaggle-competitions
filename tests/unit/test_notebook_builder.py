"""Unit tests for Gemma Developer Agent notebook builder."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict

import pytest

try:
    import nbformat as nbf
except ImportError:
    nbf = None

from competitions.gemma_developer_agent.notebooks.build_notebook import (
    DEFAULT_NOTEBOOK_PATH,
    build_gemma_agent_evaluation_notebook,
    main,
    save_notebook,
)


def _get_cells(nb: Any) -> list[Any]:
    if isinstance(nb, dict):
        return nb["cells"]
    return list(nb.cells)


def _get_cell_type(cell: Any) -> str:
    if isinstance(cell, dict):
        return str(cell["cell_type"])
    return str(cell.cell_type)


def _get_cell_source(cell: Any) -> str:
    if isinstance(cell, dict):
        source = cell["source"]
    else:
        source = cell.source
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def _get_metadata(nb: Any) -> Dict[str, Any]:
    if isinstance(nb, dict):
        return nb.get("metadata", {})
    return dict(nb.metadata)


def test_build_notebook_generates_valid_v4_notebook() -> None:
    """Verifies notebook builder creates a valid nbformat v4 structure."""
    nb = build_gemma_agent_evaluation_notebook()
    if isinstance(nb, dict):
        assert nb.get("nbformat") == 4
        assert nb.get("nbformat_minor", 0) >= 0
    else:
        assert nb.nbformat == 4
        assert nb.nbformat_minor >= 0
    if nbf is not None:
        nbf.validate(nb)


def test_notebook_metadata_contains_kaggle_gpu_config() -> None:
    """Verifies metadata declares Python 3 kernel and Kaggle GPU accelerator."""
    nb = build_gemma_agent_evaluation_notebook()
    meta = _get_metadata(nb)
    kernelspec = meta.get("kernelspec", {})
    kernel_name = kernelspec.get("name") if isinstance(kernelspec, dict) else kernelspec.name
    kaggle = meta.get("kaggle", {})
    accelerator = kaggle.get("accelerator") if isinstance(kaggle, dict) else kaggle.accelerator
    is_internet = (
        kaggle.get("isInternetEnabled") if isinstance(kaggle, dict) else kaggle.isInternetEnabled
    )

    assert kernel_name == "python3"
    assert accelerator == "nvidia-l4-x4"
    assert is_internet is False


def test_notebook_cell_structure_and_syntax() -> None:
    """Verifies all 8 cells exist, their types, and code cells compile with ast."""
    nb = build_gemma_agent_evaluation_notebook()
    cells = _get_cells(nb)
    assert len(cells) == 8

    # Cell 0: Header markdown
    assert _get_cell_type(cells[0]) == "markdown"
    assert "Google Gemma 4 Developer Agent" in _get_cell_source(cells[0])
    has_decision_loop = "ReAct Decision Loop" in _get_cell_source(
        cells[0]
    ) or "Agent Decision Loop" in _get_cell_source(cells[0])
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
        cell = cells[idx]
        assert _get_cell_type(cell) == "code"
        source = _get_cell_source(cell)
        assert snippet in source
        # Must be valid Python syntax
        ast.parse(source)


def test_save_and_reload_notebook(tmp_path: Path) -> None:
    """Verifies saving notebook to disk produces valid JSON and reloads cleanly."""
    nb = build_gemma_agent_evaluation_notebook()
    out_file = tmp_path / "test_eval.ipynb"
    saved = save_notebook(nb, out_file)

    assert saved.is_file()
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert "cells" in data
    assert len(data["cells"]) == 8

    if nbf is not None:
        reloaded = nbf.read(str(saved), as_version=4)
        nbf.validate(reloaded)
        assert len(reloaded.cells) == 8


def test_default_notebook_exists() -> None:
    """Verifies that the default gemma_agent_evaluation.ipynb exists and is valid."""
    assert DEFAULT_NOTEBOOK_PATH.is_file()
    data = json.loads(DEFAULT_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    assert "cells" in data
    assert len(data["cells"]) == 8

    if nbf is not None:
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
