---
id: TASK-09
title: "Gemma 4 Autonomous ReAct Engine & Dynamic Tool-Calling Loop"
area: competition/gemma-developer-agent
type: feature
milestone: 4
---

## 🎯 Task Objective
Implement the core autonomous reasoning engine (`inference_engine.py`, `react_orchestrator.py`) enabling Gemma 4 31B to analyze SWE-bench problem statements, dynamically select and call tools (`search_similar_code`, `read_file`, `edit_file`, `write_file`, `run_command`), interpret terminal feedback (tracebacks, pytest outputs), and iterate in a closed loop until the bug is verified and a git diff patch is submitted.

## 📋 Definition of Done
- [x] Implement `competitions/gemma_developer_agent/agent/inference_engine.py` supporting Gemma 4 prompt formatting (`<start_of_turn>user` / `model`) and offline execution
- [x] Implement `competitions/gemma_developer_agent/agent/react_orchestrator.py` with robust JSON tool-call parsing, turn budget tracking, and error recovery
- [x] Integrate closed-loop verification: test reproducer execution (`pytest reproducer.py`) and dynamic feedback feeding into the conversation
- [x] Update `DeclarativeAgentRunner` in `runner.py` and `kaggle_kernel.py` to route through the autonomous ReAct engine
- [x] Write comprehensive unit tests covering prompt formatting, action parsing, tool execution, and simulated multi-turn bug resolution
- [x] Document the end-to-end decision loop and state machine in competition README
