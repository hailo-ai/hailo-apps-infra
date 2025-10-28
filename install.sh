#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DOWNLOAD_GROUP="default"
VENV_NAME="venv_hailo_apps"
PYHAILORT_PATH=""
PYTAPPAS_PATH=""
NO_INSTALL=false
NO_SYSTEM_PYTHON=false
ENV_FILE="${SCRIPT_DIR}/.env"

# Detect if running with sudo and get original user and group
if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  if [[ -z "${SUDO_USER:-}" ]]; then
    echo "❌ This script must not be run as root directly. Please run with sudo as a regular user:"
    echo "   sudo $0"
    exit 1
  fi
  ORIGINAL_USER="${SUDO_USER}"
  # Get the primary group of the original user
  ORIGINAL_GROUP=$(id -gn "${SUDO_USER}")
else
  echo "❌ This script requires sudo privileges. Please run with sudo:"
  echo "   sudo $0 $*"
  exit 1
fi

echo "🔍 Detected user: ${ORIGINAL_USER}"
echo "🔍 Detected primary group: ${ORIGINAL_GROUP}"

# Check if group name is different from username
if [[ "${ORIGINAL_USER}" == "${ORIGINAL_GROUP}" ]]; then
  echo "✅ User's primary group matches username"
else
  echo "✅ User's primary group is different from username: ${ORIGINAL_GROUP}"
fi

as_original_user() {
  if [[ ${EUID:-$(id -u)} -eq 0 && -n "${SUDO_USER:-}" ]]; then
    sudo -n -u "$SUDO_USER" -H -- "$@"
  else
    "$@"
  fi
}

# Function to fix ownership of files/directories to original user and group
fix_ownership() {
  local target="$1"
  if [[ -e "$target" ]]; then
    sudo chown -R "${ORIGINAL_USER}:${ORIGINAL_GROUP}" "$target" 2>/dev/null || true
  fi
}

show_help() {
    cat << EOF
Usage: sudo $0 [OPTIONS]

Install Hailo Apps Infrastructure with virtual environment setup.

⚠️  This script MUST be run with sudo.

OPTIONS:
    -n, --venv-name NAME        Set virtual environment name (default: venv_hailo_apps)
    -ph, --pyhailort PATH       Path to custom PyHailoRT wheel file
    -pt, --pytappas PATH        Path to custom PyTappas wheel file
    --all                       Download all available models/resources
    -x, --no-install           Skip installation of Python packages
    --no-system-python         Don't use system site-packages (default: use system site-packages unless on x86)
    -h, --help                  Show this help message and exit

EXAMPLES:
    sudo $0                          # Basic installation with default settings
    sudo $0 -n my_venv               # Use custom virtual environment name
    sudo $0 --all                    # Install with all models/resources
    sudo $0 -x                       # Skip Python package installation
    sudo $0 --no-system-python       # Don't use system site-packages
    sudo $0 -ph /path/to/pyhailort.whl -pt /path/to/pytappas.whl  # Use custom wheel files

DESCRIPTION:
    This script sets up a Python virtual environment for Hailo Apps Infrastructure.
    It checks for required Hailo components (driver, HailoRT, TAPPAS) and installs
    missing Python bindings in the virtual environment.

    The script will:
    1. Detect the original user and their primary group
    2. Check installed Hailo components
    3. Create/recreate virtual environment
    4. Install required Python packages
    5. Download models and resources
    6. Run post-installation setup
    7. Set correct ownership for all created files

    Operations requiring root privileges (like creating directories in /usr/local)
    are executed with sudo, while all other operations are executed as the original user.

REQUIREMENTS:
    - Must be run with sudo
    - Hailo PCI driver must be installed
    - HailoRT must be installed
    - TAPPAS core must be installed

    Use 'sudo ./scripts/hailo_installer.sh' to install missing components.

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--venv-name)
      VENV_NAME="$2"
      shift 2
      ;;
    -ph|--pyhailort)
      PYHAILORT_PATH="$2"
      shift 2
      ;;
    -pt|--pytappas)
      PYTAPPAS_PATH="$2"
      shift 2
      ;;
    --all)
      DOWNLOAD_GROUP="all"
      shift
      ;;
    -x | --no-install)
      NO_INSTALL=true
      echo "Skipping installation of Python packages."
      shift
      ;;
    --no-system-python)
      NO_SYSTEM_PYTHON=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information."
      exit 1
      ;;
  esac
