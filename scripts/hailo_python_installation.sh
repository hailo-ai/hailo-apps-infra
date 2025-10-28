#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Hailo Python Wheels: downloader & installer
# Works with the main installer (calls this with --hailort-version/--tappas-core-version).
# Presets for H8/H10; overrideable via flags.
# ------------------------------------------------------------------------------

# Base URL of the deb server
BASE_URL="http://dev-public.hailo.ai/2025_10"

# Default version numbers for packages (if using --version, you can adjust these)

HAILORT_VERSION_H8="4.23.0"
TAPPAS_CORE_VERSION_H8="5.1.0"
HAILORT_VERSION_H10="5.1.0"
TAPPAS_CORE_VERSION_H10="5.1.0"

HAILORT_VERSION=""
TAPPAS_CORE_VERSION=""

# Behavior flags
HW_ARCHITECTURE=""          # hailo88 | hailo10 (affects defaults if versions not passed)
DOWNLOAD_DIR="/usr/local/hailo/resources/packages"
DOWNLOAD_ONLY=false
QUIET=false

INSTALL_HAILORT=false
INSTALL_TAPPAS=false

# Pip flag presets
PIP_SYS_FLAGS=(--break-system-packages --disable-pip-version-check --no-input --prefer-binary)
PIP_USER_FLAGS=(--user --break-system-packages --disable-pip-version-check --no-input --prefer-binary)
PIP_VENV_FLAGS=(--disable-pip-version-check --no-input --prefer-binary)


usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --arch=(H8|H10)                Choose hardware preset for default versions (default: H8)
  --hailort-version=VER          Force a specific HailoRT wheel version (overrides preset)
  --tappas-core-version=VER      Force a specific TAPPAS core wheel version (overrides preset)
  --base-url=URL                 Override base URL (default: ${BASE_URL})
  --download-dir=DIR             Where to place wheels (default: ${DOWNLOAD_DIR})
  --download-only                Only download wheels; do not install
  -q, --quiet                    Less output
  -h, --help                     Show this help

Notes:
- If you pass neither --hailort-version nor --tappas-core-version, the chosen --arch preset is used.
- If you pass only one of them, only that package is downloaded/installed.
EOF
}

log() { $QUIET || echo -e "$*"; }

# -------------------- Parse flags --------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hw-arch=*)
      HW_ARCHITECTURE="${1#*=}"
      if [[ "$HW_ARCHITECTURE" != "hailo8" && "$HW_ARCHITECTURE" != "hailo10" ]]; then
          echo "Invalid hardware architecture specified. Use 'hailo8' or 'hailo10'."
          exit 1
      fi
      shift
      ;;

    --hailort-version=*)
      HAILORT_VERSION="${1#*=}"
      shift
      ;;
    --tappas-core-version=*)
      TAPPAS_CORE_VERSION="${1#*=}"
      shift
      ;;
    --base-url=*)
      BASE_URL="${1#*=}"
      shift
      ;;
    --download-dir=*)
      DOWNLOAD_DIR="${1#*=}"
      shift
      ;;
    --download-only)
      DOWNLOAD_ONLY=true
      shift
      ;;
    -q|--quiet)
      QUIET=true
      shift
      ;;
    -d | --default)
      INSTALL_HAILORT=true
      INSTALL_TAPPAS=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# -------------------- Set versions based on hardware architecture if not already specified --------------------
if [[ -z ${HAILORT_VERSION+x} || -z "$HAILORT_VERSION" ]]; then
  case "$HW_ARCHITECTURE" in
    hailo8)  HAILORT_VERSION="$HAILORT_VERSION_H8"  ;;
    hailo10) HAILORT_VERSION="$HAILORT_VERSION_H10" ;;
  esac
fi

