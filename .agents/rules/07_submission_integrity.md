# 07 — Kaggle Submission Integrity

## Submission Guardrails
1. **Offline Mode**: Ensure agent and code run with strictly NO internet access during evaluation.
2. **Compute & Memory Budget**: Keep within Kaggle runtime limits (e.g., L4x4 GPU memory, 9-hour timeout).
3. **Package Inspection**:
   - Verify `submission.zip` contains all required files (`agent.yaml`, `prompts/`, `skills/`).
   - Check zip size limits (do not accidentally bundle large datasets or virtual environments).
4. **Dry-Run Test**: Always run an end-to-end dry-run of the submission package locally before uploading.
