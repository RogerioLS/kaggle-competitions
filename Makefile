# ==============================================================================
#                  CLEAN CHASSIS — PRODUCTION COMMAND CENTER
# ==============================================================================

PYTHON  := python3
PIP     := pip
PYTEST  := pytest

# ANSI Color Codes
RESET   := \033[0m
BOLD    := \033[1m
DIM     := \033[2m
CYAN    := \033[36m
GREEN   := \033[32m
YELLOW  := \033[33m
RED     := \033[31m
MAGENTA := \033[35m
BLUE    := \033[34m
WHITE   := \033[97m

.PHONY: help onboarding install test check audit summary clean pre-commit pr package-submission verify-submission collect-trajectories train-lora evaluate-comparison pipeline submit-kaggle run-kernel sync-dataset

help:
	@printf "$(CYAN)┌──────────────────────────────────────────────────────────────────────────────┐\n$(RESET)"
	@printf "$(CYAN)│$(RESET) $(BOLD)$(MAGENTA)                 CLEAN CHASSIS — COMMAND CENTER                             $(RESET) $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)├──────────────────────────────────────────────────────────────────────────────┤\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make help$(RESET)               $(DIM)─$(RESET) Show this interactive command center              $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make onboarding$(RESET)         $(DIM)─$(RESET) Display best practices & Git governance banner    $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make install$(RESET)            $(DIM)─$(RESET) Install dependencies and configure git hooks      $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make test$(RESET)               $(DIM)─$(RESET) Run all automated unit and integration tests      $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make check$(RESET)              $(DIM)─$(RESET) Run pre-commit linters (Black, Isort, Flake8)     $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make audit$(RESET)              $(DIM)─$(RESET) Full audit: syntax + linters + tests + security   $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make summary$(RESET)            $(DIM)─$(RESET) Generate local audit summary report (summary.md)  $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make pr$(RESET)                 $(DIM)─$(RESET) Create or update PR with quality checklist        $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make pipeline$(RESET)           $(DIM)─$(RESET) Run end-to-end competition pipeline (train->pkg)  $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make collect-trajectories$(RESET)$(DIM)─$(RESET) Extract SFT trajectories from benchmarks         $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make train-lora$(RESET)          $(DIM)─$(RESET) Fine-tune Gemma 4 LoRA adapters on trajectories   $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make evaluate-comparison$(RESET)$(DIM)─$(RESET) Compare Pass@1 of Base vs LoRA Adapted model      $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make package-submission$(RESET) $(DIM)─$(RESET) Package declarative agent into submission.zip     $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make verify-submission$(RESET)  $(DIM)─$(RESET) Validate submission.zip and run dry-run sandbox   $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make run-kernel$(RESET)         $(DIM)─$(RESET) Execute offline Kaggle runner kernel in sandbox   $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make submit-kaggle$(RESET)      $(DIM)─$(RESET) Validate and submit submission.zip to Kaggle API  $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make sync-dataset$(RESET)       $(DIM)─$(RESET) Sync codebase to Kaggle Dataset (offline GPU)    $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make clean$(RESET)              $(DIM)─$(RESET) Clean temporary cache files, pytest, and dist     $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)├──────────────────────────────────────────────────────────────────────────────┤\n$(RESET)"
	@printf "$(CYAN)│$(RESET)           $(BOLD)$(WHITE)🔥 Clean Chassis • Built for High-Performance Engineering$(RESET)          $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)└──────────────────────────────────────────────────────────────────────────────┘\n$(RESET)"

onboarding:
	@bash scripts/install-hooks.sh --banner-only

install:
	@bash scripts/clean_install.sh

test:
	@printf "$(BOLD)$(BLUE)🚀 [TESTS] Running test suite...$(RESET)\n"
	@$(PYTEST)

check:
	@printf "$(BOLD)$(BLUE)🔍 [CHECK] Running pre-commit validation across all files...$(RESET)\n"
	@bash .githooks/pre-commit
	@printf "$(GREEN)✔ All sanity checks passed! Ready for git commit.$(RESET)\n"

audit:
	@printf "$(BOLD)$(BLUE)⚡ [AUDIT] Running full project audit...$(RESET)\n"
	@$(PYTHON) -m py_compile $$(find src tests scripts competitions -name "*.py")
	@flake8 . --max-line-length=100
	@ruff check .
	@$(PYTEST)
	@$(PYTHON) scripts/generate_summary.py
	@printf "$(GREEN)✅ FULL AUDIT COMPLETE: Clean Chassis is 100%% compliant!$(RESET)\n"

summary:
	@$(PYTHON) scripts/generate_summary.py

pr:
	@printf "$(BOLD)$(BLUE)🚀 [PR] Creating or updating GitHub Pull Request...$(RESET)\n"
	@$(PYTHON) scripts/create_pr.py

collect-trajectories:
	@printf "$(BOLD)$(BLUE)📥 [TRAINING] Extracting SFT trajectories for Gemma 4...$(RESET)\n"
	@$(PYTHON) -m competitions.gemma_developer_agent.training.trajectory_collector --generate-synthetic 5 --output artifacts/trajectories.jsonl
	@printf "$(GREEN)✔ Trajectories collected: artifacts/trajectories.jsonl$(RESET)\n"

train-lora:
	@printf "$(BOLD)$(BLUE)⚡ [TRAINING] Running Gemma 4 LoRA fine-tuning...$(RESET)\n"
	@$(PYTHON) -m competitions.gemma_developer_agent.training.lora_trainer --config competitions/gemma_developer_agent/training/config.yaml --data artifacts/trajectories.jsonl --output-dir artifacts/adapters/gemma4-swe-w4a16
	@printf "$(GREEN)✔ LoRA adapter training complete: artifacts/adapters/gemma4-swe-w4a16$(RESET)\n"

evaluate-comparison:
	@printf "$(BOLD)$(BLUE)📊 [EVAL] Evaluating Pass@1 comparison (Base vs Adapted)...$(RESET)\n"
	@$(PYTHON) -m competitions.gemma_developer_agent.training.evaluator --fixtures-dir artifacts/mock_data --output-dir artifacts
	@printf "$(GREEN)✔ Comparison evaluation complete: artifacts/model_comparison_report.md$(RESET)\n"

package-submission:
	@printf "$(BOLD)$(BLUE)📦 [SUBMISSION] Packaging declarative agent submission.zip...$(RESET)\n"
	@$(PYTHON) -m competitions.gemma_developer_agent.submission.packager --output artifacts/submission.zip --validate
	@printf "$(GREEN)✔ Submission package created and verified: artifacts/submission.zip$(RESET)\n"

verify-submission:
	@printf "$(BOLD)$(BLUE)🔍 [SUBMISSION] Validating submission.zip and running dry-run execution...$(RESET)\n"
	@$(PYTHON) -m competitions.gemma_developer_agent.submission.validator artifacts/submission.zip --dry-run
	@printf "$(GREEN)✔ Submission passed full validation and dry-run!$(RESET)\n"

run-kernel:
	@printf "$(BOLD)$(BLUE)⚡ [KERNEL] Running offline Kaggle runner kernel in sandbox...$(RESET)\n"
	@$(PYTHON) -m competitions.gemma_developer_agent.submission.kaggle_kernel --dry-run
	@printf "$(GREEN)✔ Offline Kaggle runner kernel executed successfully!$(RESET)\n"

submit-kaggle:
	@printf "$(BOLD)$(BLUE)📡 [KAGGLE] Submitting package to Kaggle competition...$(RESET)\n"
	@$(PYTHON) scripts/submit_kaggle.py $(ARGS)

sync-dataset:
	@printf "$(BOLD)$(BLUE)🔄 [KAGGLE] Syncing codebase to Kaggle Dataset...$(RESET)\n"
	@$(PYTHON) scripts/sync_kaggle_dataset.py $(ARGS)

pipeline:
	@printf "$(BOLD)$(BLUE)🚀 [PIPELINE] Running full end-to-end competition pipeline...$(RESET)\n"
	@$(MAKE) collect-trajectories
	@$(MAKE) train-lora
	@$(MAKE) evaluate-comparison
	@$(MAKE) package-submission
	@$(MAKE) verify-submission
	@$(MAKE) run-kernel
	@printf "\n$(BOLD)$(GREEN)======================================================================$(RESET)\n"
	@printf "$(BOLD)$(GREEN)🏆 GEMMA 4 DEVELOPER AGENT PIPELINE COMPLETE & READY FOR SUBMISSION!$(RESET)\n"
	@printf "$(BOLD)$(GREEN)======================================================================$(RESET)\n"

clean:
	@printf "$(YELLOW)🧹 [CLEAN] Cleaning temporary files...$(RESET)\n"
	@rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .ruff_cache summary.md artifacts/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@printf "$(GREEN)✔ Cleaned successfully.$(RESET)\n"
