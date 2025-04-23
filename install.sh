#!/bin/bash
set -e

# Parse args
INSTALL_GSTREAMER=false
INSTALL_PIPELINES=false

for arg in "$@"; do
    case $arg in
        --gstreamer-only) INSTALL_GSTREAMER=true ;;
        --pipelines-only) INSTALL_GSTREAMER=true; INSTALL_PIPELINES=true ;;
        --all) INSTALL_GSTREAMER=true; INSTALL_PIPELINES=true ;;
    esac
done

# Create resource directories
echo "🔧 Creating resource directories..."
for dir in models/hailo8 models/hailo8l videos so; do
    sudo mkdir -p "/usr/local/hailo/resources/$dir"
done

sudo chown -R $SUDO_USER:$SUDO_USER /usr/local/hailo/resources
sudo chmod -R 755 /usr/local/hailo/resources

# Check installation types and status 
# Hailort Driver VERSION
HAILORT_DRIVER_VERSION=$(python3 hailo_apps_infra/common/hailo_common/installation_utils.py --pkg hailort-pcie-driver --type system)
echo "System hailort-pcie-driver VERSION: $HAILORT_DRIVER_VERSION"
if [ "$HAILORT_DRIVER_VERSION" = "None" ] || [ -z "$HAILORT_DRIVER_VERSION" ]; then
    echo "hailort-driver is not installed or version not found."
    echo "Please install hailort-driver using the installation script."
    exit 1
else
    echo "hailort-driver is installed, version: $HAILORT_DRIVER_VERSION"
fi

# Hailort VERSION
HAILORT_VERSION=$(python3 hailo_apps_infra/common/hailo_common/installation_utils.py --pkg hailort --type system)
echo "System hailort VERSION: $HAILORT_VERSION"
if [ "$HAILORT_VERSION" = "None" ] || [ -z "$HAILORT_VERSION" ]; then
    echo "hailort is not installed or version not found."
    echo "Please install hailort using the installation script."
    exit 1
else
    echo "hailort is installed, version: $HAILORT_VERSION"
fi

# Hailo-tappas VERSION
HAILO_TAPPAS_VERSION=$(python3 hailo_apps_infra/common/hailo_common/installation_utils.py --pkg hailo-tappas --type system)
echo "System hailo-tappas VERSION: $HAILO_TAPPAS_VERSION"
if [ "$HAILO_TAPPAS_VERSION" = "None" ] || [ -z "$HAILO_TAPPAS_VERSION" ]; then
    echo "hailo-tappas is not installed or version not found."
    echo "Please install hailo-tappas using the installation script."
    exit 1
else
    echo "hailo-tappas is installed, version: $HAILO_TAPPAS_VERSION"
fi

# Hailo-tappas-core VERSION
HAILO_TAPPAS_CORE_VERSION=$(python3 hailo_apps_infra/common/hailo_common/installation_utils.py --pkg hailo-tappas-core --type system)
echo "System hailo-tappas-core VERSION: $HAILO_TAPPAS_CORE_VERSION"
if [ "$HAILO_TAPPAS_CORE_VERSION" = "None" ] || [ -z "$HAILO_TAPPAS_CORE_VERSION" ]; then
    echo "hailo-tappas-core is not installed or version not found."
    echo "Please install hailo-tappas-core using the installation script."
    exit 1
else
    echo "hailo-tappas-core is installed, version: $HAILO_TAPPAS_CORE_VERSION"
fi

INSTALL_PYHAILORT=false
INSTALL_TAPPAS_CORE=false


# Python HailoRT VERSION in Host
HOST_HAILORT_PYTHON_VERSION=$(python3 hailo_apps_infra/common/hailo_common/installation_utils.py --pkg hailort --type pip)
echo "Python hailort VERSION: $HOST_HAILORT_PYTHON_VERSION"
if [ "$HOST_HAILORT_PYTHON_VERSION" = "None" ] || [ -z "$HOST_HAILORT_PYTHON_VERSION" ]; then
    echo "Python hailort is not installed on the host system."
    echo "Will be installing it in the virtual environment."
    INSTALL_PYHAILORT=true
else
    echo "Python hailort is installed, version: $HOST_HAILORT_PYTHON_VERSION"
