---
id: TASK-12
title: "Submission v4.0 Official swegemma & adk-submission Contract Alignment"
area: competition/gemma-developer-agent
type: feature
milestone: 4
github_issue: 53
---

## 🎯 Task Objective
Align the `submission.zip` declarative agent configuration (`agent.yaml`, `eval_config.yaml`, `configs/sampling.yaml`, `sub_agents/*.yaml`, and `prompts/*.md`) with the official `swegemma` + `adk-submission` (`SandboxedAgentConfig`) evaluation harness contract and native vLLM `gemma4` tool-calling parser (`<|tool_call>`), resolving the root cause of the 14-hour `0.00` public leaderboard score while preserving 100% compatibility with our local Notebook and unit test suite.

## 📋 Definition of Done
- [x] Align `agent.yaml` with `adk-submission` (`SandboxedAgentConfig`) schema: `instruction: !include prompts/system.md`, explicit root `tools:` list (`run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, `get_code_neighbors`, `search_similar_code`, `get_code_subgraph`), `agent_tool` entries with `skip_summarization: true`, and `generate_content_config: !include configs/sampling.yaml`
- [x] Add `eval_config.yaml` at the root of `submission.zip` (via `SubmissionPackager`) with calibrated `evaluation:` budgets (`timeout_seconds`, `max_tool_calls`, `max_time_minutes`, `max_turns`) to prevent 14-hour timeout loops on the Kaggle evaluator
- [x] Align `configs/sampling.yaml` with Google ADK `GenerateContentConfig` (`temperature`, `top_p`, `max_output_tokens: 16384`, `thinking_config: {thinking_budget: 4096, include_thoughts: true}`)
- [x] Update `prompts/system.md` and `prompts/*.md` to use native ADK/vLLM tool calling (`tool_call_parser="gemma4"`) instead of forcing raw markdown ```` ```json ``` ```` text blocks that trigger `turn_has_tool_call == False` and 3 continuation nudges in `swegemma`
- [x] Update `AgentConfig.from_yaml()` (`schema.py`) and `SubmissionValidator` (`validator.py`) to natively parse `!include` YAML tags and validate both the official `adk-submission` contract and `eval_config.yaml`
- [x] Verify 100% test suite pass rate (`pytest` + `make audit`) and regenerate `gemma_agent_evaluation.ipynb` and `artifacts/submission.zip`
