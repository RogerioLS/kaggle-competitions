# 06 — Git & Software Governance

## Two-Tier Quality Gates
- **Branch Format**: `<type>/<task-id>-<description>` (e.g. `feat/task-01-agent-harness`).
- **Commit Format**: `<type>(<scope>): [<TASK-ID>:#<NUM>] <desc>` or `[<RESERVED_TAG>]`.
  - Reserved Tags: `[INFRA]`, `[CHORE]`, `[DOCS]`, `[FIX]`, `[CONFIG]`, `[SECURITY]`.
- **Pre-commit Checks**: Run `make check` before attempting to commit.
- **Audit Verification**: Run `make audit` prior to pushing or opening a Pull Request.
