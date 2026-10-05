# 04 — Evaluation Harness & Zero Leakage

## Validation Discipline
1. **Zero Data Leakage**:
   - Never expose test split answers to agent prompts or training corpora.
   - Separate validation issues completely from few-shot exemplars.
2. **Local Metric Parity**:
   - The local evaluator must reflect the competition leaderboard evaluation exactly.
   - For SWE-bench: execute patches inside isolated environments and run test suites (PASS/FAIL).
3. **Run Logs & Tracking**:
   - Log timestamp, commit hash, score, execution time, and error traces for every benchmark run.