if [[ -z ${TAPPAS_CORE_VERSION+x} || -z "$TAPPAS_CORE_VERSION" ]]; then
  case "$HW_ARCHITECTURE" in
    hailo8)  TAPPAS_CORE_VERSION="$TAPPAS_CORE_VERSION_H8"  ;;
    hailo10) TAPPAS_CORE_VERSION="$TAPPAS_CORE_VERSION_H10" ;;
  esac
fi



# If user specified only one version, we install only that one.

[[ -n "$HAILORT_VERSION" ]] && INSTALL_HAILORT=true
[[ -n "$TAPPAS_CORE_VERSION" ]] && INSTALL_TAPPAS=true

if [[ "$INSTALL_HAILORT" == false && "$INSTALL_TAPPAS" == false ]]; then
  log "Nothing to do (no versions requested)."
  exit 0
fi

HW_FOLDER_NAME=""
# Determine hardware name based on architecture
if [[ "$HW_ARCHITECTURE" == "hailo8" ]]; then
  HW_FOLDER_NAME="Hailo8"
  HW_FOLDER_SECONDARY="Hailo10"
else
  HW_FOLDER_NAME="Hailo10"
  HW_FOLDER_SECONDARY="Hailo8"
fi



# -------------------- Compute tags --------------------
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
PY_TAG="cp${PY_MAJOR}${PY_MINOR}-cp${PY_MAJOR}${PY_MINOR}"

# Map uname -m to wheel platform tag
UNAME_M="$(uname -m)"
case "$UNAME_M" in
  x86_64)  ARCH_TAG="linux_x86_64" ;;
  aarch64) ARCH_TAG="linux_aarch64" ;;
  *)
    echo "Unsupported architecture: $UNAME_M"
    exit 1
    ;;
esac

if [[ -e "$DOWNLOAD_DIR" ]]; then
  if [[ ! -d "$DOWNLOAD_DIR" ]]; then
    echo "Error: $DOWNLOAD_DIR exists and is not a directory."
    exit 1
  else
    echo "Directory $DOWNLOAD_DIR already exists."
  fi
else
  echo "Creating download directory: $DOWNLOAD_DIR"
  mkdir -p "$DOWNLOAD_DIR"
fi

log "→ BASE_URL            = $BASE_URL" 
log "→ ARCH preset         = $HW_ARCHITECTURE"
log "→ Python tag          = $PY_TAG"
log "→ Wheel arch tag      = $ARCH_TAG"
$INSTALL_HAILORT && log "→ HailoRT version     = $HAILORT_VERSION"
$INSTALL_TAPPAS && log "→ TAPPAS core version = $TAPPAS_CORE_VERSION"
log "→ Download dir        = $DOWNLOAD_DIR"
log "→ Download only?      = $DOWNLOAD_ONLY"

# -------------------- Helpers --------------------
fetch() {
  local url="$1"
  local out="$2"
  if [[ -f "$out" ]]; then
    log "  - Exists: $(basename "$out")"
    return 0
  fi
  log "  - GET $url"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 --retry-delay 2 -o "$out" "$url"
  else
    wget -q --tries=3 --timeout=20 -O "$out" "$url"
  fi
}
is_venv() {
  # True for venv/virtualenv/conda (prefix differs) or real_prefix set
  python3 - "$@" <<'PY'
import sys
print("1" if (getattr(sys, "real_prefix", None) or sys.prefix != sys.base_prefix) else "0")
PY
}

site_writable() {
  # True if system site-packages dir is writable
  python3 - "$@" <<'PY'
import os, site, sys
try:
    paths = site.getsitepackages()
except Exception:
    # Fallback (rare, but just in case)
    paths = [sys.prefix + "/lib/python%s.%s/site-packages" % sys.version_info[:2]]
print("1" if (paths and os.access(paths[0], os.W_OK)) else "0")
PY
}

