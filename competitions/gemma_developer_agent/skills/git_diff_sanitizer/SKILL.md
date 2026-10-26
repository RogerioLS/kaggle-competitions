---
name: git_diff_sanitizer
description: Standard operating procedure for formatting, cleaning, and sanitizing git diff patches prior to submission.
---

# Git Diff Sanitizer Skill

## CRITICAL OUTPUT RULE — ZERO CONVERSATIONAL CHATTER
- **DO NOT CHAT.** Emit ONLY a single ` ```json ... ``` ` action block per turn.
- **ALWAYS CALL `submit_patch` IMMEDIATELY AFTER EDITING.** Once `edit_file` succeeds on the target source file, your very next action MUST be `submit_patch` with `{}`.

## Protocol
1. **Remove Ephemeral Artifacts**: Never leave `reproducer.py`, `reproduce_issue.py`, or `test_reproduce.py` in the working tree. If any temporary file was created, remove it via `run_command("rm -f reproducer.py reproduce_issue.py test_reproduce.py")` before calling `submit_patch`.
2. **Surgical Source Edits Only**: Verify only source files directly addressing the issue are modified.
3. **Immediate Submission**: Call `submit_patch` before turn or timeout budgets expire.

## Few-Shot Tool Calling Example
```json
{
  "thought": "The surgical fix in requests/models.py is complete and workspace is clean. Calling submit_patch now.",
  "sub_agent": "validator",
  "tool": "submit_patch",
  "arguments": {}
}
```
