# 🤖 Google - The Gemma 4 Developer Agent Competition

- **Track 1:** Featured Prediction Competition ($65,000 USD)
- **Track 2:** Paper Track ($35,000 USD, NeurIPS Expo workshop showcase)
- **Total Prize Pool:** $100,000 USD
- **Deadline:** December 02, 2026 (Entry & Merger: Nov 25, 2026)

---

## 🎯 Competition Objective
Post-train an open model (**Gemma 4 31B**) into an autonomous software engineering agent capable of navigating complex codebases and drafting reliable fixes for real-world software engineering issues (SWE-bench benchmark style).

The key thesis is enabling high-performance coding agents that can run **offline on consumer-grade hardware** (tested on 4x NVIDIA L4 GPUs in Kaggle).

---

## 📦 Submission Format & Rules
1. **Declarative Architecture Only**:
   - Submissions **must not** contain raw Python entrypoints (e.g. `agent.py` is disallowed).
   - The Kaggle environment parses submissions with a **sandboxed YAML compiler**.
   - The archive must be named `submission.zip` with `agent.yaml` at the root.
2. **Components in `submission.zip`**:
   - `agent.yaml`: Master configuration declaring agent personas, tools, sub-agents, and limits.
   - `prompts/`: System prompts, role instructions, and few-shot exemplars (e.g. `prompts/system.md`).
   - `configs/`: Runtime settings (e.g. `sampling.yaml`).
   - `adapters/`: Optional LoRA adapter weights if fine-tuning is used.
3. **Environment Tools Available in Sandbox**:
   - `run_command`: Execute shell commands inside the container sandbox.
   - `edit_file`: Patch and modify source files.
   - `submit_patch`: Finalize git patch and submit solution.
   - Code graph search & embedding navigation tools.
4. **Constraints**:
   - Strictly **OFFLINE** during evaluation.
   - Maximum execution budget per task: `timeout_seconds` and `max_turns`.

---

## 🗺️ Engineering Roadmap
- **[TASK-02]**: Kit ingestion, 129 public development tasks setup.
- **[TASK-03]**: Local SWE-bench evaluation harness & scoring sandbox.
- **[TASK-04]**: Declarative `agent.yaml` baseline and persona prompts.
- **[TASK-05]**: Automated `submission.zip` packaging and dry-run validator.
- **[TASK-06]**: Gemma 4 LoRA fine-tuning on high-signal trajectories.
