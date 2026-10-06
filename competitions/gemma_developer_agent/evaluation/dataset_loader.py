"""Dataset Loader and Ingestion Engine for Google Gemma 4 Developer Agent Competition.

Parses SWE-bench development benchmark tasks, AST call/dependency graphs,
dense float32 semantic embeddings, and creates reproducible fixtures.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class SWEInstance:
    """Represents a single SWE-bench software engineering benchmark task.

    Attributes:
        instance_id: Unique task identifier (e.g. 'psf__requests-863').
        repo: GitHub repository slug (e.g. 'psf/requests').
        base_commit: 40-char commit SHA before the bug fix.
        problem_statement: Bug report or issue prompt provided to the agent.
        hints_text: Optional maintainer discussions or hints.
        patch: Reference gold solution patch.
        test_patch: Unit test patch that reproduces and validates the issue.
        created_at: ISO-8601 creation timestamp.
    """

    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    hints_text: str = ""
    patch: str = ""
    test_patch: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializes instance to dictionary format."""
        return asdict(self)


class CodeGraph:
    """NetworkX Abstract Syntax Tree (AST) call and dependency graph wrapper.

    Provides structural symbol lookup and neighborhood traversals without AST parsing overhead.
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initializes code graph from raw JSON dictionary.

        Args:
            data: Parsed JSON data conforming to NetworkX multigraph schema.
        """
        self.raw_data = data
        self.nodes: Dict[str, Dict[str, Any]] = {}
        for node in data.get("nodes", []):
            if "id" in node:
                self.nodes[node["id"]] = node

        self.edges: List[Dict[str, Any]] = data.get("edges", [])

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves symbol metadata by qualified node ID."""
        return self.nodes.get(node_id)

    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[str] = None,
        max_neighbors: int = 50,
    ) -> List[str]:
        """Finds incoming and outgoing neighbors of a symbol in the graph.

        Args:
            node_id: Target symbol path (e.g. 'fastapi.routing.get_request_handler').
            edge_type: Optional filter (e.g. 'calls', 'imports', 'inherits').
            max_neighbors: Maximum neighbor IDs to return.

        Returns:
            List of unique neighboring symbol node IDs.
        """
        neighbors: set[str] = set()

        for edge in self.edges:
            source = edge.get("source")
            target = edge.get("target")
            e_type = edge.get("type")

            if edge_type and e_type != edge_type:
                continue

            if source == node_id and target:
                neighbors.add(target)
            elif target == node_id and source:
                neighbors.add(source)

            if len(neighbors) >= max_neighbors:
                break

        return sorted(list(neighbors))[:max_neighbors]

    def get_subgraph(self, node_ids: List[str]) -> Dict[str, Any]:
        """Extracts induced subgraph containing specified nodes and interconnecting edges."""
        target_set = set(node_ids)
        sub_nodes = [node for nid, node in self.nodes.items() if nid in target_set]
        sub_edges = [
            edge
            for edge in self.edges
            if edge.get("source") in target_set and edge.get("target") in target_set
        ]

        return {
            "directed": self.raw_data.get("directed", True),
            "multigraph": self.raw_data.get("multigraph", True),
            "nodes": sub_nodes,
            "edges": sub_edges,
        }


class CodeEmbeddings:
    """Dense semantic vector feature store for offline cosine similarity retrieval."""

    def __init__(self, node_ids: List[str], vectors: np.ndarray) -> None:
        """Initializes embedding index.

        Args:
            node_ids: List of qualified symbol IDs corresponding to vectors.
            vectors: Float32 numpy matrix of shape (N, D), typically (N, 256).
        """
        if len(node_ids) != len(vectors):
            raise ValueError(f"Mismatch: {len(node_ids)} node_ids vs {len(vectors)} vectors")

        self.node_ids = node_ids
        self.vectors = vectors.astype(np.float32)

        # Normalize vectors for fast cosine similarity via dot product
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.normalized_vectors = self.vectors / norms

    def search_similar(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Finds top-k symbol nodes with highest cosine similarity to query vector.

        Args:
            query_vector: Float32 vector of dimension D.
            k: Top-k results to return.

        Returns:
            List of tuples (node_id, cosine_score) sorted descending by similarity.
        """
        q = query_vector.astype(np.float32).flatten()
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm

        scores = np.dot(self.normalized_vectors, q)
        top_indices = np.argsort(scores)[::-1][:k]

        return [(self.node_ids[idx], float(scores[idx])) for idx in top_indices]


