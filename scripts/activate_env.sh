#!/bin/bash
# Activate .venv virtual environment
# Usage: source scripts/activate_env.sh

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Error: .venv directory not found. Please create it first:"
    echo "  python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo "Virtual environment activated: $(which python)"
