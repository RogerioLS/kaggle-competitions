#!/usr/bin/env bash
# ==============================================================================
#            CLEAN CHASSIS — 42-STYLE QUIET INSTALLER & PROGRESS
# ==============================================================================

set -e

RESET="\033[0m"
GREEN="\033[32m"
BLUE="\033[34m"
CYAN="\033[36m"
RED="\033[31m"
BOLD="\033[1m"
DIM="\033[2m"

LOG_FILE=$(mktemp /tmp/clean_install.XXXXXX.log)
trap 'rm -f "$LOG_FILE"' EXIT

TOTAL_STEPS=3
COUNT=0

progress() {
    COUNT=$((COUNT + 1))
    PERCENT=$((COUNT * 100 / TOTAL_STEPS))
    printf "\r${GREEN}Installing Clean Chassis %3d%%${RESET} ${DIM}(%s)${RESET}\033[K" "$PERCENT" "$1"
}

spinner_run() {
    local msg="$1"
    shift
    local pid
    "$@" > "$LOG_FILE" 2>&1 &
    pid=$!

    local spin='-\|/'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i + 1) % 4 ))
        local percent=$(( (COUNT * 100) / TOTAL_STEPS ))
        printf "\r${GREEN}Installing Clean Chassis %3d%%${RESET} ${DIM}%s [%c]${RESET}\033[K" "$percent" "$msg" "${spin:$i:1}"
        sleep 0.1
    done

    wait "$pid"
    local status=$?
    if [ $status -ne 0 ]; then
        printf "\r${RED}❌ Error during: %s${RESET}\n" "$msg"
        cat "$LOG_FILE"
        exit $status
    fi
    progress "$msg"
}

printf "${BOLD}${BLUE}📦 [INSTALL] Preparing Clean Chassis environment...${RESET}\n"

# Step 1: Upgrading pip
spinner_run "Upgrading pip" python3 -m pip install --upgrade pip

# Step 2: Installing project dependencies (editable)
spinner_run "Installing dependencies" python3 -m pip install -e ".[dev]"

# Step 3: Configuring Git hooks
spinner_run "Configuring git hooks" bash scripts/install-hooks.sh --no-banner

printf "\n${GREEN}✔ Clean Chassis environment ready!${RESET}\n"
