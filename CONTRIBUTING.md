# 🤝 Contributing to Kaggle Competitions Hub

Thank you for your interest in the **Kaggle Competitions Portfolio & AI Engineering Hub**! We uphold rigorous software engineering standards, automated quality gates, and structured Git Submodule governance.

---

## 🚀 Quickstart & Environment Setup

Clone the repository with submodules and configure local git hooks:

```bash
# 1. Clone repository with submodules
git clone --recurse-submodules git@github.com:RogerioLS/kaggle-competitions.git
cd kaggle-competitions

# 2. Configure local git hooks and view onboarding commands
make install
make help
```

---

## 🌿 Branch Naming Convention

Every feature, fix, or chore must be developed in a dedicated branch adhering to the standard format:

```text
<type>/<task-id>-<description-in-kebab-case>
or: <type>/<description-in-kebab-case>
```

- **Allowed Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `hotfix`, `release`
- **Valid Examples**:
  - `feat/register-02-kaggle-nfl-big-data-bowl`
  - `fix/submodule-pointer-drift`
  - `chore/update-dependabot-schedule`

> [!CAUTION]
> Pull Requests originating from branches violating this format will be **automatically closed by CI**.

---

## 📝 Conventional Task Commits

Commits must follow the Conventional Commits specification with approved reserved tags:

```text
<type>(<scope>): [<TASK-ID>:#<ISSUE_NUM>] <description>
or: <type>(<scope>): [<TASK-ID>] <description>
or: <type>(<scope>): [<RESERVED_TAG>] <description>
```

- **Valid Examples**:
  - `feat(hub): [INFRA] register 02_kaggle-nfl-big-data-bowl submodule`
  - `fix(sync): [INFRA] repair detached HEAD during automated submodule update`
  - `docs(readme): [DOCS] update competition index table with bronze medal badge`
  - `chore(deps): [CHORE] bump pytest to latest version`

- **Reserved Global Tags**: `[INFRA]`, `[CHORE]`, `[DOCS]`, `[FIX]`, `[HOTFIX]`, `[GLOBAL]`, `[CONFIG]`, `[SECURITY]`, `[RELEASE]`.

---

## 🏆 Registering a New Competition

### Method 1: Autonomous Discovery (Recommended)
```bash
make discover ARGS="--auto-merge"
```

### Method 2: Explicit Registration
```bash
make add ARGS="--repo kaggle-new-challenge --title 'New Challenge' --task 'NLP / Agents'"
```

---

## 🧪 Quality Gate & Test Verification

Before pushing changes, verify that all linters and tests pass locally:

```bash
# Check code style, syntax, and run tests
make check
make test

# Generate summary audit report with cyberpunk badge
make summary
```
