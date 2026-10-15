---
id: TASK-10
title: "Interactive Kaggle GPU Evaluation Notebook & Benchmark Telemetry"
area: competition/gemma-developer-agent
type: feature
milestone: 4
github_issue: 26
---

## 🎯 Task Objective
Create an interactive, production-grade Kaggle Notebook (`notebooks/gemma_agent_evaluation.ipynb`) running on 4x NVIDIA L4 GPUs with Kaggle Datasets integration, allowing interactive execution, live agent thought telemetry, Pass@1 calculation on SWE-bench validation samples, and patch diff visualizer before official leaderboard submission.

## 📋 Definition of Done
- [x] Create `notebooks/gemma_agent_evaluation.ipynb` with automated environment setup, GPU memory verification, and dataset mounting
- [x] Implement interactive execution cell running the agent on configurable SWE-bench problem instances
- [x] Add real-time telemetry visualizer displaying agent thoughts, tool calls, and pytest outputs per turn
- [x] Add automated Pass@1 resolution scoring against SWE-bench ground truth test suites
- [x] Implement export utility generating `submission.zip` directly from validated notebook runs
- [x] Write integration test validating notebook export and syntax compliance
