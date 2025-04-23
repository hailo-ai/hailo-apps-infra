#!/bin/bash
set -e

# Path to your tests directory
TESTS_DIR="tests"

# Create logs directory if it doesn't exist
mkdir -p tests/tests_logs

# Get virtual environment name from config
VENV_NAME=$(python -c "from hailo_apps_infra.common.hailo_common.get_config_values import get_config_value; print(get_config_value('virtual_env_name'))" 2>/dev/null || echo "hailo_venv")

# Define the virtual environment path based on config value
VENV_DIR="$VENV_NAME"

echo "Using virtual environment: $VENV_DIR"

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run the installation script first or make sure the virtual environment path is correct"
    exit 1
fi

# Source the virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install pytest requirements if not already installed
echo "Installing test requirements..."
pip install -r tests/test_resources/requirements.txt

# Download resources using the Python-based downloader with group from config
echo "Downloading resources..."
python -m hailo_apps_infra.installation.hailo_installation.download_resources --group all

# Run pytest for all test files
echo "Running tests..."
PYTHONPATH="." pytest --log-cli-level=INFO \
       "$TESTS_DIR/test_sanity_check.py" \
       "$TESTS_DIR/test_pipelines.py" \

echo "All tests completed."