# 📜 Changelog

All notable changes, competition milestones, and architectural achievements for the **Kaggle Competitions Hub** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]








### Added
- **02_kaggle-name-that-llm**: ✨ feat(v7-gold): [TASK-10] implement transductive prompt centering, hungarian matching and compiler
- **02_kaggle-name-that-llm**: 📝 docs(architecture): [DOCS] document competitive journey and v7.0 gold medal architecture
- **02_kaggle-name-that-llm**: ✨ feat(stylometry): [TASK-09:#30] integrate 100+ deep stylometric features and tune sibling re-ranking
- **02_kaggle-name-that-llm**: ✨ feat(v6): [TASK-09:#30] extract modular apex architecture and add deterministic compiler
- **02_kaggle-name-that-llm**: 📝 docs(status): [DOCS] record official lb score 0.669 for v6.0 multi-lora apex
- **02_kaggle-name-that-llm**: 📝 docs(memory): [TASK-08:#26] document v5.0 empirical ceiling, v6.0 multi-lora architecture and evolution strategy
- **02_kaggle-name-that-llm**: 📝 docs(status): [TASK-08:#26] activate v6.0 multi-lora apex roadmap
- **02_kaggle-name-that-llm**: 📝 docs(status): [TASK-08:#26] record v5.0 official score 0.364 and update roadmap toward neural multi-lora
- **02_kaggle-name-that-llm**: ✨ feat(notebooks): [TASK-08:#26] implement v5.0 offline notebook with open pool dual-svc and sibling refinement
- **02_kaggle-name-that-llm**: 📝 docs: [TASK-08:#26] document v4.0 post-mortem and v5.0 open pool dual-svc architecture
- **02_kaggle-name-that-llm**: ✨ feat(notebooks): [TASK-08:#26] integrate sinkhorn test balancing into offline notebook generator
- **02_kaggle-name-that-llm**: ✨ feat(models): [TASK-08:#26] implement damped sinkhorn-knopp marginal distribution balancer
- **02_kaggle-name-that-llm**: ✨ feat(models): [TASK-08:#26] implement conditional family gating and sibling refiner
- **02_kaggle-name-that-llm**: 📝 docs: [TASK-07:#21] update master memory compilation and system design ADRs for v3.0 architecture
- **02_kaggle-name-that-llm**: Merge remote-tracking branch 'origin/main' into feat/task-06-hierarchical-deberta-and-deep-stylometry
- **02_kaggle-name-that-llm**: ✨ feat(modeling): [TASK-07:#21] implement boosted decision trees, SVD latent semantics and calibrated stacking
- **02_kaggle-name-that-llm**: ✨ feat(notebook): [TASK-06:#18] build v2.0 offline notebook with hierarchical deep stylometry engine
- **02_kaggle-name-that-llm**: 📝 docs(audit): [TASK-06:#18] record architecture ADRs, 83 passing tests and task 07 roadmap
- **02_kaggle-name-that-llm**: ✨ feat(transformers): [TASK-04:#10] implement dense transformer embeddings and neural sequence classifier
- **02_kaggle-name-that-llm**: ✨ feat(features): [TASK-03:#9] implement stylometric and tfidf feature pipeline with baseline models
- **02_kaggle-name-that-llm**: ✨ feat(evaluation): [TASK-02] implement domain entities, stratified group cv splitter, and balanced accuracy metrics
- **02_kaggle-name-that-llm**: ✨ feat(governance): [TASK-01] establish institutional operating system, rules, and documentation
- **01_kaggle-gemma4-developer-agent**: Merge feat/register-02-kaggle-name-that-llm
- **01_kaggle-gemma4-developer-agent**: ✨ feat(hub): [INFRA] auto-register 02_kaggle-name-that-llm submodule
- **01_kaggle-gemma4-developer-agent**: ✨ feat(hub): [INFRA] register 02_kaggle-name-that-llm submodule and update portfolio index
- **01_kaggle-gemma4-developer-agent**: 🔧 chore(submodules): [INFRA] sync 01_kaggle-gemma4-developer-agent to task-17 and refine auth logging
- **01_kaggle-gemma4-developer-agent**: ✨ feat(governance): [DOCS] add institutional security, code of conduct, contributing, and AI changelog tracker
- **01_kaggle-gemma4-developer-agent**: ✨ feat(notebook): [TASK-17] integrate 10-task stratified benchmark into cell 6 of evaluation notebook
- **01_kaggle-gemma4-developer-agent**: Merge branch 'main' into feat/task-17-test-driven-reproduction
- **01_kaggle-gemma4-developer-agent**: ✨ feat(prompt): [TASK-17] enrich validator with framework-specific verification recipes and /tmp safety
- **01_kaggle-gemma4-developer-agent**: ✨ feat(benchmark): [TASK-17] implement stratified 10-task benchmark sampler and unit tests
- **01_kaggle-gemma4-developer-agent**: 📝 docs(task-17): [TASK-17] eliminate django/sympy hallucinations and align with competition dataset (fastapi, rich, requests)
- Autonomous AI competition discovery and registration bot (`scripts/auto_discover_competitions.py`).
- Automatic upstream submodule synchronization bot with GitHub Actions (`submodule_sync.yml`).
- Portfolio health audit suite with cyberpunk badge generator (`scripts/generate_summary.py`).
- Automated branch naming and commit quality gate with PR auto-close (`branch_lint.yml`).
- Initialized federated portfolio architecture powered by Git Submodules.

---

## [v1.0.0] - 2026-11-04

### Added
- **Competition `01_kaggle-gemma4-developer-agent`**:
  - Registered official Google Gemma 4 Developer Agent challenge repository.
  - Autonomous software engineering agent capable of declarative SWE-bench execution.
  - Multi-agent ReAct orchestration, 4-bit LoRA fine-tuning, and vLLM quad-L4 GPU tensor parallelism.
  - Validated offline packaging and live Kaggle CLI submission pipelines.
- Production command center `Makefile` (`help`, `status`, `sync`, `add`, `discover`, `summary`, `test`, `pr`).
- Institutional governance framework (`SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`).
- Multi-tier pre-commit git hooks enforcing conventional commits and code styling.
