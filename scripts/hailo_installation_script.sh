#!/bin/bash
# Hailo Runtime Installer Script
# This script downloads and installs all Hailo runtime requirements
# from the deb server. It performs several checks:
#   - Checks system architecture (x86_64, aarch64, or Raspberry Pi)
#   - For Raspberry Pi: if 'hailo-all' is not installed, points to RPi docs and exits.
#   - Validates Python version (supported: 3.8, 3.9, 3.10, 3.11)
#   - Checks the kernel version (warns if not officially supported)
#   - Downloads and installs the following:
#       * HailoRT driver deb
#       * HailoRT deb
#       * Tapas core deb
#       * HailoRT Python bindings whl
#       * Tapas core Python bindings whl
#
# The deb server is hosted at: http://dev-public.hailo.ai/2025_01
# Owner: Sergii Tishchenko
#
# Usage example:
#   wget http://dev-public.hailo.ai/2025_01/hailo_runtime_installer.sh -O installer.sh && bash installer.sh [--version=<version>]
#

set -e

# --- Configurable Variables ---

# Base URL of the deb server
BASE_URL="http://dev-public.hailo.ai/2025_01"

# Default version numbers for packages (if using --version, you can adjust these)
HAILORT_VERSION="4.20.0"
TAPPAS_CORE_VERSION="3.31.0"

# Default architecture (can be overridden by command-line argument)
VENV_NAME="hailo_venv"


# Parse optional command-line flag to override version numbers (e.g., --version=4.20.0)
# For a more complex versioning scheme, you might also separate HailoRT and TAPPAS versions.
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --hailort-version=*)
            HAILORT_VERSION="${1#*=}"
            ;;
        --tappas-core-version=*)
            TAPPAS_CORE_VERSION="${1#*=}"
            ;;
        --venv-name=*)
            VENV_NAME="${1#*=}"
            ;;
        *)
            echo "Unknown parameter passed: $1"
            exit 1
            ;;
    esac
    shift
done


# Download directory for temporary resources
DOWNLOAD_DIR="hailo_temp_resources"
mkdir -p "$DOWNLOAD_DIR"

# --- Functions ---

# Download file function: Retries download once if it fails.
download_file() {
    local file="$1"
    echo "Downloading $file from $BASE_URL..."
    wget "$BASE_URL/$file" -O "$DOWNLOAD_DIR/$file"
    if [ $? -ne 0 ]; then
        echo "Error downloading $file. Retrying..."
        wget "$BASE_URL/$file" -O "$DOWNLOAD_DIR/$file"
        if [ $? -ne 0 ]; then
            echo "Failed to download $file after retry. Exiting."
            exit 1
        fi
    fi
}

# Install file function: Uses dpkg for .deb files or pip for .whl files.
install_file() {
    local file="$1"
    local file_path="$DOWNLOAD_DIR/$file"
    echo "Installing $file..."
    if [[ "$file" == *.deb ]]; then
         sudo dpkg -i "$file_path" || { echo "dpkg installation failed for $file. Exiting."; exit 1; }
    elif [[ "$file" == *.whl ]]; then
         python3 -m pip install "$file_path" || { echo "pip installation failed for $file. Exiting."; exit 1; }
    else
         echo "Unknown file type for $file."
    fi
}

# --- System Checks ---

# Check system architecture.
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# --- Raspberry Pi Specific Check ---
if [[ "$ARCH" == *"arm"* ]]; then
    # Check if running on a Raspberry Pi by inspecting the device model if available.
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(tr -d '\0' < /proc/device-tree/model)
        echo "Device model: $MODEL"
        if [[ "$MODEL" == *"Raspberry Pi"* ]]; then
            echo "Raspberry Pi detected."
            # Check if 'hailo-all' is installed (adjust the command check as needed).
            if ! command -v hailo-all &> /dev/null; then
                echo "hailo-all is not installed on this Raspberry Pi."
                echo "Please refer to the Raspberry Pi installation documentation:"
                echo "https://www.raspberrypi.com/documentation/computers/ai.html"
                exit 1
            else
                echo "hailo-all is already installed. Note: This installer does not auto-install on RPi."
                exit 0
            fi
        fi
    fi
fi

# Check Python version; only versions 3.8, 3.9, 3.10, and 3.11 are supported.
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"
if [[ ! "$PYTHON_VERSION" =~ ^3\.(8|9|10|11) ]]; then
   echo "Unsupported Python version. Supported versions are 3.8, 3.9, 3.10, and 3.11."
   exit 1
fi

# Check kernel version and warn if it may not be officially supported.
KERNEL_VERSION=$(uname -r)
echo "Kernel version: $KERNEL_VERSION"
# Placeholder: change the condition to suit your officially supported kernel(s)
OFFICIAL_KERNEL_PREFIX="6.5.0"
if [[ "$KERNEL_VERSION" != "$OFFICIAL_KERNEL_PREFIX"* ]]; then
    echo "Warning: Kernel version $KERNEL_VERSION may not be officially supported."
