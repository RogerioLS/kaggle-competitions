---
name: reproducer_writer
description: Standard operating procedure for authoring minimal, deterministic SWE-bench issue reproduction scripts.
---

# Reproducer Writer Skill

## Objective
Author a minimal, isolated test script (e.g. `reproduce_issue.py` or a standalone `pytest` test case) that fails on the unmodified repository and passes once the correct patch is applied.

## Protocol
1. **Analyze Failure Conditions**: Extract the specific exception, unexpected return value, or assertion failure described in the problem statement.
2. **Minimize Dependencies**: Use only modules available in the repository virtual environment; avoid external network requests.
3. **Deterministic Assertion**: Structure the reproducer to exit with code `1` (or fail an assertion) when the bug is present, and exit with code `0` when fixed.
4. **Targeted Execution**: Execute via `run_command("python reproduce_issue.py")` or `run_command("pytest test_reproduce.py")` to verify reproduction before authoring the patch.
