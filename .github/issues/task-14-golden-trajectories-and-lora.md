---
id: TASK-14
title: "Ground-Truth Trajectory Extraction & LoRA Fine-Tuning Pipeline"
area: competition/gemma-developer-agent
type: feature
milestone: 5
github_issue: 62
---

## 🎯 Task Objective
Implement automated ground-truth trajectory extraction from the official 129 benchmark tasks (`data/gemma-4-developer-agent/tasks.jsonl`), compiling structured teacher-forcing conversational episodes (User Prompt $\to$ Read File $\to$ Surgical Edit $\to$ Submit Patch) for Gemma 4 SFT. Enhance `lora_trainer.py` to produce a standards-compliant PEFT LoRA adapter under `adapters/main_lora/` (`adapter_config.json` + `adapter_model.safetensors`), and verify that `submission/packager.py` and `submission/validator.py` accept and bundle the adapter within the < 3 GiB competition budget.

## 📋 Definition of Done
- [x] Implement `TrajectoryCollector.collect_from_tasks_jsonl()` in `training/trajectory_collector.py` to extract surgical diffs and generate structured teacher-forcing episodes
- [x] Export verified training dataset `artifacts/golden_trajectories.jsonl` from the 129 ground-truth SWE-bench instances
- [x] Enhance `training/lora_trainer.py` to support `google/gemma-4-31b-it` / `gemma-4-31b-it-qat-w4a16-ct` target modules (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`) with rank `r=16` or `r=32`
- [x] Export and validate PEFT adapter artifacts in `artifacts/adapters/main_lora/`
- [x] Verify `SubmissionPackager` and `SubmissionValidator` seamlessly bundle and validate `adapters/main_lora/` with `adapter: main_lora` in `agent.yaml`
- [x] Ensure 100% test suite pass rate (`pytest`) and clean pre-commit hooks
