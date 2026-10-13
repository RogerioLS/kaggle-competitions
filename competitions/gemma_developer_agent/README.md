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
| **[TASK-04]** | Declarative Agent Architecture & Structured Prompts | [#9](https://github.com/RogerioLS/kaggle-competitions/issues/9) | 🟢 Completed | `feat/task-04-declarative-agent-baseline` |
| **[TASK-05]** | Kaggle Submission Pipeline & Dry-Run Validator | [#10](https://github.com/RogerioLS/kaggle-competitions/issues/10) | ⚪ Planned | `feat/task-05-submission-pipeline-and-dryrun` |
| **[TASK-06]** | Gemma 4 Post-Training & LoRA Adapter Pipeline | [#11](https://github.com/RogerioLS/kaggle-competitions/issues/11) | ⚪ Planned | `feat/task-06-lora-posttraining-pipeline` |

---

## 🚀 Local Commands & Quickstart

```bash
# 1. Run repository health and governance audit
make audit

# 2. Ingest competition kit or generate test fixtures
python -m competitions.gemma_developer_agent.evaluation.dataset_loader --mode fixtures

# 3. Run evaluation harness on development tasks
python -m competitions.gemma_developer_agent.evaluation.harness --sample 5

# 4. Package and validate submission.zip
make package-submission
```
