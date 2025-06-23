#!/bin/bash
#
# This script configures the environment to allow running Python scripts
# from anywhere within the project, correctly resolving package imports.
# It will also activate the virtual environment.
#
# INSTRUCTIONS:
# 1. Run this script from the project's root directory using the 'source' command.
# 2. Example: source set_env.sh
#
# After sourcing, your PYTHONPATH will be set for the current terminal session.
# Function to check if the script is being sourced
is_sourced() {
    if [ -n "$ZSH_VERSION" ]; then
        [[ -o sourced ]]
    elif [ -n "$BASH_VERSION" ]; then
        [[ "${BASH_SOURCE[0]}" != "$0" ]]
    else
        echo "Unsupported shell. Please use bash or zsh."
        return 1
    fi
}

# Only proceed if the script is being sourced
if is_sourced; then
    echo "Setting up the environment..."
else
    echo "This script should be sourced, not executed directly."
    exit 1
fi

# Get the absolute path of the project's root directory (where this script is located).
PROJECT_ROOT=$(pwd)

# Prepend the project root to the PYTHONPATH.
# This ensures our project's modules are found first.
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo "Project directory added to PYTHONPATH for this session:"
echo "${PROJECT_ROOT}"

# Activate the virtual environment
if [ -d "venv_hailo_apps" ]; then
    source venv_hailo_apps/bin/activate
    echo "Virtual environment activated"
else
    echo "Virtual environment directory 'venv_hailo_apps' not found. Please ensure it is created and try again."
    return 1
fi