install_pip_package() {
  local package_path="$1"

  # Detect venv
  local in_venv
  in_venv="$(python3 - <<'PY'
import sys
print("1" if (getattr(sys, "real_prefix", None) or sys.prefix != sys.base_prefix) else "0")
PY
)"

  if [[ "$in_venv" == "1" ]]; then
    echo "Installing into active virtual environment"
    python3 -m pip install "${PIP_VENV_FLAGS[@]}" --upgrade -- "$package_path"
  elif [[ "$(site_writable)" == "1" ]]; then
    echo "Installing system-wide"
    python3 -m pip install "${PIP_SYS_FLAGS[@]}" --upgrade -- "$package_path"
  else
    echo "Installing with --user (+ --break-system-packages)"
    python3 -m pip install "${PIP_USER_FLAGS[@]}" --upgrade -- "$package_path"
  fi
}


# -------------------- Download wheels --------------------
HW_FOLDER_NAME=""
# Determine hardware name based on architecture
if [[ "$HW_ARCHITECTURE" == "hailo8" ]]; then
  HW_FOLDER_NAME="Hailo8"
  HW_FOLDER_SECONDARY="Hailo10"
else
  HW_FOLDER_NAME="Hailo10"
  HW_FOLDER_SECONDARY="Hailo8"
fi

if [[ "$INSTALL_TAPPAS" == true ]]; then

  TAPPAS_FILE="hailo_tappas_core_python_binding-${TAPPAS_CORE_VERSION}-py3-none-any.whl"
  TAPPAS_URL="${BASE_URL}/${HW_FOLDER_NAME}/${TAPPAS_FILE}"

  if ! fetch "$TAPPAS_URL" "${DOWNLOAD_DIR}/${TAPPAS_FILE}"; then
    echo "Failed from primary ($HW_FOLDER_NAME). Trying secondary: ${HW_FOLDER_SECONDARY}"
    TAPPAS_URL="${BASE_URL}/${HW_FOLDER_SECONDARY}/${TAPPAS_FILE}"
    if ! fetch "$TAPPAS_URL" "${DOWNLOAD_DIR}/${TAPPAS_FILE}"; then
      echo "Failed from both primary and secondary folders. Check URL(s) and network."
      exit 1
    fi
  fi
fi

if [[ "$INSTALL_HAILORT" == true ]]; then
  HAILORT_FILE="hailort-${HAILORT_VERSION}-${PY_TAG}-${ARCH_TAG}.whl"
  HAILORT_URL="${BASE_URL}/${HW_FOLDER_NAME}/${HAILORT_FILE}"
  fetch "$HAILORT_URL" "${DOWNLOAD_DIR}/${HAILORT_FILE}"
fi

if [[ "$DOWNLOAD_ONLY" == true ]]; then
  log "✅ Download(s) complete (download-only)."
  exit 0
fi

# -------------------- Install into current environment --------------------
log "→ Upgrading pip / wheel / setuptools…"

log "→ Upgrading pip / wheel / setuptools…"
if [[ "$(is_venv)" == "1" ]]; then
  echo "Upgrading in virtual environment"
  python3 -m pip install "${PIP_VENV_FLAGS[@]}" --upgrade pip setuptools wheel >/dev/null
elif [[ "$(site_writable)" == "1" ]]; then
  echo "Upgrading system-wide"
  python3 -m pip install "${PIP_SYS_FLAGS[@]}" --upgrade pip setuptools wheel >/dev/null
else
  echo "Upgrading with --user (+ --break-system-packages)"
  python3 -m pip install "${PIP_USER_FLAGS[@]}" --upgrade pip setuptools wheel >/dev/null
fi


if [[ "$INSTALL_HAILORT" == true ]]; then
  log "→ Installing HailoRT wheel…"
  install_pip_package "${DOWNLOAD_DIR}/${HAILORT_FILE}"
fi

if [[ "$INSTALL_TAPPAS" == true ]]; then
  log "→ Installing TAPPAS core wheel…"
  install_pip_package "${DOWNLOAD_DIR}/${TAPPAS_FILE}"
fi

log "✅ Installation complete."