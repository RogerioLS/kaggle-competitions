#!/usr/bin/env bash
# ==============================================================================
#            CLEAN CHASSIS — GIT HOOKS INSTALLER & ONBOARDING
# ==============================================================================

set -e

# ANSI Color Codes & Formatting
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
MAGENTA="\033[35m"
BLUE="\033[34m"
WHITE="\033[97m"

if [ "$1" != "--banner-only" ]; then
    GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || true)

    if [ -z "$GIT_DIR" ]; then
        echo -e "${RED}❌ Error: Not a git repository.${RESET}"
        exit 1
    fi

    echo -e "${BOLD}${BLUE}🔧 Configuring custom git hooks path...${RESET}"
    git config core.hooksPath .githooks
    chmod +x .githooks/* 2>/dev/null || true

    echo -e "${GREEN}✅ Git hooks successfully configured to '.githooks'.${RESET}"
fi

if [ "$1" = "--no-banner" ]; then
    exit 0
fi

echo ""
printf "${CYAN}┌──────────────────────────────────────────────────────────────────────────────┐\n${RESET}"
printf "${CYAN}│${RESET}  ${BOLD}${MAGENTA}              🛡️  CLEAN CHASSIS — ONBOARDING & BEST PRACTICES               ${RESET} ${CYAN}│\n${RESET}"
printf "${CYAN}├──────────────────────────────────────────────────────────────────────────────┤\n${RESET}"
printf "${CYAN}│${RESET}  ${BOLD}${YELLOW}🌿 1. BRANCH NAMING CONVENTION:${RESET}                                             ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     Format:   ${GREEN}<type>/<task-id>-<description-in-kebab-case>${RESET}                   ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     Examples: ${WHITE}feat/task-01-core-engine${RESET} ${DIM}|${RESET} ${WHITE}fix/auth-02-expired-token${RESET}           ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}                                                                              ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}  ${BOLD}${YELLOW}📝 2. CONVENTIONAL TASK COMMITS:${RESET}                                            ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     Format:   ${GREEN}<type>(<scope>): [<TASK-ID>:#<ISSUE>] <description>${RESET}            ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     Examples: ${WHITE}feat(core): [TASK-01:#1] implement calculation engine${RESET}          ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}               ${WHITE}chore(ci): [INFRA] configure pre-commit linters${RESET}                ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}                                                                              ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}  ${BOLD}${YELLOW}🧪 3. QUALITY GATES & COMMANDS:${RESET}                                             ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     ${BOLD}${GREEN}make check${RESET}      ${DIM}─${RESET} Run pre-commit linters across all project files        ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     ${BOLD}${GREEN}make audit${RESET}      ${DIM}─${RESET} Full test suite + syntax compilation + security scan   ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     ${BOLD}${GREEN}make onboarding${RESET} ${DIM}─${RESET} Display this best practices guide anytime              ${CYAN}│\n${RESET}"
printf "${CYAN}│${RESET}     ${BOLD}${GREEN}make help${RESET}       ${DIM}─${RESET} Open interactive CLI command center                    ${CYAN}│\n${RESET}"
printf "${CYAN}├──────────────────────────────────────────────────────────────────────────────┤\n${RESET}"
printf "${CYAN}│${RESET}           ${BOLD}${WHITE}🔥 Clean Chassis • Built for Production Quality${RESET}                    ${CYAN}│\n${RESET}"
printf "${CYAN}└──────────────────────────────────────────────────────────────────────────────┘\n${RESET}"
echo ""
