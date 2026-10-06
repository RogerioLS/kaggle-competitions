---
id: TASK-03
github_issue: 8
title: "Local SWE-bench Evaluation Harness & Benchmark Sandbox"
area: competition/gemma-developer-agent
type: feature
milestone: 2
---

## 🎯 Task Objective
Build a reproducible local test harness that executes declarative agent configurations against public benchmark tasks in isolated sandboxes, running verification test suites to measure Pass@1 resolution rate.

## 📋 Definition of Done
- [x] Implement `competitions/gemma_developer_agent/evaluation/harness.py`
- [x] Create isolated workspace sandbox runner for applying patches and executing pytest/unittest
- [x] Implement scoring metrics: Pass@1, resolution rate, token budget, execution time
- [x] Add JSON/Markdown evaluation report generator with failed test case diagnostics
