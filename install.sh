#!/bin/bash
set -euo pipefail

###——— CONFIGURATION —————————————————————————————————————————————
# Override by exporting VENV_NAME, otherwise defaults here:
: "${VENV_NAME:=hailo_infra_venv}"

PIP_CMD="pip3"
PYTHON_CMD="python3"

###——— ARCHITECTURE DETECTION —————————————————————————————————————
ARCH=$(uname -m)
if [[ "$ARCH" == arm* || "$ARCH" == aarch64 ]]; then
  SYS_PKG="hailo-all"
  TAPPAS_PIP_PKG="hailo-tappas-core-python-binding"
  echo "🔍 Detected ARM architecture ($ARCH): will check for 'hailo-all' and RPi Python binding"
else
  SYS_PKG="hailort-pcie-driver"
  TAPPAS_PIP_PKG="hailo-tappas-core"
  echo "🔍 Detected x86 architecture ($ARCH): will check for 'hailort-pcie-driver' and x86 Python binding"
fi

###——— ARG PARSING —————————————————————————————————————————————————
INSTALL_GSTREAMER=true
INSTALL_PIPELINES=true

for arg in "$@"; do
  case "$arg" in
    --gstreamer-only)
      INSTALL_GSTREAMER=true
      ;;
    --pipelines-only)
      INSTALL_GSTREAMER=true
      INSTALL_PIPELINES=true
      ;;
    --all)
      INSTALL_GSTREAMER=true
      INSTALL_PIPELINES=true
      ;;
    *)
      echo "⚠️  Ignoring unknown flag: $arg"
      ;;
  esac
done

###——— HELPERS —————————————————————————————————————————————————————
detect_system_pkg_version() {
  dpkg-query -W -f='${Version}' "$1" 2>/dev/null || echo ""
}

detect_pip_pkg_version() {
  if $PIP_CMD show "$1" >/dev/null 2>&1; then
    $PIP_CMD show "$1" \
      | awk -F': ' '/^Version: /{print $2; exit}'
  else
    echo ""
  fi
}

check_system_pkg() {
  pkg="$1"
  ver=$(detect_system_pkg_version "$pkg")
  if [[ -z "$ver" ]]; then
    echo "❌ System package '$pkg' not found."
    echo "    Please install it before proceeding."
    exit 1
  else
    echo "✅ $pkg (system) version: $ver"
  fi
}

###——— RESOURCE DIRS —————————————————————————————————————————————————

# detect real invoking user & group (works under sudo or direct run)
if [ -n "$SUDO_USER" ]; then
  INSTALL_USER="$SUDO_USER"
else
  INSTALL_USER="$(id -un)"
fi
INSTALL_GROUP="$(id -gn "$INSTALL_USER")"

RESOURCE_BASE="/usr/local/hailo/resources"

echo
echo "🔧 Creating $RESOURCE_BASE subdirs…"
RESOURCE_BASE="/usr/local/hailo/resources"
for sub in models/hailo8 models/hailo8l videos so; do
  sudo mkdir -p "$RESOURCE_BASE/$sub"
done

# chown/chmod with the detected user:group
sudo chown -R "$INSTALL_USER":"$INSTALL_GROUP" "$RESOURCE_BASE"
sudo chmod -R 755 "$RESOURCE_BASE"


###——— SYSTEM PKG CHECKS —————————————————————————————————————————————
echo
echo "📋 Checking required system packages…"
check_system_pkg "$SYS_PKG"
check_system_pkg hailort

echo
echo "📋 Checking for HailoRT system version"
HRT_VER=$(detect_system_pkg_version hailort)
echo "📋 Checking for hailo-tappas vs hailo-tappas-core…"
HT1=$(detect_system_pkg_version hailo-tappas)
HT2=$(detect_system_pkg_version hailo-tappas-core)
HTC_VER="none"
if [[ -n "$HT1" ]]; then
  echo "✅ hailo-tappas version: $HT1"
  HTC_VER="$HT1"
elif [[ -n "$HT2" ]]; then
  echo "✅ hailo-tappas-core version: $HT2"
  HTC_VER="$HT2"
else
  echo "❌ Neither hailo-tappas nor hailo-tappas-core is installed."
  exit 1
fi

###——— PIP PKG CHECKS —————————————————————————————————————————————————
echo
echo "📋 Checking host-Python pip packages…"
INSTALL_PYHAILORT=false
INSTALL_TAPPAS_CORE=false