class DatasetLoader:
    """Central dataset loader and offline fixture manager for SWE-bench instances."""

    @staticmethod
    def load_tasks(tasks_path: Path | str) -> List[SWEInstance]:
        """Loads SWE-bench instances from a JSONL file.

        Args:
            tasks_path: File path to tasks.jsonl.

        Returns:
            List of SWEInstance objects.

        Raises:
            FileNotFoundError: If tasks_path does not exist.
        """
        path = Path(tasks_path)
        if not path.is_file():
            raise FileNotFoundError(f"Tasks file not found: {path}")

        instances: List[SWEInstance] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    data = json.loads(clean_line)
                    instances.append(
                        SWEInstance(
                            instance_id=data["instance_id"],
                            repo=data.get("repo", ""),
                            base_commit=data.get("base_commit", ""),
                            problem_statement=data.get("problem_statement", ""),
                            hints_text=data.get("hints_text", ""),
                            patch=data.get("patch", ""),
                            test_patch=data.get("test_patch", ""),
                            created_at=data.get("created_at", ""),
                        )
                    )
                except (json.JSONDecodeError, KeyError) as err:
                    print(f"Warning: Line {line_num} invalid in {path}: {err}")

        return instances

    @staticmethod
    def load_task_by_id(tasks_path: Path | str, instance_id: str) -> Optional[SWEInstance]:
        """Loads a single benchmark task by its instance_id."""
        tasks = DatasetLoader.load_tasks(tasks_path)
        for task in tasks:
            if task.instance_id == instance_id:
                return task
        return None

    @staticmethod
    def load_graph(graph_path: Path | str) -> CodeGraph:
        """Loads and parses a NetworkX JSON AST graph."""
        path = Path(graph_path)
        if not path.is_file():
            raise FileNotFoundError(f"Graph file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CodeGraph(data)

    @staticmethod
    def load_embeddings(emb_path: Path | str) -> CodeEmbeddings:
        """Loads symbol embeddings from a .npz or .npy archive."""
        path = Path(emb_path)
        if not path.is_file():
            raise FileNotFoundError(f"Embeddings file not found: {path}")

        with np.load(path) as data:
            if "node_ids" in data and "vectors" in data:
                node_ids = list(data["node_ids"])
                vectors = data["vectors"]
            else:
                # Handle dictionary of individual arrays or matrix
                keys = list(data.keys())
                node_ids = keys
                vectors = np.array([data[k] for k in keys], dtype=np.float32)

        return CodeEmbeddings(node_ids=node_ids, vectors=vectors)

    @staticmethod
    def create_mock_fixtures(target_dir: Path | str) -> Path:
        """Generates a complete offline mock fixture dataset for fast testing and CI/CD.

        Creates tasks.jsonl, a sample AST graph, and synthetic 256-d embeddings.

        Args:
            target_dir: Directory where fixtures will be generated.

        Returns:
            Path to the initialized fixtures root directory.
        """
        root = Path(target_dir)
        root.mkdir(parents=True, exist_ok=True)
        graphs_dir = root / "graphs"
        embeddings_dir = root / "embeddings"
        graphs_dir.mkdir(exist_ok=True)
        embeddings_dir.mkdir(exist_ok=True)

        # 1. Create sample tasks.jsonl
        task_1 = SWEInstance(
            instance_id="psf__requests-863",
            repo="psf/requests",
            base_commit="e818b2849e7b257d0796ff0a1841320efad3a5b6",
            problem_statement="Fix redirect status code handling when allow_redirects=False.",
            hints_text="Check status_code in (301, 302, 303, 307).",
            patch="""diff --git a/requests/models.py b/requests/models.py
--- a/requests/models.py
+++ b/requests/models.py
@@ -10,3 +10,4 @@
 def handle_redirect():
+    pass
""",
            test_patch="""diff --git a/tests/test_requests.py b/tests/test_requests.py
--- a/tests/test_requests.py
+++ b/tests/test_requests.py
@@ -20,3 +20,4 @@
 def test_redirect():
+    assert True
""",
            created_at="2026-09-25T12:00:00Z",
        )

        task_2 = SWEInstance(
            instance_id="fastapi__fastapi-11194",
            repo="fastapi/fastapi",
            base_commit="4f2b1c90a18b76251ef0a4309312b918fa09e32a",
            problem_statement="Response model validation fails for nested Union with None.",
            hints_text="Inspect fastapi.routing._prepare_response_content.",
            patch="""diff --git a/fastapi/routing.py b/fastapi/routing.py
--- a/fastapi/routing.py
+++ b/fastapi/routing.py
@@ -15,3 +15,4 @@
 def prepare():
+    pass
""",
            test_patch="""diff --git a/tests/test_routing.py b/tests/test_routing.py
--- a/tests/test_routing.py
+++ b/tests/test_routing.py
@@ -30,3 +30,4 @@
 def test_union():
+    assert True
""",
            created_at="2026-09-26T14:30:00Z",
        )

        tasks_file = root / "tasks.jsonl"
        with open(tasks_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(task_1.to_dict()) + "\n")
            f.write(json.dumps(task_2.to_dict()) + "\n")

        # 2. Create sample graph JSON
        graph_data = {
            "directed": True,
            "multigraph": True,
            "graph": {"repo": "psf/requests"},
            "nodes": [
                {
                    "id": "requests.sessions.Session.send",
                    "name": "send",
                    "text": "def send(self, request, **kwargs): ...",
                },
                {
                    "id": "requests.adapters.HTTPAdapter.send",
                    "name": "send",
                    "text": "def send(self, request, stream=False, ...): ...",
                },
                {
                    "id": "requests.models.Response",
                    "name": "Response",
                    "text": "class Response: ...",
                },
            ],
            "edges": [
                {
                    "source": "requests.sessions.Session.send",
                    "target": "requests.adapters.HTTPAdapter.send",
                    "type": "calls",
                    "key": 0,
                },
                {
                    "source": "requests.sessions.Session.send",
                    "target": "requests.models.Response",
                    "type": "returns",
                    "key": 0,
                },
            ],
        }
        graph_file = graphs_dir / "psf__requests-863.json"
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)

        # 3. Create synthetic 256-d embeddings (.npz)
        rng = np.random.default_rng(42)
        node_ids = np.array([node["id"] for node in graph_data["nodes"]])
        vectors = rng.standard_normal((len(node_ids), 256)).astype(np.float32)
        emb_file = embeddings_dir / "psf__requests-863.npz"
        np.savez(emb_file, node_ids=node_ids, vectors=vectors)

        return root