done

SUMMARY_LINE=$(
  as_original_user ./scripts/check_installed_packages.sh 2>&1 \
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

if [[ "$NO_INSTALL" = true ]]; then
  echo "Skipping installation of Python packages."
  INSTALL_HAILORT=false
  INSTALL_TAPPAS_CORE=false
fi

VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"

# Detect architecture
ARCH=$(uname -m)
IS_X86=false
if [[ "$ARCH" == "x86_64" || "$ARCH" == "i386" || "$ARCH" == "i686" ]]; then
  IS_X86=true
fi

# Determine whether to use system site-packages
USE_SYSTEM_SITE_PACKAGES=true
if [[ "$NO_SYSTEM_PYTHON" = true ]]; then
  USE_SYSTEM_SITE_PACKAGES=false
  echo "🔧 Using --no-system-python flag: virtualenv will not use system site-packages"
else
  echo "🔧 Using system site-packages for virtualenv"
fi

if [[ -d "${VENV_PATH}" ]]; then
  echo "🗑️  Removing existing virtualenv at ${VENV_PATH}"
  # Try removing as regular user first, fallback to sudo if needed
  if ! as_original_user rm -rf "${VENV_PATH}" 2>/dev/null; then
    echo "  ⚠️  Regular user removal failed, fixing ownership..."
    fix_ownership "${VENV_PATH}"
    as_original_user rm -rf "${VENV_PATH}"
  fi
fi

echo "🧹 Cleaning up build artifacts..."
# Try cleaning as regular user first, fallback to sudo if needed
if ! as_original_user find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null; then
  echo "  ⚠️  Regular user cleanup failed, fixing ownership..."
  fix_ownership .
  as_original_user find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
fi

if ! as_original_user rm -rf build/ dist/ 2>/dev/null; then
  echo "  ⚠️  Regular user cleanup failed, fixing ownership..."
  fix_ownership .
  as_original_user rm -rf build/ dist/ 2>/dev/null || true
fi
echo "✅ Build artifacts cleaned"

# Remove existing .env file if it exists
if [[ -f "${ENV_FILE}" ]]; then
  echo "🗑️  Removing existing .env file at ${ENV_FILE}"
  if ! as_original_user rm -f "${ENV_FILE}" 2>/dev/null; then
    echo "  ⚠️  Regular user removal failed, fixing ownership..."
    fix_ownership "${ENV_FILE}"
    as_original_user rm -f "${ENV_FILE}"
  fi
fi

# Create .env file with proper ownership and permissions
as_original_user touch "${ENV_FILE}"
as_original_user chmod 644 "${ENV_FILE}"
echo "✅ Created .env file at ${ENV_FILE}"

sudo apt-get install -y meson
sudo apt install python3-gi python3-gi-cairo

# Create virtual environment with or without system site-packages
if [[ "$USE_SYSTEM_SITE_PACKAGES" = true ]]; then
  echo "🌱 Creating virtualenv '${VENV_NAME}' (with system site-packages)…"
  as_original_user python3 -m venv --system-site-packages "${VENV_PATH}"
else
  echo "🌱 Creating virtualenv '${VENV_NAME}' (without system site-packages)…"
  as_original_user python3 -m venv "${VENV_PATH}"
fi

if [[ ! -f "${VENV_PATH}/bin/activate" ]]; then
  echo "❌ Could not find activate at ${VENV_PATH}/bin/activate"
  exit 1
fi

echo "🔌 Activating venv: ${VENV_NAME}"

if [[ -n "$PYHAILORT_PATH" ]]; then
  echo "Using custom HailoRT Python binding path: $PYHAILORT_PATH"
  if [[ ! -f "$PYHAILORT_PATH" ]]; then
    echo "❌ HailoRT Python binding not found at $PYHAILORT_PATH"
    exit 1
  fi
  as_original_user bash -c "source '${VENV_PATH}/bin/activate' && pip install '$PYHAILORT_PATH'"
  INSTALL_HAILORT=false
fi
if [[ -n "$PYTAPPAS_PATH" ]]; then
  echo "Using custom TAPPAS Python binding path: $PYTAPPAS_PATH"
  if [[ ! -f "$PYTAPPAS_PATH" ]]; then
    echo "❌ TAPPAS Python binding not found at $PYTAPPAS_PATH"
    exit 1
  fi
  as_original_user bash -c "source '${VENV_PATH}/bin/activate' && pip install '$PYTAPPAS_PATH'"
  INSTALL_TAPPAS_CORE=false
fi

  echo '📦 Installing Python Hailo packages…'
  FLAGS=''
  if [[ '${INSTALL_TAPPAS_CORE}' = true ]]; then
    echo 'Installing TAPPAS core Python binding'
    FLAGS='--tappas-core-version=${TAPPAS_CORE_VERSION}'
  fi
  if [[ '${INSTALL_HAILORT}' = true ]]; then
    echo 'Installing HailoRT Python binding'
    FLAGS=\"\${FLAGS} --hailort-version=${HAILORT_VERSION}\"
  fi

if [[ -z "$FLAGS" ]]; then
  echo "No Hailo Python packages to install."
else
  echo "Installing Hailo Python packages with flags: ${FLAGS}"
  as_original_user ./scripts/hailo_python_installation.sh ${FLAGS}
fi

as_original_user bash -c "source '${VENV_PATH}/bin/activate' && python3 -m pip install --upgrade pip setuptools wheel"

echo "📦 Installing package (editable + post-install)…"
as_original_user bash -c "source '${VENV_PATH}/bin/activate' && pip install -e ."

# Create Hailo resources directories with correct permissions
echo "📁 Creating Hailo resources directories..."

RESOURCES_ROOT="/usr/local/hailo/resources"

# Create the directory structure (requires sudo)
sudo mkdir -p ${RESOURCES_ROOT}/models/{hailo8,hailo8l,hailo10h}
sudo mkdir -p ${RESOURCES_ROOT}/{videos,so,photos,json,packages}
sudo mkdir -p ${RESOURCES_ROOT}/face_recon/{train,samples}

# Set ownership to current user and their primary group
sudo chown -R ${ORIGINAL_USER}:${ORIGINAL_GROUP} ${RESOURCES_ROOT}

# Set permissions: rwxr-xr-x for directories (775 for group access)
sudo chmod -R 775 ${RESOURCES_ROOT}

# Ensure the user can write to these directories
sudo chmod -R u+w ${RESOURCES_ROOT}

echo "✅ Hailo resources directories created successfully"
echo "   Owner: ${ORIGINAL_USER}:${ORIGINAL_GROUP}"
echo "   Location: ${RESOURCES_ROOT}"

echo "🔧 Running post-install script…"

# Fix resources directory permissions if needed
echo "🔍 Checking resources directory permissions..."
if [[ -d "resources" ]]; then
    # Check if it's a symlink and test the target directory
    if [[ -L "resources" ]]; then
        target_dir=$(readlink "resources")
        echo "  🔗 Resources is a symlink pointing to: $target_dir"
        # Test if user can write to the target directory
        if ! as_original_user test -w "$target_dir" 2>/dev/null; then
            echo "  ⚠️  Target directory requires sudo permissions, fixing ownership..."
            fix_ownership "$target_dir"
        fi
        # Also fix the symlink itself
        if ! as_original_user test -w "resources" 2>/dev/null; then
            echo "  ⚠️  Symlink requires sudo permissions, fixing ownership..."
            fix_ownership "resources"
        fi
    else
        # It's a regular directory
        if ! as_original_user test -w "resources" 2>/dev/null; then
            echo "  ⚠️  Resources directory requires sudo permissions, fixing ownership..."
            fix_ownership "resources"
        fi
    fi
fi

if ! as_original_user bash -c "source '${VENV_PATH}/bin/activate' && hailo-post-install --group '$DOWNLOAD_GROUP'"; then
    echo ""
    echo "❌ Post-installation failed!"
    echo "This usually means:"
    echo "  - C++ compilation failed (check for permission issues in build directories)"
    echo "  - Resource download failed (check network connection)"
    echo "  - Environment setup failed"
    echo ""
    echo "Please check the error messages above and try again."
    echo "If you see permission errors, you may need to clean up old build directories with sudo."
    exit 1
fi

echo ""
echo "🔍 Verifying installation..."

# Verification function
verify_installation() {
    local success=true
    
    echo "  📁 Checking virtual environment..."
    if [[ -f "${VENV_PATH}/bin/activate" ]]; then
        echo "    ✅ Virtual environment created successfully"
    else
        echo "    ❌ Virtual environment not found"
        success=false
    fi
    
    echo "  🐍 Checking Python packages..."
    if as_original_user bash -c "source '${VENV_PATH}/bin/activate' && python3 -c 'import hailo_apps; print(\"Hailo Apps version:\", hailo_apps.__file__)'" 2>/dev/null; then
        echo "    ✅ Hailo Apps package installed successfully"
    else
        echo "    ❌ Hailo Apps package not properly installed"
        success=false
    fi
    
    echo "  📦 Checking HailoRT Python bindings..."
    if as_original_user bash -c "source '${VENV_PATH}/bin/activate' && python3 -c 'import hailo; print(\"HailoRT available\")'" 2>/dev/null; then
        echo "    ✅ HailoRT Python bindings available"
    else
        echo "    ⚠️  HailoRT Python bindings not available (may need system installation)"
    fi
    
    echo "  📦 Checking TAPPAS Python bindings..."
    if as_original_user bash -c "source '${VENV_PATH}/bin/activate' && python3 -c 'import hailo_platform; print(\"TAPPAS available\")'" 2>/dev/null; then
        echo "    ✅ TAPPAS Python bindings available"
    else
        echo "    ⚠️  TAPPAS Python bindings not available (may need system installation)"
    fi
    
    echo "  📁 Checking resources directory..."
    if [[ -d "resources" && -L "resources" ]]; then
        echo "    ✅ Resources symlink created successfully"
        if [[ -d "resources/models" ]]; then
            local model_count=$(find resources/models -name "*.hef" 2>/dev/null | wc -l)
            echo "    ✅ Found $model_count model files"
        else
            echo "    ⚠️  Models directory not found"
        fi
    else
        echo "    ❌ Resources directory not properly set up"
        success=false
    fi
    
    
    echo "  📄 Checking environment file..."
    if [[ -f ".env" ]]; then
        echo "    ✅ Environment file created successfully"
    else
        echo "    ❌ Environment file not found"
        success=false
    fi
    
    echo "  🔨 Checking C++ postprocess compilation..."
    # Check for compiled C++ libraries in the expected location
    if [[ -d "/usr/local/hailo/resources/so" ]]; then
        local so_count=$(find /usr/local/hailo/resources/so -name "*.so" 2>/dev/null | wc -l)
        if [[ $so_count -gt 0 ]]; then
            echo "    ✅ Found $so_count compiled C++ postprocess libraries"
        else
            echo "    ⚠️  No compiled C++ postprocess libraries found"
            echo "       This may affect some advanced features"
        fi
    else
        echo "    ⚠️  C++ library directory not found"
        echo "       This may affect some advanced features"
    fi
    
    return 0
}

# Run verification
verify_installation

# Final ownership fix for all project files
echo ""
echo "🔧 Ensuring all project files have correct ownership..."
fix_ownership "${SCRIPT_DIR}"
echo "✅ Project files ownership fixed to ${ORIGINAL_USER}:${ORIGINAL_GROUP}"

echo ""
echo "✅ Installation process completed!"
echo "Virtual environment: ${VENV_NAME}"
echo "Location: ${VENV_PATH}"
echo "User: ${ORIGINAL_USER}"
echo "Group: ${ORIGINAL_GROUP}"

echo "✅ All done! Your package is now in '${VENV_NAME}'."
echo "source setup_env.sh to setup the environment"
