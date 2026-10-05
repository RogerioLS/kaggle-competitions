# 05 — Antigravity Agent Workflow

## Standard Operational Lifecycle
For every task or feature:
1. **Load Context**: Read `.agents/AGENTS.md`, relevant rules, and task specification.
2. **Inspect**: Check current repository files, git status, and existing tests.
3. **Plan**: Formulate a clear, minimal step-by-step implementation.
4. **Implement**: Write clean, modular, typed code adhering to repository standards.
5. **Validate Locally**: Run `make check`, `make test`, and competition evaluation harness.
6. **Commit with Governance**: Commit adhering to Conventional Commits: `<type>(<scope>): [<TASK-ID>] <desc>`.
