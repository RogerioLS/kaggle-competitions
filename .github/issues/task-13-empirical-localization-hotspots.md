---
id: TASK-13
title: "Empirical Hotspot Priors, Localization & Surgical Resiliency"
area: competition/gemma-developer-agent
type: feature
milestone: 5
github_issue: 60
---

## 🎯 Task Objective
Ground agent prompts (`prompts/explorer.md`, `prompts/locator.md`, `prompts/drafter.md`, `prompts/system.md`) and sub-agent configs in the empirical findings from all 129 SWE-bench tasks (`data/gemma-4-developer-agent/tasks.jsonl`), directly addressing the 92.2% localization bottleneck by injecting target hotspot priors for FastAPI (86.6% in 6 files, 40.3% in `fastapi/dependencies/utils.py`), Rich (64.6% in 8 files), and Requests (84.6% in 4 files). Calibrate `eval_config.yaml` execution budgets (`max_tool_calls: 35`, `max_turns: 40`, `max_time_minutes: 7`) and enforce resilient surgical re-reading on `edit_file` failures.

## 📋 Definition of Done
- [x] Inject repository-specific hotspot priors into `prompts/explorer.md` and `prompts/locator.md` so the agent checks high-probability files when domain keywords are detected
- [x] Enforce surgical editing and re-reading protocol in `prompts/drafter.md`: if `edit_file` reports `String not found`, immediately call `read_file` to re-fetch exact line context instead of guessing whitespace
- [x] Calibrate `competitions/gemma_developer_agent/agent/eval_config.yaml` to raise `max_tool_calls` to 35, `max_turns` to 40, and `max_time_minutes` to 7
- [x] Verify that all 123 tests in `tests/` pass cleanly (`pytest`)
- [x] Regenerate `artifacts/submission.zip` (v5.0 candidate) and validate via `SubmissionValidator` (0 errors, 100% compliant)
- [x] Update `PROJECT_STATUS.md` and `README.md` upon completion
