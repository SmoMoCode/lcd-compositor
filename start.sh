#!/bin/bash

# PSB Layer Extractor Startup Script
# This script sets up the Python virtual environment and runs the layer extraction tool

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/extract_layers.py"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=^..^= PSB Layer Extractor"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
echo "Checking dependencies..."
NEEDS_INSTALL=0

if ! python -c "import psd_tools" 2>/dev/null; then
    NEEDS_INSTALL=1
fi

if ! python -c "import PIL" 2>/dev/null; then
    NEEDS_INSTALL=1
fi

if ! python -c "import yaml" 2>/dev/null; then
    NEEDS_INSTALL=1
fi

# Install or upgrade dependencies if needed
if [ $NEEDS_INSTALL -eq 1 ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS"
    echo -e "${GREEN}Dependencies installed.${NC}"
else
    echo -e "${GREEN}All dependencies are installed.${NC}"
fi

# Run the Python script with all arguments passed to this script
echo ""
echo "Running layer extractor..."
echo ""
python "$PYTHON_SCRIPT" "$@"

# Deactivate virtual environment
deactivate
