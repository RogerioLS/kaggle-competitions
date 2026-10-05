# 01 — Competition Architecture & Boundaries

## Competition Isolation
Each competition lives in its own subdirectory under `competitions/`:
```text
competitions/
├── gemma-developer-agent/
│   ├── agent/             # Agent definition (agent.yaml, tools, runner)
│   ├── prompts/           # System prompts, personas, few-shots
│   ├── evaluation/        # Local SWE-bench benchmark harness
│   ├── training/          # Optional fine-tuning / adapter scripts
│   └── submission/        # Packaging and zip generator
```

## Import Rules
- Competition code CAN import from `src/common`.
- Competition code CANNOT import from other competition folders.
- `src/common` CANNOT import from any `competitions/*` folder.
