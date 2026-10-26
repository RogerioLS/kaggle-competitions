---
name: reproducer_writer
description: Standard operating procedure for running inline, zero-pollution SWE-bench issue reproductions.
---

# Reproducer Writer Skill

## CRITICAL OUTPUT RULE — ZERO CONVERSATIONAL CHATTER
- **DO NOT CHAT.** Emit ONLY a single ` ```json ... ``` ` action block per turn.
- **DO NOT WRITE UNTRACKED FILES TO DISK.** Never use `write_file` to create `reproducer.py`, `reproduce_issue.py`, or `test_reproduce.py`, because untracked files pollute `git diff` and invalidate the SWE-bench patch.

## Protocol
1. **Inline Reproduction Only**: If you need to reproduce the bug or verify a fix, execute a one-liner via `run_command` using `python3 -c "..."` or run a single existing test file (`pytest path/to/test_file.py -k test_name`).
2. **Never Run Full Test Suites**: Never run `pytest` across the entire `tests/` directory, as it will time out before `submit_patch` can be called.
3. **Prioritize Patch & Submission**: As soon as you identify the root cause in the source file, apply the fix with `edit_file` and immediately call `submit_patch`.

## Few-Shot Tool Calling Example
```json
{
  "thought": "Verify the fix in requests/models.py using an inline python3 -c one-liner without creating untracked files.",
  "sub_agent": "validator",
  "tool": "run_command",
  "arguments": {
    "command": "python3 -c \"import requests; print('verified')\""
  }
}
```