# hailort
host_py=$(detect_pip_pkg_version hailort)
if [[ -z "$host_py" ]]; then
  echo "⚠️  pip 'hailort' missing; will install in venv."
  INSTALL_PYHAILORT=true
else
  echo "✅ pip 'hailort' version: $host_py"
fi

# tappas binding pkg (RPi vs x86)
host_tc=$(detect_pip_pkg_version "$TAPPAS_PIP_PKG")
if [[ -z "$host_tc" ]]; then
  echo "⚠️  pip '$TAPPAS_PIP_PKG' missing; will install in venv."
  INSTALL_TAPPAS_CORE=true
else
  echo "✅ pip '$TAPPAS_PIP_PKG' version: $host_tc"
fi

###——— VENV SETUP —————————————————————————————————————————————————————
echo
if [[ -d "$VENV_NAME" ]]; then
  echo "✅ Virtualenv '$VENV_NAME' exists. Activating…"
  source "$VENV_NAME/bin/activate"
else
  echo "🔧 Creating virtualenv '$VENV_NAME'…"
  if $INSTALL_PYHAILORT && $INSTALL_TAPPAS_CORE; then
    $PYTHON_CMD -m venv "$VENV_NAME"
  else
    $PYTHON_CMD -m venv --system-site-packages "$VENV_NAME"
  fi
  echo "✅ Created. Activating…"
  source "$VENV_NAME/bin/activate"
fi

# Re-check inside venv
if ! pip show hailort >/dev/null 2>&1; then INSTALL_PYHAILORT=true; fi
if ! pip show "$TAPPAS_PIP_PKG" >/dev/null 2>&1; then INSTALL_TAPPAS_CORE=true; fi

###——— INSTALL MISSING PIP PACKAGES —————————————————————————————————————
echo
echo "📦 Installing missing pip packages…"
to_install=()

# this is the python installer path
PY_INSTALLER="hailo_apps_infra/installation/hailo_installation/python_installation.py"

# build list of what we _would_ install
$INSTALL_PYHAILORT   && to_install+=( "hailort" )
$INSTALL_TAPPAS_CORE && to_install+=( "$TAPPAS_PIP_PKG" )

if [[ ${#to_install[@]} -gt 0 ]]; then
  echo "🔧 Installing Hailo Python bindings via installer script…"

  cmd=( python3 "$PY_INSTALLER" --venv-path "$VENV_NAME" )

  # only pass flags for what we need
  if [[ $INSTALL_PYHAILORT == true ]]; then
    cmd+=( --install-pyhailort --pyhailort-version "$HRT_VER" )
  fi
  if [[ $INSTALL_TAPPAS_CORE == true ]]; then
    cmd+=( --install-tappas-core --tappas-version "$HTC_VER" )
  fi

  # run it
  "${cmd[@]}"
else
  echo "✅ All required pip packages present."
fi


###——— ENV FILE —————————————————————————————————————————————————————
ENV_FILE=".env"
ENV_PATH="$(pwd)/$ENV_FILE"

# Step 1: Create the .env file if it doesn't exist
if [[ ! -f "$ENV_PATH" ]]; then
    echo "🔧 Creating .env file at $ENV_PATH"
    touch "$ENV_PATH"
    chmod 666 "$ENV_PATH"  # rw-rw-r-- for user/group
else
    echo "✅ .env already exists at $ENV_PATH"
    chmod 666 "$ENV_PATH"
fi


###——— MODULE INSTALLS ———————————————————————————————————————————————————
echo
echo "📦 Upgrading pip/setuptools/wheel…"
pip install --upgrade pip setuptools wheel

echo "📦 Installing core Hailo modules…"
pip install -e ./hailo_apps_infra/common \
            -e ./hailo_apps_infra/config \
            -e ./hailo_apps_infra/installation

$INSTALL_GSTREAMER && echo "📦 Installing gstreamer…" && pip install -e ./hailo_apps_infra/gstreamer
$INSTALL_PIPELINES && echo "📦 Installing pipelines…" && pip install -e ./hailo_apps_infra/pipelines

echo "📦 Installing shared runtime deps…"
pip install -r requirements.txt

###——— POST-INSTALL ———————————————————————————————————————————————————
echo
echo "⚙️  Running post-install…"
$PYTHON_CMD -m hailo_installation.post_install

###——— FINISHED —————————————————————————————————————————————————————
cat <<EOF

🎉  All done!

To reactivate your environment later:
    source $VENV_NAME/bin/activate

EOF
