#!/usr/bin/env bash
set -euo pipefail



SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREATE_SCRIPT="${SCRIPT_DIR}/hailo_apps_infra/hailo_core/hailo_installation/create_hailo_venv.py"
DOWNLOAD_GROUP="default"
# Capture any --venv-name / -n flags (so we can re-source the right dir later)
VENV_NAME="hailo_infra_venv"
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

sudo apt-get install meson

echo "🌱 Running venv-creation script…"
python3 "$CREATE_SCRIPT" --virtualenv "$VENV_NAME"

VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"
if [[ ! -f "${VENV_PATH}/bin/activate" ]]; then
  echo "❌ Could not find activate at ${VENV_PATH}/bin/activate"
  exit 1
fi

echo "🔌 Activating venv: ${VENV_NAME}"
# shellcheck disable=SC1090
source "${VENV_PATH}/bin/activate"

python3 -m pip install --upgrade pip setuptools wheel

echo "📦 Installing package (editable + post-install)…"
pip install -e .

echo "🔧 Running post-install script…"
POST_INSTALL_SCRIPT="${SCRIPT_DIR}/hailo_apps_infra/hailo_core/hailo_installation/post_install.py"
if [[ ! -f "$POST_INSTALL_SCRIPT" ]]; then
  echo "❌ Could not find post-install script at $POST_INSTALL_SCRIPT"
  exit 1
fi

# <-- add this line to execute it:
python3 "$POST_INSTALL_SCRIPT"  --group "$DOWNLOAD_GROUP"

echo "✅ All done! Your package is now in '${VENV_NAME}'."
