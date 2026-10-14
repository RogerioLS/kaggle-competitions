---
id: TASK-08
title: "GitHub-to-Kaggle Dataset Sync Automation & CI/CD Pipeline"
area: competition/gemma-developer-agent
type: feature
milestone: 4
---

## 🎯 Task Objective
Implement an automated synchronization pipeline between GitHub and Kaggle Datasets (`scripts/sync_kaggle_dataset.py`, `.github/workflows/sync_kaggle.yml`, `make sync-dataset`), enabling continuous code deployment to Kaggle's offline GPU environment without manual upload overhead.

## 📋 Definition of Done
- [ ] Create Kaggle dataset metadata configuration and packaging utility `scripts/sync_kaggle_dataset.py` with credential discovery, directory filtering, and `--dry-run` simulation
- [ ] Implement GitHub Actions workflow `.github/workflows/sync_kaggle.yml` for automatic dispatch on push to `main` and manual trigger (`workflow_dispatch`)
- [ ] Add `make sync-dataset` command to Makefile with parameter passing and audit integration
- [ ] Write automated unit tests covering dataset packaging, metadata validation, and dry-run execution
- [ ] Update competition documentation in `competitions/gemma_developer_agent/README.md` with dataset attachment and usage instructions in Kaggle Notebooks
