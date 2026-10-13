---
id: TASK-05
github_issue: 10
title: "Kaggle Submission Pipeline, Validator & Dry-Run"
area: competition/gemma-developer-agent
type: feature
milestone: 3
---

## 🎯 Task Objective
Implement an automated build target (`make package-submission`) that validates `submission.zip` compliance (root `agent.yaml`, offline constraints, absence of raw Python entrypoints) and verifies dry-run execution.

## 📋 Definition of Done
- [x] Implement `competitions/gemma-developer-agent/submission/packager.py`
- [x] Build submission validator ensuring offline compatibility, file structure, and size limits
- [x] Add `make package-submission` and `make verify-submission` Makefile targets
- [x] Execute successful dry-run producing a validated `submission.zip`
