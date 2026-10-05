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

.PHONY: help install onboarding test check audit summary clean pre-commit

help:
	@printf "$(CYAN)┌──────────────────────────────────────────────────────────────────────────────┐\n$(RESET)"
	@printf "$(CYAN)│$(RESET) $(BOLD)$(MAGENTA)                 CLEAN CHASSIS — COMMAND CENTER                             $(RESET) $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)├──────────────────────────────────────────────────────────────────────────────┤\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make help$(RESET)       $(DIM)─$(RESET) Show this interactive command center                     $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make onboarding$(RESET) $(DIM)─$(RESET) Display best practices & Git governance banner           $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make install$(RESET)    $(DIM)─$(RESET) Install dev dependencies and configure local git hooks     $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make test$(RESET)       $(DIM)─$(RESET) Run all automated unit and integration test suites        $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make check$(RESET)      $(DIM)─$(RESET) Run pre-commit linters (Black, Isort, Flake8, Ruff)       $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make audit$(RESET)      $(DIM)─$(RESET) Full audit: syntax + linters + unit tests + security scan $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make summary$(RESET)    $(DIM)─$(RESET) Generate local audit summary report (summary.md)          $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make clean$(RESET)      $(DIM)─$(RESET) Clean temporary cache files, .pytest_cache and dist       $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)├──────────────────────────────────────────────────────────────────────────────┤\n$(RESET)"
	@printf "$(CYAN)│$(RESET)           $(BOLD)$(WHITE)🔥 Clean Chassis • Built for High-Performance Engineering$(RESET)          $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)└──────────────────────────────────────────────────────────────────────────────┘\n$(RESET)"

onboarding:
	@bash scripts/install-hooks.sh --banner-only

install:
	@printf "$(BOLD)$(BLUE)📦 [INSTALL] Installing dev dependencies and configuring git hooks...$(RESET)\n"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -e ".[dev]"
	@bash scripts/install-hooks.sh
	@printf "$(GREEN)✔ Clean Chassis environment ready!$(RESET)\n"

test:
	@printf "$(BOLD)$(BLUE)🚀 [TESTS] Running test suite...$(RESET)\n"
	@$(PYTEST)

check:
	@printf "$(BOLD)$(BLUE)🔍 [CHECK] Running pre-commit validation across all files...$(RESET)\n"
	@bash .githooks/pre-commit
	@printf "$(GREEN)✔ All sanity checks passed! Ready for git commit.$(RESET)\n"

audit:
	@printf "$(BOLD)$(BLUE)⚡ [AUDIT] Running full project audit...$(RESET)\n"
	@$(PYTHON) -m py_compile $$(find src tests scripts -name "*.py")
	@flake8 . --max-line-length=100
	@ruff check .
	@$(PYTEST)
	@$(PYTHON) scripts/generate_summary.py
	@printf "$(GREEN)✅ FULL AUDIT COMPLETE: Clean Chassis is 100%% compliant!$(RESET)\n"

summary:
	@$(PYTHON) scripts/generate_summary.py

clean:
	@printf "$(YELLOW)🧹 [CLEAN] Cleaning temporary files...$(RESET)\n"
	@rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .ruff_cache summary.md artifacts/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@printf "$(GREEN)✔ Cleaned successfully.$(RESET)\n"