fi

# Python Hailo Tappas Core Version in host
HOST_HAILO_TAPPAS_CORE_PYTHON_VERSION=$(python3 hailo_apps_infra/common/hailo_common/installation_utils.py --pkg hailo-tappas-core --type pip)
echo "Python hailo-tappas-core VERSION: $HOST_HAILO_TAPPAS_CORE_PYTHON_VERSION"
if [ "$HOST_HAILO_TAPPAS_CORE_PYTHON_VERSION" = "None" ] || [ -z "$HOST_HAILO_TAPPAS_CORE_PYTHON_VERSION" ]; then
    echo "Python hailo-tappas-core is not installed on the host system."
    echo "Will be installing it in the virtual environment."
    INSTALL_TAPPAS_CORE=true
else
    echo "Python hailo-tappas-core is installed, version: $HOST_HAILO_TAPPAS_CORE_PYTHON_VERSION"
fi


VENV_NAME=$(python3 hailo_apps_infra/common/hailo_common/get_config_values.py virtual_env_name)
if [ -z "$VENV_NAME" ]; then
    echo "❌ Failed to get virtual environment name from config."
    echo "Using default name: 'hailo_infra_venv'"
    VENV_NAME=$(python3 -c "from hailo_apps_infra.common.hailo_common.get_config_values import get_default_config_value; print(get_default_config_value('virtual_env_name'))")
fi

if [ -d "$VENV_NAME" ]; then
    echo "✅ Virtual environment already exists: $VENV_NAME"
    source "$VENV_NAME/bin/activate"

    # Check if hailo-tappas-core is installed in the venv
    if not (pip show hailo-tappas-core > /dev/null 2>&1); then
        INSTALL_TAPPAS_CORE=true
    fi

    # Check if hailort is installed in the venv
    if not (pip show hailort > /dev/null 2>&1); then
        INSTALL_PYHAILORT=true
    fi
else
    # VENV does not exist
    if [ INSTALL_PYHAILORT == true and INSTALL_TAPPAS_CORE == true]; then
        echo "Both Hailort and Hailo-tappas-core are not installed on the system."
        echo "Creating virtual environment without --system-site-packages."
        python3 -m venv "$VENV_NAME"
    else
        echo "Creating virtual environment with --system-site-packages."
        python3 -m venv --system-site-packages "$VENV_NAME"
    fi
    # Check if the virtual environment was created successfully
    echo "✅ Virtual environment created: $VENV_NAME"
    source "$VENV_NAME/bin/activate"
fi


# Invoke python_installation.py to install missing packages.
python3 hailo-apps-infra/hailo_apps_infra/installation/hailo_installation/python_installation.py \
  $( [ "$INSTALL_PYHAILORT" = true ] && echo "--install-pyhailort --pyhailort-version $HAILORT_VERSION" ) \
  $( [ "$INSTALL_TAPPAS_CORE" = true ] && echo "--install-tappas-core --tappas-version $TAPPAS_CORE_VERSION" )

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

# Step 2: Ensure it is writable
if [[ ! -w "$ENV_PATH" ]]; then
    echo "⚠️  .env exists but is not writable. Trying to fix permissions..."
    chmod u+w "$ENV_PATH" || {
        echo "❌ Failed to fix permissions for $ENV_PATH. Please run with sudo or fix manually."
        exit 1
    }
fi

echo "📦 Installing base tooling..."
pip install --upgrade pip setuptools wheel

# Core modules (always)
echo "📦 Installing core modules..."
pip install -e ./hailo_apps_infra/common
pip install -e ./hailo_apps_infra/config
pip install -e ./hailo_apps_infra/installation

# Optional modules
$INSTALL_GSTREAMER && pip install -e ./hailo_apps_infra/gstreamer
$INSTALL_PIPELINES && pip install -e ./hailo_apps_infra/pipelines

# 🔧 Runtime requirements
echo "📦 Installing shared runtime dependencies..."
pip install -r requirements.txt

# Post-install setup
echo "⚙️ Running post-install setup..."
python3 -m hailo_installation.post_install


echo "✅ All done! To activate environment later, run:"
echo "    source $VENV_NAME/bin/activate"
