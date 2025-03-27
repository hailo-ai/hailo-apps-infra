#!/bin/bash

# Path to your tests directory
TESTS_DIR="tests"

# Create logs directory if it doesn't exist
mkdir -p tests/tests_logs

# Source the virtual environment
echo "Activating virtual environment..."
source infra-venv/bin/activate

# Install pytest requirements if not already installed
echo "Installing test requirements..."
pip install -r tests/test_resources/requirements.txt

# Download resources using the Python-based downloader
echo "Downloading resources..."
python -m hailo_apps_infra.install.download_resources --group all

# Run pytest for all test files
echo "Running tests..."
pytest --log-cli-level=INFO \
       "$TESTS_DIR/test_sanity_check.py" \
       "$TESTS_DIR/test_pipelines.py" \
       "$TESTS_DIR/test_special_features.py"

echo "All tests completed."