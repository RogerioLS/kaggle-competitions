# 🤝 Contributing to Clean Chassis

Thank you for your interest in contributing to **Clean Chassis**! We enforce strict software engineering governance to ensure high-performance, maintainable, and reliable software.

---

## 🚀 Quickstart & Local Setup

Clone the repository and run the automated setup command:

```bash
# 1. Install development dependencies and configure local git hooks
make install

# 2. View available commands and best practices
make help
make onboarding
```

---

## 🌿 Branch Naming Convention

Every feature, fix, or chore must be developed in a dedicated branch adhering to the institutional format:

```text
<type>/<task-id>-<description-in-kebab-case>
or: <type>/<description-in-kebab-case>
```

- **Allowed Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `hotfix`, `release`
- **Valid Examples**:
  - `feat/task-01-core-engine`
  - `fix/auth-02-expired-token`
  - `chore/infra-setup-ci`

> [!CAUTION]
> Pull Requests originating from branches violating this format will be **automatically closed by CI**.

---

## 📝 Conventional Task Commits

Commits must follow the Conventional Commits specification, tagged with the associated task ID:

```text
<type>(<scope>): [<TASK-ID>:#<ISSUE_NUM>] <description in lowercase>
or: <type>(<scope>): [<TASK-ID>] <description in lowercase>
or: <type>(<scope>): [<RESERVED_TAG>] <description in lowercase>
```

- **Valid Examples**:
  - `feat(core): [TASK-01:#1] implement core calculation engine`
  - `fix(engine): [TASK-01:#1] handle empty dataset exception`
  - `chore(ci): [INFRA] configure pre-commit hooks and workflows`
  - `docs(readme): [DOCS] update quickstart instructions`

- **Reserved Global Tags**: `[INFRA]`, `[CHORE]`, `[DOCS]`, `[FIX]`, `[HOTFIX]`, `[GLOBAL]`, `[CONFIG]`, `[SECURITY]`, `[RELEASE]`.

---

## 🧪 Local Quality Gate Verification

Before committing, ensure that all linters and tests pass locally:

```bash
# Run linters (Black, Isort, Flake8, Ruff)
make check

# Run full test suite and compile checks
make test
make audit
```
