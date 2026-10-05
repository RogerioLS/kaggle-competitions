# 00 — Global Rules for Competition Engineering

These rules apply to every agent, every task, and every implementation in this repository.

## Mission
This repository is an institutional competition engineering platform.
It is not a scratchpad for messy notebooks.
It is not an unverified prompt sandbox.
It is not a place for undocumented experiments.

The platform must remain:
- **Modular**: Code partitioned cleanly between shared utilities and isolated competitions.
- **Reproducible**: Seed fixing, environment pinning, deterministic outputs.
- **Harness-Validated**: Every change must be benchmarked on the local validation suite.
- **Auditable**: Fully passing Clean Chassis quality gates (`make audit`).
- **Production-Ready**: Adhering strictly to Kaggle compute, time, and offline constraints.

## Separation of Concerns
1. Shared tools live in `src/common/` and must be covered by tests in `tests/`.
2. Competition code lives in `competitions/<competition-name>/`.
3. Datasets and model checkpoints must never be checked into Git.
4. Evaluation harnesses must run independently from model training or agent prompt design.
