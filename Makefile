# ==============================================================================
#           KAGGLE COMPETITIONS HUB — PRODUCTION COMMAND CENTER
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

.PHONY: help install status sync add discover changelog summary check clean onboarding pr test

help:
	@printf "$(CYAN)┌──────────────────────────────────────────────────────────────────────────────┐\n$(RESET)"
	@printf "$(CYAN)│$(RESET) $(BOLD)$(MAGENTA)                   KAGGLE COMPETITIONS HUB — COMMAND CENTER                 $(RESET) $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)├──────────────────────────────────────────────────────────────────────────────┤\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make help$(RESET)       $(DIM)─$(RESET) Show this interactive command center                      $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make status$(RESET)     $(DIM)─$(RESET) Display health status & branches of all submodules        $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make sync$(RESET)       $(DIM)─$(RESET) Pull latest remote commits across all submodules          $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make add$(RESET)        $(DIM)─$(RESET) Register existing repo as next submodule (02_, 03_...)    $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make discover$(RESET)   $(DIM)─$(RESET) Auto-discover and register uncataloged 'kaggle-*' repos   $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make changelog$(RESET)  $(DIM)─$(RESET) AI milestone synthesis & CHANGELOG.md curation          $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make summary$(RESET)    $(DIM)─$(RESET) Generate visual portfolio audit report (summary.md)       $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make test$(RESET)       $(DIM)─$(RESET) Run automated integrity test suite via pytest             $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make check$(RESET)      $(DIM)─$(RESET) Run syntax validation across all automation scripts       $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make pr$(RESET)         $(DIM)─$(RESET) Create or update Pull Request with quality checklist      $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make install$(RESET)    $(DIM)─$(RESET) Configure local git hooks & conventional commit policies  $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)│$(RESET)  $(BOLD)$(GREEN)make clean$(RESET)      $(DIM)─$(RESET) Clean temporary files, caches, and report artifacts       $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)├──────────────────────────────────────────────────────────────────────────────┤\n$(RESET)"
	@printf "$(CYAN)│$(RESET)       $(BOLD)$(WHITE)🏆 Kaggle Competitions Hub • Federated Machine Learning Portfolio$(RESET)      $(CYAN)│\n$(RESET)"
	@printf "$(CYAN)└──────────────────────────────────────────────────────────────────────────────┘\n$(RESET)"

onboarding:
	@bash scripts/install-hooks.sh --banner-only

install:
	@bash scripts/install-hooks.sh

status:
	@$(PYTHON) scripts/sync_submodules.py --status

sync:
	@$(PYTHON) scripts/sync_submodules.py --update

add:
	@$(PYTHON) scripts/add_competition.py $(ARGS)

discover:
	@$(PYTHON) scripts/auto_discover_competitions.py $(ARGS)

changelog:
	@$(PYTHON) scripts/update_changelog.py $(ARGS)

summary:
	@$(PYTHON) scripts/generate_summary.py

check:
	@printf "$(BOLD)$(BLUE)⚡ [SYNTAX] Compiling Python automation scripts...$(RESET)\n"
	@$(PYTHON) -m py_compile scripts/*.py
	@printf "$(GREEN)✔ All scripts compiled successfully!$(RESET)\n"

test:
	@printf "$(BOLD)$(BLUE)🧪 [TESTS] Running automated hub integrity test suite...$(RESET)\n"
	@$(PYTEST) -v

pr:
	@printf "$(BOLD)$(BLUE)🚀 [PR] Creating or updating GitHub Pull Request...$(RESET)\n"
	@$(PYTHON) scripts/create_pr.py

clean:
	@printf "$(YELLOW)🧹 [CLEAN] Cleaning temporary files...$(RESET)\n"
	@rm -rf artifacts/ summary.md .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@printf "$(GREEN)✔ Cleaned successfully.$(RESET)\n"
