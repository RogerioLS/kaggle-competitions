---
id: TASK-11
title: "Submission v3.0 Prompt Hardening, Budget Calibration & Resilient JSON Parser"
area: competition/gemma-developer-agent
type: feature
milestone: 4
github_issue: 50
---

## 🎯 Task Objective
Eliminate conversational chatter, git diff pollution (`reproducer.py`), sub-agent turn/timeout bottlenecks before `submit_patch`, and `JSONDecodeError` failures caused by unescaped inner quotes (`hasattr(data, "read")`) across all declarative prompts, sub-agent configs, skills, and the ReAct parser.

## 📋 Definition of Done
- [x] Harden all 5 agent prompts (`system.md`, `explorer.md`, `locator.md`, `drafter.md`, `validator.md`) and 2 skills (`reproducer_writer`, `git_diff_sanitizer`) with `ZERO CONVERSATIONAL CHATTER`, `JSON QUOTE ESCAPING RULE`, and valid Few-Shot JSON tool-calling examples
- [x] Calibrate sub-agent turn budgets, timeouts, and tool permissions (`submit_patch` enabled in `locator`, `drafter`, and `validator`) and set deterministic sampling (`temperature: 0.1`, `top_p: 0.90`, `max_tokens_per_turn: 4096`)
- [x] Implement automatic sanitization of temporary scripts (`reproducer.py`, `reproduce_issue.py`, `test_reproduce.py`) in `DeclarativeAgentRunner._tool_submit_patch()`
- [x] Implement `ReActParser._load_json_resilient()` with iterative quote/newline repair and regex key-boundary fallback extraction
- [x] Validate 100% Pass@1 resolution on `requests_7505` (3 turns, 132.39s) and `requests_7502` (3 turns, 142.23s) on Kaggle 4x NVIDIA L4 GPUs
