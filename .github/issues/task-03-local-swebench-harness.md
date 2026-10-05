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
- [ ] Implement `competitions/gemma-developer-agent/evaluation/harness.py`
- [ ] Create isolated workspace sandbox runner for applying patches and executing pytest/unittest
- [ ] Implement scoring metrics: Pass@1, resolution rate, token budget, execution time
- [ ] Add JSON/Markdown evaluation report generator with failed test case diagnostics
