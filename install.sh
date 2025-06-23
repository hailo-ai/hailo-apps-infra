#!/usr/bin/env bash
set -euo pipefail

# Resolve this script’s directory (install.sh), so venv sits next to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DOWNLOAD_GROUP="default"
VENV_NAME="venv_hailo_apps"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--venv-name)
      VENV_NAME="$2"
      shift 2
      ;;
    --all)
      DOWNLOAD_GROUP="all"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# 1) Grab *only* the SUMMARY line (strip off the "SUMMARY: " prefix)
SUMMARY_LINE=$(
  ./scripts/check_installed_packages.sh 2>&1 \
    | sed -n 's/^SUMMARY: //p'
)

if [[ -z "$SUMMARY_LINE" ]]; then
  echo "❌ Could not find SUMMARY line" >&2
  exit 1
fi

IFS=' ' read -r -a pairs <<< "$SUMMARY_LINE"

DRIVER_VERSION="${pairs[0]#*=}"
HAILORT_VERSION="${pairs[1]#*=}"
PYHAILORT_VERSION="${pairs[2]#*=}"
TAPPAS_CORE_VERSION="${pairs[3]#*=}"
PYTAPPAS_VERSION="${pairs[4]#*=}"

INSTALL_HAILORT=false
INSTALL_TAPPAS_CORE=false

# 2) Check installed versions
if [[ "$DRIVER_VERSION" == "-1" ]]; then
  echo "❌ Hailo PCI driver is not installed. Please install it first."
  echo "To install the driver, run:"
  echo "    sudo ./scripts/hailo_installer.sh"
  exit 1
fi
if [[ "$HAILORT_VERSION" == "-1" ]]; then
  echo "❌ HailoRT is not installed. Please install it first."
  echo "To install the driver, run:"
  echo "    sudo ./scripts/hailo_installer.sh"
  exit 1
fi
if [[ "$TAPPAS_CORE_VERSION" == "-1" ]]; then
  echo "❌ TAPPAS is not installed. Please install it first."
  echo "To install the driver, run:"
  echo "    sudo ./scripts/hailo_installer.sh"
  exit 1
fi

if [[ "$PYHAILORT_VERSION" == "-1" ]]; then
  echo "❌ Python HailoRT binding is not installed."
  echo "Will be installed in the virtualenv."
  INSTALL_HAILORT=true
fi
if [[ "$PYTAPPAS_VERSION" == "-1" ]]; then
  echo "❌ Python TAPPAS binding is not installed."
  echo "Will be installed in the virtualenv."
  INSTALL_TAPPAS_CORE=true
fi

VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"

# If a venv with this name already exists, delete it
if [[ -d "${VENV_PATH}" ]]; then
  echo "🗑️  Removing existing virtualenv at ${VENV_PATH}"
  rm -rf "${VENV_PATH}"
fi

# Clean up build artifacts from the current directory
echo "🧹 Cleaning up build artifacts..."
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf build/ dist/ 2>/dev/null || true
echo "✅ Build artifacts cleaned"

# Ensure Meson is installed
sudo apt-get install -y meson
sudo apt install python3-gi python3-gi-cairo

echo "🌱 Creating virtualenv '${VENV_NAME}' (with system site-packages)…"
python3 -m venv --system-site-packages "${VENV_PATH}"

if [[ ! -f "${VENV_PATH}/bin/activate" ]]; then
  echo "❌ Could not find activate at ${VENV_PATH}/bin/activate"
  exit 1
fi

echo "🔌 Activating venv: ${VENV_NAME}"
# shellcheck disable=SC1090
source "${VENV_PATH}/bin/activate"

# run  hailo python packages installation script
echo "📦 Installing Python Hailo packages…"
FLAGS=""
if [[ "$INSTALL_TAPPAS_CORE" = true ]]; then
  echo "Installing TAPPAS core Python binding"
  FLAGS="--tappas-core-version=${TAPPAS_CORE_VERSION}"
fi
if [[ "$INSTALL_HAILORT" = true ]]; then
  echo "Installing HailoRT Python binding"
  FLAGS="${FLAGS} --hailort-version=${HAILORT_VERSION}"
fi

./scripts/hailo_python_installation.sh ${FLAGS}

python3 -m pip install --upgrade pip setuptools wheel

echo "📦 Installing package (editable + post-install)…"
pip install -e .

echo "🔧 Running post-install script…"

hailo-post-install --group "$DOWNLOAD_GROUP"

echo "✅ All done! Your package is now in '${VENV_NAME}'."
