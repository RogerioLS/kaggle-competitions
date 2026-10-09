# 🏆 Kaggle Competitions Hub & Arena

[![CI & Quality Gate](https://github.com/RogerioLS/kaggle-competitions/actions/workflows/audit.yml/badge.svg)](https://github.com/RogerioLS/kaggle-competitions/actions/workflows/audit.yml)
[![Branch & Commit Gate](https://github.com/RogerioLS/kaggle-competitions/actions/workflows/branch_lint.yml/badge.svg)](https://github.com/RogerioLS/kaggle-competitions/actions/workflows/branch_lint.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: Flake8](https://img.shields.io/badge/flake8-100%20cols-brightgreen.svg)](https://flake8.pycqa.org/)
[![Linter: Ruff](https://img.shields.io/badge/linter-ruff-red.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Enterprise-grade monorepo for competitive machine learning, autonomous agent engineering, and quantitative modeling with strict MLOps governance, local test harnesses, and automated submission pipelines.**

---

## 🧭 Overview

**Kaggle Competitions Hub** is an institutional development and experimentation platform designed for elite competitive machine learning and AI agent challenges.

Built on the foundation of **Clean Chassis**, it enforces high-performance engineering standards:
- 🛡️ **Two-Tier Quality Gates**: Local pre-commit git hooks coupled with strict GitHub Actions CI gates that validate style, syntax, security, and conventions.
- 🤖 **Agent Operating System (`.agents/`)**: Protocol-driven AI coding agents with specialized skills, rules, and evaluation harnesses.
- 📐 **Conventional Governance**: Strict semantic commit formats (`<type>(<scope>): [<TASK-ID>:#<NUM>] <desc>`) linked to issue backlogs.
- 🎛️ **Zero-Friction Developer Experience**: A single command (`make install`) configures dependencies, git hooks, and displays an onboarding guide.
- 📦 **Reproducible Submission Pipelines**: Automated validation, test harness verification, and packaging for Kaggle leaderboard submissions.

---

## 🎯 Active Competitions

| Competition | Domain / Focus | Stack | Status | Target / Prize |
| :--- | :--- | :--- | :---: | :--- |
| **[Google - The Gemma 4 Developer Agent](competitions/gemma_developer_agent)** | Autonomous Software Engineering Agents (SWE-bench) | Gemma 4 31B, ADK, LoRA, Python | 🟢 Active | Dec 02, 2026 ($100k) |
| **[NFL Big Data Bowl 2027](https://www.kaggle.com/competitions/nfl-big-data-bowl-2027)** | Combine Sensor Tracking to NFL Performance | Polars, Spatio-Temporal 10Hz, Python | ⚪ Planned | Jan 06, 2027 ($100k) |
| **Enveda CASMI 2026** | Mass Spectrometry / Signal Modeling | PyTorch, Spectral Graph Nets | ⚪ Planned | Dec 14, 2026 ($50k) |

---

## 🏛️ Architecture & Directory Structure

```text
kaggle-competitions/
├── .agents/                               # 🤖 Institutional Agent Operating System
│   ├── AGENTS.md                          # Master agent operating protocol & routing layer
│   ├── rules/                             # Architectural & engineering guardrails (00 to 07)
│   └── skills/                            # Specialized agent capabilities & personas
│
├── .github/                               # 🤖 CI/CD Workflows, Automations & Templates
│   ├── CODEOWNERS                         # Mandatory code review ownership
│   ├── dependabot.yml                     # Continuous dependency and Action security patches
│   ├── labeler.yml                        # Automated PR labeling based on modified paths
│   ├── pull_request_template.md           # Mandatory PR quality checklist
│   ├── release.yml                        # Semantic category mapping for GitHub releases
│   ├── ISSUE_TEMPLATE/                    # Structured Bug and Feature issue forms
│   ├── issues/                            # Markdown backlog for offline task tracking
│   └── workflows/                         # GitHub Actions pipelines (Audit, Branch Lint)
│
├── .githooks/                             # 🔒 Local Machine Git Hooks
│   ├── pre-commit                         # Runs formatters, linters, and norm auditors
│   └── commit-msg                         # Enforces conventional task commit formats
│
├── competitions/                          # 🏆 Isolated Competition Modules
│   └── gemma-developer-agent/             # Google Gemma 4 Developer Agent challenge
│       ├── README.md                      # Competition rules, baseline, metrics
│       ├── agent/                         # Agent specification (agent.yaml, tools, runner)
│       ├── prompts/                       # System prompts, few-shot examples, personas
│       ├── evaluation/                    # Local SWE-bench style harness & benchmark runner
│       ├── training/                      # LoRA / QLoRA fine-tuning scripts
│       └── submission/                    # Packaging scripts for submission.zip
│
├── src/                                   # 🧠 Shared MLOps & Competition Engineering Logic
│   ├── common/
│   │   ├── kaggle_client.py               # Kaggle API wrapper for datasets and submissions
│   │   ├── metrics.py                     # Generic scoring and evaluation metrics
│   │   └── utils.py                       # I/O, seed fixing, and environment helpers
│   └── core/
│       └── engine.py                      # Core computation engine
│
├── scripts/                               # ⚙️ Automation and Quality Gate Utilities
│   ├── lint_branch_and_commits.py         # Branch and commit validator with PR auto-close
│   ├── generate_summary.py                # Visual Markdown and JSON audit report builder
│   ├── release_bot.py                     # Idempotent release publisher
│   └── install-hooks.sh                   # Hooks installer with ANSI onboarding banner
│
├── tests/                                 # 🧪 Automated Test Suite (Zero-Regression)
│   ├── unit/                              # Isolated component tests
│   └── integration/                       # End-to-end execution pipeline tests
│
├── Makefile                               # 🎛️ Command Center (help, install, check, audit, test)
├── pyproject.toml                         # Tooling config (Black, Flake8, Ruff, Pytest, Bandit)
├── CHANGELOG.md                           # Semantic version history (Keep a Changelog)
├── CONTRIBUTING.md                        # Collaboration guide and branch/commit conventions
├── CODE_OF_CONDUCT.md                     # Contributor Covenant Code of Conduct
├── SECURITY.md                            # Responsible disclosure security policy
└── LICENSE                                # MIT License
```

---

## 🚀 Quickstart: Setup in 3 Steps

### 1. Run One-Command Setup
Clone your repository and run:

```bash
make install
```

This single command:
- Upgrades `pip` and installs all development and competition dependencies.
- Configures local Git hooks in `.githooks/` with executable permissions.
- Displays the interactive onboarding banner.

### 2. Verify Quality Gates
Run the full project audit suite:

```bash
make audit
```

### 3. Kaggle API Configuration
Place your `kaggle.json` credentials in `~/.kaggle/kaggle.json` or project root (git-ignored) with:
```bash
chmod 600 ~/.kaggle/kaggle.json
```

---

## 🎛️ Command Center (`Makefile`)

| Command | Purpose |
|---|---|
| `make help` | Interactive color-coded CLI menu of all targets |
| `make onboarding` | Display best practices & Git governance banner |
| `make install` | Install dev dependencies and configure local git hooks |
| `make test` | Run all unit and integration test suites via Pytest |
| `make check` | Run pre-commit linters (Black, Isort, Flake8 100 cols, Ruff) |
| `make audit` | Full audit: syntax + linters + unit tests + Bandit scan |
| `make summary` | Generate visual audit report (`summary.md`) |
| `make clean` | Remove temporary caches, build artifacts, and coverage files |

---

## 🌿 Git Governance & Quality Gates

### Branch Naming Convention
Branches must adhere to the format:
```text
<type>/<task-id>-<description-in-kebab-case>
or: <type>/<description-in-kebab-case>
```
*Allowed Types*: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `hotfix`, `release`.  
*Examples*: `feat/task-01-core-engine`, `fix/auth-02-expired-token`, `chore/infra-ci`.

### Conventional Task Commits
Commits must specify the type, optional scope, and task identifier:
```text
<type>(<scope>): [<TASK-ID>:#<ISSUE_NUM>] <description>
or: <type>(<scope>): [<TASK-ID>] <description>
or: <type>(<scope>): [<RESERVED_TAG>] <description>
```
*Examples*:
- `feat(core): [TASK-01:#1] implement core calculation engine`
- `fix(engine): [TASK-01:#1] handle zero division error`
- `chore(ci): [INFRA] update github actions versions`

---

## ⚖️ License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
