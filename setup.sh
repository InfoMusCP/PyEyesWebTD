#!/usr/bin/env bash

# -------------------------------
# CONFIGURATION
# -------------------------------
VENV_DIR="./pyeyesweb_env"
LIB_SOURCE="."
# -------------------------------

# -------------------------------
# ANSI COLOR CODES
# -------------------------------
RED="\033[91m"
GREEN="\033[92m"
YELLOW="\033[93m"
RESET="\033[0m"

# -------------------------------
# CHECK PYTHON
# -------------------------------
echo -e "${YELLOW}[INFO] Checking Python installation...${RESET}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python not found. Please install Python 3.11.${RESET}"
    exit 1
fi

PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${YELLOW}[INFO] Python version detected: $PY_VER${RESET}"

if [[ ! "$PY_VER" =~ ^3\.11\. ]]; then
    echo -e "${RED}[ERROR] Python 3.11.x is required. Found $PY_VER${RESET}"
    exit 1
fi
echo -e "${GREEN}[OK] Python 3.11.x found.${RESET}"

# -------------------------------
# CREATE VIRTUAL ENV
# -------------------------------
echo -e "${YELLOW}[INFO] Creating virtual environment \"$VENV_DIR\"...${RESET}"
python3 -m venv "$VENV_DIR"
if [[ $? -ne 0 ]]; then
    echo -e "${RED}[ERROR] Failed to create virtual environment.${RESET}"
    exit 1
fi
echo -e "${GREEN}[OK] Virtual environment created.${RESET}"

# -------------------------------
# ACTIVATE VENV
# -------------------------------
echo -e "${YELLOW}[INFO] Activating virtual environment...${RESET}"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
if [[ $? -ne 0 ]]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment.${RESET}"
    exit 1
fi
echo -e "${GREEN}[OK] Virtual environment activated.${RESET}"

# -------------------------------
# INSTALL LIBRARY
# -------------------------------
echo -e "${YELLOW}[INFO] Upgrading pip, setuptools, wheel...${RESET}"
python -m pip install --upgrade pip setuptools wheel

echo -e "${YELLOW}[INFO] Installing pyeyesweb from \"$LIB_SOURCE\"...${RESET}"
python -m pip install pyeyesweb
if [[ $? -ne 0 ]]; then
    echo -e "${RED}[ERROR] Library installation failed.${RESET}"
    exit 1
fi
echo -e "${GREEN}[OK] Library installed successfully in virtual environment.${RESET}"

# -------------------------------
# END
# -------------------------------
echo
echo -e "${YELLOW}[INFO] Script finished.${RESET}"
exit 0
