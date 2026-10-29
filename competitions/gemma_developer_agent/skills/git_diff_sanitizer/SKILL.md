---
name: git_diff_sanitizer
description: Pre-submission checklist to guarantee clean unified diffs and immediate patch submission via submit_patch.
---

# Skill: Git Diff Sanitizer (`git_diff_sanitizer`)

## Critical Rule
- **DO NOT CHAT**: Invoke tools directly without conversational filler.

## Pre-Submission Checklist
1. **No Untracked Scratch Files in `/workspace`**:
   - Ensure no temporary scripts exist in `/workspace` (use `/tmp` for any scratch files, or remove untracked files in `/workspace` before calling `submit_patch`).
2. **No Modifications to Protected Test or Config Files**:
   - Never modify `tests/*`, `test_*.py`, `*_test.py`, `/workspace/pytest.ini`, `/workspace/conftest.py`, or `pyproject.toml`.
3. **Seal the Patch Immediately**:
   - Call `submit_patch` as your final action (`submit_patch` is free and does not count toward `max_tool_calls`) and verify `patch_size > 0` and `files_changed > 0`.
