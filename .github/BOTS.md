# 🤖 Automated Bots & System Collaborators Manifest

This repository uses automated bots to maintain continuous integration, issue synchronization, dependency governance, and software quality gates.

---

## 1. 📋 GitHub Actions Bot (`@github-actions[bot]`)
* **Role:** Automated CI/CD & Dynamic Kanban Synchronization
* **Identity:** `41898282+github-actions[bot]@users.noreply.github.com`
* **Responsibilities:**
  - Automated task synchronization from `.github/issues/task-*.md`.
  - Automatic task issue creation on merge to `main`.
  - Automated issue closure on Definition of Done completion (`- [x]`).
  - Idempotent milestone, label, and duplicate issue governance.

---

## 2. 📦 Dependabot (`@dependabot[bot]`)
* **Role:** Automated Dependency & Vulnerability Governance
* **Identity:** `49699333+dependabot[bot]@users.noreply.github.com`
* **Responsibilities:**
  - Weekly dependency freshness scans for Python (`pip` / `pyproject.toml`).
  - GitHub Actions version updates and security advisory monitoring.
  - Institutional conventional commits with `chore(deps):` and `ci(deps):`.