fi

# Install build-essential package# ...
sudo apt-get update && sudo apt-get install -y build-essential 
echo "Installing build-essential package..."

# --- Install Dependencies for hailo-tappas-core ---
echo "Installing additional dependencies for hailo-tappas-core..."
sudo apt-get update && sudo apt-get install -y ffmpeg python3-virtualenv gcc-12 g++-12 python-gi-dev pkg-config libcairo2-dev libgirepository1.0-dev libgstreamer1.0-dev cmake libgstreamer-plugins-base1.0-dev libzmq3-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-bad gstreamer1.0-libav libopencv-dev python3-opencv rapidjson-dev

# --- Determine Package Files Based on Architecture & Python Version ---

# Common files (downloaded regardless of architecture):
common_files=(
    "hailort-pcie-driver_${HAILORT_VERSION}_all.deb"
    "tappas_core_python_binding-${TAPPAS_CORE_VERSION}-py3-none-any.whl"
)

# Variables to construct file names for Python wheels (using the installed Python version)
PY_VER_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PY_VER_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
PY_TAG="cp${PY_VER_MAJOR}${PY_VER_MINOR}-cp${PY_VER_MAJOR}${PY_VER_MINOR}"

# Initialize an array to hold architecture-specific files.
ARCH_FILES=()

if [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then
    echo "Configuring file list for AMD64..."
    # AMD64-specific files:
    amd64_deb_files=(
        "hailort_${HAILORT_VERSION}_amd64.deb"
        "hailo-tappas-core_${TAPPAS_CORE_VERSION}_amd64.deb"
    )
    # Python binding wheel for AMD64.
    amd64_whl="hailort-${HAILORT_VERSION}-${PY_TAG}-linux_x86_64.whl"
    ARCH_FILES=( "${amd64_deb_files[@]}" "$amd64_whl" )
elif [[ "$ARCH" == "aarch64" ]]; then
    echo "Configuring file list for ARM64..."
    # ARM64-specific files:
    arm64_deb_files=(
        "hailort_${HAILORT_VERSION}_arm64.deb"
        "hailo-tappas-core_${TAPPAS_CORE_VERSION}_arm64.deb"
    )
    # Python binding wheel for ARM64.
    arm64_whl="hailort-${HAILORT_VERSION}-${PY_TAG}-linux_aarch64.whl"
    ARCH_FILES=( "${arm64_deb_files[@]}" "$arm64_whl" )
else
    echo "Unknown or unsupported architecture: $ARCH"
    exit 1
fi

# --- Download Phase ---

echo "Downloading common package files..."
for file in "${common_files[@]}"; do
    download_file "$file"
done

echo "Downloading architecture-specific package files..."
for file in "${ARCH_FILES[@]}"; do
    download_file "$file"
done

echo "All selected files downloaded successfully."

# --- Installation Phase ---

echo "Starting installation process..."

# 1. Install PCIe driver (common file)
install_file "${common_files[0]}"

# 2. Install HailoRT deb (architecture-specific file, index 0)
install_file "${ARCH_FILES[0]}"

# 3. Install Hailo Tappas Core deb (architecture-specific file, index 1)
install_file "${ARCH_FILES[1]}"

# Variable VENV_NAME should be set to your virtual environment folder name
VENV_NAME=${VENV_NAME:-hailo_venv}

# Get the actual user (even when run with sudo)
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER=$SUDO_USER
    ACTUAL_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
else
    ACTUAL_USER=$USER
    ACTUAL_HOME=$HOME
fi

echo "Creating virtual environment for user: $ACTUAL_USER"

# Create or reuse virtual environment using an absolute path
if [ ! -d "$PROJECT_ROOT/$VENV_NAME" ]; then
    echo "Creating virtual environment: $VENV_NAME"
    python3 -m venv "$PROJECT_ROOT/$VENV_NAME"
    
    # Change ownership to the actual user if running as sudo
    if [ -n "$SUDO_USER" ]; then
        chown -R $ACTUAL_USER:$ACTUAL_USER "$PROJECT_ROOT/$VENV_NAME"
    fi
else
    echo "Using existing virtual environment: $VENV_NAME"
fi

# Check that the activation script exists before sourcing it
if [ -f "$PROJECT_ROOT/$VENV_NAME/bin/activate" ]; then
    source "$PROJECT_ROOT/$VENV_NAME/bin/activate"
    pip install --upgrade pip
else
    echo "Error: Could not find virtual environment activation script at $PROJECT_ROOT/$VENV_NAME/bin/activate"
    exit 1
fi

pip install --upgrade pip

echo "Installing Python bindings into virtual environment..."
install_file "${ARCH_FILES[2]}"  # hailort Python wheel
install_file "${common_files[1]}"  # tappas core Python binding wheel

deactivate

echo "Python bindings installed into virtual environment: $VENV_NAME"
echo "Installation completed successfully."

echo "To activate it later, run: source $VENV_NAME/bin/activate"

