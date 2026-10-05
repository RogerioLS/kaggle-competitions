# AGENTS.md — Institutional Agent Operating System

**Project:** kaggle-competitions  
**Domain:** Competitive Machine Learning & Autonomous Agent Engineering  
**Primary Focus:** Google - The Gemma 4 Developer Agent Competition ($100k)  
**Purpose:** Master operating protocol for AI agents working in this repository  
**Version:** 1.0  

---

# 0. Why This File Exists

This file is the repository-level operating protocol for AI coding agents.

It is not a motivational persona.  
It is not a duplicate of every rule, README, or skill.  

It is the routing layer that tells an agent:
- what this project is;
- where the truth lives;
- how to discover the current state;
- which documents to read before acting;
- which skills and rules to load;
- how to use the evaluation harness;
- how to avoid false assumptions;
- how to complete work without breaking repository quality gates.

The repository is the source of truth.  
Chat history is not the source of truth.  
Human memory is not the source of truth.  
Agent memory is not the source of truth.  

---

# 1. Institutional Identity

You are operating inside an institutional competitive ML and agent engineering platform.

Your job is not merely to write quick scripts or produce messy notebook code.  
Your job is to preserve the engineering integrity of the platform while advancing toward winning competitive solutions.

- **Rigor over haste**: A disciplined, reproducible baseline beats an unverified hack.
- **Harness-driven development**: No model or agent configuration is considered improved until validated against the local benchmark harness.
- **Clean Chassis Governance**: Every commit, branch, and module must pass two-tier quality gates (`make check`, `make audit`).
- **Offline & Submission Readiness**: All competition artifacts must adhere strictly to Kaggle compute, time, and offline constraints.

---

# 2. Monorepo Architecture & Isolation

The platform organizes multiple competitive challenges under a unified MLOps backbone:

```text
kaggle-competitions/
├── .agents/                 # Master operating protocol, rules, skills, and harness specs
├── .github/                 # Quality gates (audit, branch lint, issue backlog)
├── .githooks/               # Local pre-commit & commit-msg hooks
├── src/common/              # Shared utilities (Kaggle API, logging, metrics, seeds)
└── competitions/            # Completely isolated competition workspaces
    └── gemma-developer-agent/ # Current primary focus
```

### Isolation Rules:
1. **Competition Isolation**: Code specific to a competition (e.g. `competitions/gemma-developer-agent/`) must never import directly from another competition directory.
2. **Shared Code Discipline**: Code in `src/common/` must be general, battle-tested, fully typed, and covered by unit tests in `tests/`.
3. **Artifact Segregation**: Big weights, datasets, and zip artifacts must remain git-ignored and never committed.

---

# 3. Local Evaluation Harness Protocol

A competition is won or lost by the quality and correlation of the local validation harness:

1. **Zero Leakage**: Never evaluate on data that was used in training, prompt tuning, or few-shot exemplars.
2. **SWE-bench Style Harness**: For agent competitions (like Gemma 4), evaluation occurs in isolated execution sandboxes running test suites (PASS/FAIL verification).
3. **Reproducibility**: All harness runs must log git commit SHA, timestamp, seed, duration, and full trace output.
4. **Offline Parity**: The local evaluation environment must simulate Kaggle runtime constraints (timeout, CPU/GPU memory, offline networking).

---

# 4. Active Competition: Google Gemma 4 Developer Agent

- **Goal**: Build an autonomous coding agent powered by Gemma 4 31B that resolves real-world GitHub issues (SWE-bench style).
- **Format**: `submission.zip` containing `agent.yaml`, `prompts/`, `sub_agents/`, `skills/`, and optional adapters.
- **Runtime Environment**: Kaggle L4x4 GPUs (96GB VRAM), CPU mode fallback, strictly offline during evaluation.
- **Evaluation Metric**: Percentage of test suites resolved (Pass@1).

---

# 5. Two-Tier Quality Gates (Clean Chassis)

Every change must satisfy:
1. **Local Pre-commit Hook**:
   - `black` (100 cols)
   - `isort`
   - `flake8` (100 cols)
   - `ruff`
   - `bandit`
2. **Commit Message Gate**:
   - Format: `<type>(<scope>): [<TASK-ID>:#<NUM>] <desc>` or `<type>(<scope>): [<TASK-ID>] <desc>` or `<type>(<scope>): [<RESERVED_TAG>] <desc>`
3. **Branch Name Gate**:
   - Format: `<type>/<task-id>-<description>` or `<type>/<description>`
4. **CI Remote Gate**:
   - GitHub Actions runs `make audit` and `scripts/lint_branch_and_commits.py`.

---

# 6. Rules Routing Layer

Before acting, consult the rules in `.agents/rules/`:
- `00_global_rules.md`: Foundational principles and separation of concerns.
- `01_competition_architecture.md`: Folder boundaries and monorepo structure.
- `02_clean_code_python.md`: Python standards (types, docstrings, formatting).
- `03_minimalism_and_iteration.md`: Speed, lean designs, incremental progress.
- `04_evaluation_harness_and_leakage.md`: Local validation, zero leakage, test sandboxing.
- `05_antigravity_agent_workflow.md`: Standard 10-step agent operational flow.
- `06_git_and_governance.md`: Branches, conventional commits, quality gates.
- `07_submission_integrity.md`: Packaging `submission.zip`, offline verification, runtime limits.

---

# 7. Skills Routing Layer

When executing specialized tasks, invoke the corresponding skill under `.agents/skills/`:
- `competition-orchestrator`: Backlog, milestone, and roadmap planning.
- `gemma-agent-engineer`: Agent architecture, system prompt design, tools, sub-agents.
- `harness-and-evaluator`: Benchmark sandbox, test runner, scoring metrics.
- `submission-guard`: Package validation, zip inspection, offline test runner.
- `code-quality-auditor`: Running linters, security scanners, and test suites.

---

# 8. Operational Guardrails

- Never push code that breaks `make check` or `make audit`.
- Never submit a zip to Kaggle without prior verification through the local evaluation harness.
- Never commit sensitive tokens or credentials (`kaggle.json`, API keys).
- Always document experimental results with exact seeds and commit hashes.
