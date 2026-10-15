# 🤖 Google - The Gemma 4 Developer Agent Competition

[![Kaggle Competition](https://img.shields.io/badge/Kaggle-Competition%20Page-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Prize Pool](https://img.shields.io/badge/Prizes-%24100%2C000%20USD-gold.svg)](https://www.kaggle.com/competitions/gemma-4-developer-agent)
[![Model](https://img.shields.io/badge/Model-Gemma%204%2031B%20(W4A16)-blue.svg)](https://huggingface.co/google/gemma-4-31b-it)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Target Score](https://img.shields.io/badge/Target%20Score-%3E0.25%20Pass%401-brightgreen.svg)](#-leaderboard-tracker)

> **Official Competition URL:** [https://www.kaggle.com/competitions/gemma-4-developer-agent](https://www.kaggle.com/competitions/gemma-4-developer-agent)

---

## 🧭 Executive Overview

**The Gemma 4 Developer Agent Competition** is a flagship challenge hosted by Google DeepMind to pioneer autonomous coding agents powered by open-weights models running offline on consumer-grade hardware.

- **Core Challenge**: Post-train and configure **Gemma 4 31B** (`gemma-4-31b-it-qat-w4a16-ct`) into an autonomous software engineering agent that navigates complex, unfamiliar codebases, reproduces issues, writes patches, and passes verification test suites (SWE-bench benchmark style).
- **Execution Environment**: Kaggle 4x NVIDIA L4 GPUs (96GB VRAM total), running in strict **offline mode** (`--network none`) with a 12-hour total evaluation budget.

---

## 🏆 Prize Structure & Timeline

| Track | Prize Pool | Focus & Deliverable | Key Deadline |
| :--- | :--- | :--- | :--- |
| **Track 1: Featured Prediction Competition** | **$65,000 USD**<br>(1st: $37k \| 2nd: $18k \| 3rd: $10k) | Pass@1 resolution rate on the hidden private SWE-bench test set. | **Dec 02, 2026**<br>(Entry & Merger: Nov 25) |
| **Track 2: Paper Track** | **$35,000 USD**<br>(NeurIPS Expo Workshop Showcase) | Research paper on code-graphs, agent architectures, and LoRA post-training. | **Nov 12, 2026** (11:59 PM UTC) |

---

## 📊 Leaderboard Tracker

| Tier | Pass@1 Resolution Rate | Status / Competitor Benchmark |
| :--- | :---: | :--- |
| **Current #1 (Gold)** | **0.24** (24%) | Leading competitor on Kaggle Public Leaderboard |
| **Top 2 – 6 (Gold/Silver)** | **0.17 – 0.18** | Clustered prompt-engineering & basic grep agents |
| **Naive Baseline** | **~0.10 – 0.12** | Raw model without graph navigation or test loop |
| 🎯 **Our Target** | **> 0.25+** | **Leaderboard Top 1 + NeurIPS Paper Presentation** |

> [!NOTE]
> 76% of issues remain completely unsolved by existing competitors. By combining pre-computed code graphs, closed-loop pytest verification, and targeted LoRA fine-tuning, our architecture directly attacks the primary failure modes.

---

## 📦 Submission Specification (`submission.zip`)

> [!IMPORTANT]
> **Declarative Architecture Requirement**:
> Submissions **must not** contain raw Python entrypoints (e.g. `agent.py` is disallowed by the Kaggle sandbox). The submission is evaluated by a sandboxed YAML compiler. The root of `submission.zip` must contain `agent.yaml`.

```text
submission.zip
├── agent.yaml                       # REQUIRED: Root declarative agent spec
├── configs/
│   └── sampling.yaml                # Decoding parameters (temperature, top_p)
├── prompts/
│   ├── system.md                    # Root orchestrator instructions
│   ├── explorer.md                  # Semantic codebase exploration
│   ├── locator.md                   # Bug localization and test reproducer
│   ├── drafter.md                   # Surgical code patch surgeon
│   └── validator.md                 # Test suite runner & regression gatekeeper
├── sub_agents/                      # Sub-agent YAML configurations
│   ├── explorer.yaml
│   ├── locator.yaml
│   ├── drafter.yaml
│   └── validator.yaml
├── skills/                          # ADK Skill SOPs (SKILL.md)
│   ├── reproducer_writer/
│   └── git_diff_sanitizer/
└── adapters/                        # PEFT LoRA adapter weights (optional)
    └── gemma4-swe-w4a16/
        ├── adapter_config.json
        └── adapter_model.safetensors
```

---

## 🛠️ Predefined Sandbox Environment Tools

The competition sandbox provides 9 native tools to the agent:

### 1. Code-Graph & Semantic Retrieval Tools (Zero GPU VRAM Overhead)
- `search_similar_code(query: str, k: int = 10)`: Finds top-$k$ graph nodes with highest cosine similarity in the 256-d float32 embeddings.
- `get_code_neighbors(node: str, edge_type: str | None = None, max_neighbors: int = 50)`: Traverses callers, callees, and dependencies in the NetworkX AST graph.
- `get_code_subgraph(nodes: list[str])`: Extracts induced structural subgraph to provide concise context without reading entire files.

### 2. Operational & Execution Tools
- `read_file(filepath: str, start_line: int | None, end_line: int | None)`: 1-indexed inclusive slicing of files in `/workspace`.
- `edit_file(filepath: str, old_string: str, new_string: str, allow_multiple: bool = False)`: Atomic string replacement.
- `write_file(filepath: str, content: str)`: Creates or overwrites files (used for standalone test reproducers).
- `run_command(command: str)`: Executes commands in `/bin/bash -c` inside `/workspace` (e.g., `pytest`, `git diff`).
- `get_status()`: Returns remaining execution budget and dirty file list.
- `submit_patch()`: Stages file modifications and captures `git diff HEAD` as the final submission patch.

---

## 🧪 Dataset Breakdown (22.42 GB)

- `tasks.jsonl`: 129 public SWE-bench benchmark tasks across `fastapi`, `rich`, `requests`, and `httpx`.
  - Fields: `instance_id`, `repo`, `base_commit`, `problem_statement`, `hints_text`, `patch`, `test_patch`.
- `snapshots/`: 129 `.tgz` archives containing frozen Git repositories at `base_commit` with future history removed.
- `graphs/`: 256 NetworkX AST call and dependency graphs in JSON format.
- `embeddings/`: 256 `.npz` files containing 256-dimensional float32 dense semantic vector features.
- `wheels/`: 124 offline Python wheels mounted at `/wheels/` (`pip install --no-index --find-links=/wheels -e .`).
- `docker/`: Specifications for building the local `swebench-sandbox:latest` container.

---

## 🗺️ Engineering Tasks & Issue Backlog

| Task ID | Issue Specification | GitHub Issue | Status | Branch |
| :--- | :--- | :---: | :---: | :--- |
| **[TASK-01]** | Project Initialization & Clean Chassis OS | [#6](https://github.com/RogerioLS/kaggle-competitions/issues/6) | 🟢 Completed | `main` |
| **[TASK-02]** | Competition Ingestion & Dataset Preparation | [#7](https://github.com/RogerioLS/kaggle-competitions/issues/7) | 🟢 Completed | `main` |
| **[TASK-03]** | Local SWE-bench Evaluation Harness & Sandbox | [#8](https://github.com/RogerioLS/kaggle-competitions/issues/8) | 🟢 Completed | `main` |
| **[TASK-04]** | Declarative Agent Architecture & Structured Prompts | [#9](https://github.com/RogerioLS/kaggle-competitions/issues/9) | 🟢 Completed | `main` |
| **[TASK-05]** | Kaggle Submission Pipeline & Dry-Run Validator | [#10](https://github.com/RogerioLS/kaggle-competitions/issues/10) | 🟢 Completed | `main` |
| **[TASK-06]** | Gemma 4 Post-Training & LoRA Adapter Pipeline | [#11](https://github.com/RogerioLS/kaggle-competitions/issues/11) | 🟢 Completed | `main` |
| **[TASK-07]** | Kaggle Code Submission Automation & Offline Kernel | [#20](https://github.com/RogerioLS/kaggle-competitions/issues/20) | 🟢 Completed | `feat/task-07-kaggle-submission-and-kernel` |
| **[TASK-08]** | GitHub-to-Kaggle Dataset Sync Automation & CI/CD | [#22](https://github.com/RogerioLS/kaggle-competitions/issues/22) | 🟢 Completed | `feat/task-08-kaggle-dataset-sync` |
| **[TASK-09]** | Gemma 4 Autonomous ReAct Engine & Tool-Calling Loop | Pending | 🟢 Completed | `feat/task-09-gemma4-react-engine` |
| **[TASK-10]** | Interactive Kaggle GPU Evaluation Notebook & Telemetry | Pending | ⚪ Planned | `feat/task-10-kaggle-evaluation-notebook` |

---

## 🔬 Fluxo Autônomo de Resolução (Closed-Loop ReAct Engine)

Para você ter total controle do fluxo, aqui está a anatomia exata do que o código vai fazer a cada passo:

```mermaid
sequenceDiagram
    autonumber
    actor SWE as SWE-bench Task
    participant Orchestrator as ReAct Orchestrator
    participant Model as Gemma 4 31B (W4A16)
    participant Sandbox as Subprocess Sandbox

    SWE->>Orchestrator: Entrega problem_statement (ex: Bug no FastAPI)

    loop Ciclo Autônomo de Resolução (até 30 turnos)
        Orchestrator->>Model: Envia histórico + ferramentas disponíveis (&lt;start_of_turn&gt;user)
        Model-->>Orchestrator: Responde com Pensamento + Ação JSON (&lt;start_of_turn&gt;model)

        alt Ação: Navegar no Código
            Orchestrator->>Sandbox: search_similar_code(query) ou read_file(path)
            Sandbox-->>Orchestrator: Retorna código ou nós do grafo
        else Ação: Reproduzir o Bug
            Orchestrator->>Sandbox: write_file("reproducer.py", content)
            Sandbox-->>Orchestrator: Arquivo criado com sucesso
        else Ação: Editar Código (Correção)
            Orchestrator->>Sandbox: edit_file(path, old_str, new_str)
            Sandbox-->>Orchestrator: Linhas alteradas com sucesso
        else Ação: Validar com Testes
            Orchestrator->>Sandbox: run_command("pytest reproducer.py")
            Sandbox-->>Orchestrator: Traceback ou "All tests passed!"
        end

        Orchestrator->>Model: Devolve o resultado da ferramenta como Observação
    end

    Orchestrator->>Sandbox: submit_patch() -> captura "git diff HEAD"
    Sandbox-->>SWE: Patch final gerado para submissão
```

---

## 📡 Kaggle Submission Protocol & Execution Guide

The repository supports multiple submission modes designed for Kaggle's offline evaluation environment:

### Mode 1: End-to-End Pipeline Maestro (Recommended)
Executes the full pipeline in a single command (trajectory collection, LoRA fine-tuning, Pass@1 comparative evaluation, packaging, and offline validation):
```bash
make pipeline
```

### Mode 2: Automated Kaggle CLI Submission
Dispatches `artifacts/submission.zip` directly to the Kaggle competition:
```bash
# Dry-run validation (no network calls)
make submit-kaggle ARGS="--dry-run"

# Live submission to Kaggle leaderboard
make submit-kaggle ARGS="--message 'Gemma 4 Multi-Agent LoRA W4A16 Production Submission'"

# Query recent submissions status
make submit-kaggle ARGS="--status"
```

### Mode 3: Standalone Offline Kaggle Kernel
Simulates execution inside Kaggle's 4x NVIDIA L4 GPU environment (`--network none`):
```bash
make run-kernel
```

### Mode 4: Automated GitHub-to-Kaggle Dataset Sync
Synchronizes codebase modules (`competitions`, `src`, `scripts`) into a Kaggle Dataset (`gemma-agent-code`) for offline notebook execution:
```bash
# Dry-run packaging simulation
make sync-dataset ARGS="--dry-run"

# Live push to Kaggle Datasets
make sync-dataset ARGS="--message 'Sync Gemma 4 agent modules'"
```

Inside your Kaggle Notebook (runs even with `Internet: OFF`):
```python
import sys
sys.path.insert(0, "/kaggle/input/gemma-agent-code")

from competitions.gemma_developer_agent.agent.runner import DeclarativeAgentRunner
```

---

## 🚀 Local Commands & Quickstart

```bash
# 1. Run repository health and governance audit
make audit

# 2. Ingest competition kit or generate test fixtures
python -m competitions.gemma_developer_agent.evaluation.dataset_loader --mode fixtures

# 3. Run evaluation harness on development tasks
python -m competitions.gemma_developer_agent.evaluation.harness --sample 5

# 4. Extract SFT trajectories and fine-tune Gemma 4 LoRA adapter
make collect-trajectories
make train-lora
make evaluate-comparison

# 5. Package and validate submission.zip
make package-submission
make verify-submission

# 6. Execute full pipeline and submit
make pipeline
make submit-kaggle ARGS="--dry-run"

# 7. Sync codebase to Kaggle Dataset
make sync-dataset ARGS="--dry-run"
```
