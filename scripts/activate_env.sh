#!/bin/bash
# Activate vsm-hva conda environment
# Usage: source scripts/activate_env.sh

# Initialize conda if needed
if [ -z "$CONDA_EXE" ]; then
    if [ -f "/opt/homebrew/anaconda3/etc/profile.d/conda.sh" ]; then
        source /opt/homebrew/anaconda3/etc/profile.d/conda.sh
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    fi
fi

# Activate environment
conda activate vsm-hva

# Ensure conda Python is first in PATH
export PATH="/opt/homebrew/anaconda3/envs/vsm-hva/bin:$PATH"
