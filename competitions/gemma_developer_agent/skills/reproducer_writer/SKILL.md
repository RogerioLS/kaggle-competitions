---
name: reproducer_writer
description: Standard Operating Procedure for verifying defects using targeted tests or inline commands without polluting the git workspace.
---

# Skill: Minimal Defect Verification (`reproducer_writer`)

## Critical Rule
- **DO NOT CHAT**: Invoke tools directly without conversational filler.
- **NEVER create untracked files in `/workspace`** (such as `/workspace/reproducer.py` or `test_reproduce.py`), because `submit_patch` runs `git add -N . && git diff HEAD` inside `/workspace`.

## Verification Protocol
1. **Prefer Targeted Existing Tests or Inline One-Liners**:
   - Run a specific test node via `run_command`: `pytest tests/test_module.py -k test_function -q`
   - Or run an inline Python check via `run_command`: `python3 -c "import requests; ..."`
   - If you must write a temporary script, write it ONLY to `/tmp/repro.py` via `run_command`.
2. **Never Run Full-Repo Test Suites**:
   - Never run bare `pytest` or `pytest .` without a target file path.
