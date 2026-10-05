"""Unit Tests for SWE-bench Dataset Loader & Graph Embeddings."""

import tempfile

import numpy as np
import pytest

from competitions.gemma_developer_agent.evaluation.dataset_loader import (
    CodeEmbeddings,
    CodeGraph,
    DatasetLoader,
    SWEInstance,
)


class TestSWEInstance:
    """Tests for SWEInstance dataclass."""

    def test_swe_instance_attributes_and_dict(self) -> None:
        inst = SWEInstance(
            instance_id="test__repo-1",
            repo="test/repo",
            base_commit="abc12345",
            problem_statement="Fix bug in foo()",
            hints_text="Check bar()",
            patch="diff --git a/foo.py...",
            test_patch="diff --git a/test_foo.py...",
        )
        assert inst.instance_id == "test__repo-1"
        data = inst.to_dict()
        assert data["instance_id"] == "test__repo-1"
        assert data["repo"] == "test/repo"


class TestCodeGraph:
    """Tests for NetworkX AST CodeGraph wrapper."""

    def test_get_neighbors_and_subgraph(self) -> None:
        graph_data = {
            "directed": True,
            "multigraph": True,
            "nodes": [
                {"id": "mod.A", "name": "A"},
                {"id": "mod.B", "name": "B"},
                {"id": "mod.C", "name": "C"},
            ],
            "edges": [
                {"source": "mod.A", "target": "mod.B", "type": "calls"},
                {"source": "mod.A", "target": "mod.C", "type": "imports"},
            ],
        }
        cg = CodeGraph(graph_data)
        assert cg.get_node("mod.A") is not None
        assert cg.get_node("mod.X") is None

        # Check all neighbors
        neighbors = cg.get_neighbors("mod.A")
        assert "mod.B" in neighbors
        assert "mod.C" in neighbors

        # Filter by edge type
        calls = cg.get_neighbors("mod.A", edge_type="calls")
        assert calls == ["mod.B"]

        # Subgraph extraction
        sub = cg.get_subgraph(["mod.A", "mod.B"])
        assert len(sub["nodes"]) == 2
        assert len(sub["edges"]) == 1


class TestCodeEmbeddings:
    """Tests for CodeEmbeddings dense vector retrieval."""

    def test_search_similar(self) -> None:
        node_ids = ["node_1", "node_2", "node_3"]
        # Create vectors where node_1 is aligned with query
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        v3 = np.array([0.5, 0.5, 0.0], dtype=np.float32)
        vectors = np.stack([v1, v2, v3])

        emb = CodeEmbeddings(node_ids=node_ids, vectors=vectors)
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        results = emb.search_similar(query, k=2)

        assert len(results) == 2
        top_node, top_score = results[0]
        assert top_node == "node_1"
        assert pytest.approx(top_score, rel=1e-3) == 1.0


class TestDatasetLoader:
    """Tests for DatasetLoader and Mock Fixtures."""

    def test_create_fixtures_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = DatasetLoader.create_mock_fixtures(tmp_dir)
            tasks_file = root / "tasks.jsonl"
            assert tasks_file.is_file()

            # Load tasks
            tasks = DatasetLoader.load_tasks(tasks_file)
            assert len(tasks) == 2
            assert tasks[0].instance_id == "psf__requests-863"
            assert tasks[1].instance_id == "fastapi__fastapi-11194"

            # Load specific task by ID
            task = DatasetLoader.load_task_by_id(tasks_file, "fastapi__fastapi-11194")
            assert task is not None
            assert task.repo == "fastapi/fastapi"

            # Load graph
            graph_file = root / "graphs" / "psf__requests-863.json"
            graph = DatasetLoader.load_graph(graph_file)
            assert len(graph.nodes) == 3

            # Load embeddings
            emb_file = root / "embeddings" / "psf__requests-863.npz"
            embeddings = DatasetLoader.load_embeddings(emb_file)
            assert len(embeddings.node_ids) == 3
            assert embeddings.vectors.shape == (3, 256)
