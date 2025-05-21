#!/usr/bin/env bash
set -euo pipefail



SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREATE_SCRIPT="${SCRIPT_DIR}/hailo_apps_infra/hailo_core/hailo_installation/create_hailo_venv.py"

# Capture any --venv-name / -n flags (so we can re-source the right dir later)
VENV_NAME="hailo_infra_venv"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--venv-name)
      VENV_NAME="$2"
      shift 2
      ;;
    *)
      # pass through anything else to the create script
      shift
      ;;
  esac
done

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

echo "📦 Installing package (editable + post-install)…"
pip install -e .

echo "✅ All done! Your package is now in '${VENV_NAME}'."
