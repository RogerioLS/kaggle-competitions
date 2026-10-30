---
id: TASK-15
title: "Multi-File Surgery, Path Normalization & Submission v6.0 Preparation"
area: competition/gemma-developer-agent
type: feature
milestone: 5
github_issue: 66
---

## 🎯 Task Objective
Implement the 4 high-ROI, zero-risk surgical enhancements identified in the empirical gap analysis to advance from Public Score 0.17 towards 0.24+ (Leaderboard Top 1):
1. **Multi-File Surgical Coordination (14.7% of benchmark / 19 tasks)**: Extend `prompts/drafter.md` and `prompts/validator.md` to support editing up to 2 tightly coupled files before sealing `submit_patch`.
2. **Layout Normalization & Bidirectional Fallback (89.15% flat vs 10.85% `src/`)**: Prevent Turn 1 `FileNotFoundError` by implementing automatic reflexive lookup across flat and `src/` layouts in `prompts/explorer.md` and `prompts/locator.md`.
3. **Ultra-Fast Syntax Gatekeeper (`python3 -m py_compile`)**: Enforce a 0.2s pre-submission syntax validation check via `run_command` in `validator.md` before `submit_patch()` to eliminate `IndentationError` and syntax fatalities in Container B without pytest timeout risks.
4. **Symbolic AST Graph Prompting**: Teach `explorer.md` to supply exact symbol identifiers (`Session.send`, `HTTPAdapter`) to `search_similar_code` rather than natural language, unlocking the 22.5% of tasks outside the 18 hotspots.
5. **Packager and Submission v6.0 Preparation**: Generate candidate `artifacts/submission.zip` and validate 100% compliance via `SubmissionValidator`.

## 📋 Definition of Done
- [ ] Implement multi-file edit protocol (up to 2 files) in `prompts/drafter.md` and update `prompts/validator.md`
- [ ] Add bidirectional path fallback (`<pkg>/...` <-> `src/<pkg>/...`) in `prompts/explorer.md`, `locator.md`, and `system.md`
- [ ] Add lightweight syntax validation directive (`python3 -m py_compile`) in `prompts/validator.md`
- [ ] Calibrate `prompts/explorer.md` to instruct AST symbol queries on `search_similar_code`
- [ ] Verify test suite passes cleanly with 0 regressions (`pytest`)
- [ ] Validate generated v6.0 package via `SubmissionValidator`
- [ ] Synchronize `PROJECT_STATUS.md` and `README.md`
