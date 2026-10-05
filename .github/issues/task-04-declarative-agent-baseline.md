---
id: TASK-04
github_issue: 9
title: "Declarative Agent Architecture & Structured Prompts"
area: competition/gemma-developer-agent
type: feature
milestone: 2
---

## 🎯 Task Objective
Design and implement the baseline declarative `agent.yaml`, structured system prompts, specialized sub-agents (codebase navigator, bug locator, patch drafter, reviewer), and turn budgets for Gemma 4.

## 📋 Definition of Done
- [ ] Create `competitions/gemma-developer-agent/agent/agent.yaml`
- [ ] Author structured prompt templates under `competitions/gemma-developer-agent/prompts/`
- [ ] Implement sub-agent routing and task budget guardrails (`max_turns`, `timeout_seconds`)
- [ ] Benchmark baseline agent on development tasks using the local evaluation harness
