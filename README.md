# 🛡️ Clean Chassis

[![CI & Quality Gate](https://github.com/RogerioLS/clean-chassis/actions/workflows/audit.yml/badge.svg)](https://github.com/RogerioLS/clean-chassis/actions/workflows/audit.yml)
[![Branch & Commit Gate](https://github.com/RogerioLS/clean-chassis/actions/workflows/branch_lint.yml/badge.svg)](https://github.com/RogerioLS/clean-chassis/actions/workflows/branch_lint.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: Flake8](https://img.shields.io/badge/flake8-100%20cols-brightgreen.svg)](https://flake8.pycqa.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Production-ready software chassis with strict governance, automated quality gates, continuous delivery, and zero-friction developer experience.**

---

## 🧭 Overview

**Clean Chassis** is an enterprise-grade repository blueprint and foundation designed for building mission-critical software, machine learning pipelines, and backend microservices.

It replaces repetitive repository setup with a battle-tested architecture featuring:
- 🛡️ **Two-Tier Quality Gates**: Local pre-commit git hooks coupled with strict GitHub Actions CI gates that auto-close non-compliant Pull Requests.
- 📐 **Conventional Governance**: Strict semantic commit formats (`<type>(<scope>): [<TASK-ID>:#<NUM>] <desc>`) linked to issue backlogs.
- 🎛️ **Zero-Friction Developer Experience**: A single command (`make install`) configures dependencies, git hooks, and displays an ANSI terminal onboarding guide.
- 🌐 **Static Asset & Documentation CDN**: Headless plot and report generation deployed automatically to GitHub Pages.
- 🤖 **Automated Release Bot**: Idempotent milestone-driven changelog updates and GitHub Release publication.

---

## 🏛️ Architecture & Directory Structure

```text
clean-chassis/
├── .github/                               # 🤖 CI/CD Workflows, Automations & Templates
│   ├── CODEOWNERS                         # Mandatory code review ownership
│   ├── dependabot.yml                     # Continuous dependency and Action security patches
│   ├── labeler.yml                        # Automated PR labeling based on modified paths
│   ├── pull_request_template.md           # Mandatory PR quality checklist
│   ├── release.yml                        # Semantic category mapping for GitHub releases
│   ├── ISSUE_TEMPLATE/                    # Structured Bug and Feature issue forms
│   ├── issues/                            # Markdown backlog for offline task tracking
│   └── workflows/                         # GitHub Actions pipelines (Audit, Branch Lint, Pages)
│
├── .githooks/                             # 🔒 Local Machine Git Hooks
│   ├── pre-commit                         # Runs formatters, linters, and norm auditors
│   └── commit-msg                         # Enforces conventional task commit formats
│
├── scripts/                               # ⚙️ Automation and Quality Gate Utilities
│   ├── lint_branch_and_commits.py         # Branch and commit validator with PR auto-close
│   ├── generate_summary.py                # Visual Markdown and JSON audit report builder
│   ├── release_bot.py                     # Idempotent release publisher
│   ├── rename_pr.py                       # Dynamic PR title updater
│   ├── update_pr_checklist.py             # Automated PR description checkbox updater
│   ├── update_issue_checklist.py          # Closes linked issues with state_reason: completed
│   └── install-hooks.sh                   # Hooks installer with ANSI onboarding banner
│
├── src/                                   # 🧠 Domain & Core Application Logic
│   └── core/
│       └── engine.py                      # Core computation engine example
│
├── tests/                                 # 🧪 Automated Test Suite (Zero-Regression)
│   ├── unit/                              # Isolated component tests
│   └── integration/                       # End-to-end execution pipeline tests
│
├── Makefile                               # 🎛️ Command Center (help, install, check, audit, test)
├── pyproject.toml                         # Unified tooling config (Black, Flake8, Ruff, Pytest)
├── CHANGELOG.md                           # Semantic version history (Keep a Changelog)
├── CONTRIBUTING.md                        # Collaboration guide and branch/commit conventions
├── CODE_OF_CONDUCT.md                     # Contributor Covenant Code of Conduct
├── SECURITY.md                            # Responsible disclosure security policy
└── LICENSE                                # MIT License
```

---

## 🚀 Quickstart: Using this Template in 3 Steps

### 1. Instantiate the Repository
Click the green **"Use this template"** button on GitHub to instantiate a new repository.

### 2. Run One-Command Setup
Clone your new repository and run:

```bash
make install
```

This single command:
- Upgrades `pip` and installs all development dependencies (`pytest`, `black`, `flake8`, `ruff`, `bandit`).
- Configures local Git hooks in `.githooks/` with executable permissions.
- Displays the colorful interactive onboarding card on your terminal.

### 3. Verify Quality Gates
Run the full project audit suite:

```bash
make audit
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

> [!IMPORTANT]
> The remote Quality Gate (`branch_lint.yml`) will automatically reject and **close** any Pull Request violating branch or commit formatting.

---

## ⚖️ License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
