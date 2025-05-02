#!/usr/bin/env bash
set -e

# Activate the virtual environment
source ./hailo_infra_venv/bin/activate

# Directories
TESTS_DIR="tests"
LOG_DIR="${TESTS_DIR}/tests_logs"
mkdir -p "${LOG_DIR}"

# Install pytest and timeout plugin into the venv
echo "Installing test requirements..."
python -m pip install --upgrade pip
python -m pip install -r tests/test_resources/requirements.txt

# Download necessary Hailo resources
echo "Downloading resources..."
python -m hailo_apps_infra.installation.hailo_installation.download_resources --group all

# Run pytest via the Python module so it’s guaranteed to run in this venv
echo "Running tests..."
python -m pytest --log-cli-level=INFO \
    "${TESTS_DIR}/test_sanity_check.py" \
    "${TESTS_DIR}/test_all_pipelines.py"

echo "All tests completed successfully."
