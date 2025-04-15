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

# check where the x86 goes (should be fixed in brnach CSG-temp)
VENV_NAME=$(python3 hailo_apps_infra/common/hailo_common/get_config_values.py virtual_env_name)
if [ -z "$VENV_NAME" ]; then
    echo "❌ Failed to get virtual environment name from config."
    ECHO "Using default name: 'hailo_infra_venv'"
    VENV_NAME="hailo_infra_venv"
fi

if [ ! -d "$VENV_NAME" ]; then
    echo "🔧 Creating virtual environment in $VENV_NAME..."
    python3 -m venv "$VENV_NAME" --system-site-packages
    # 1a) On x86 hosts, immediately install x86 deps
    if detect_x86; then
        install_x86_deps
    else
        echo "ℹ️  Non‑x86 host; skipping x86‑only deps on fresh venv."
    fi
else
    echo "✅ Virtual environment already exists: $VENV_NAME"
    source "$VENV_NAME/bin/activate"
    
    if detect_x86 && ! check_hailo_installed; then
        echo "🔧 Installing x86 dependencies..."
        install_x86_deps
    else
        echo "ℹ️  Non‑x86 host; skipping x86‑only deps on existing venv."
    fi
fi

echo "✅ Activating virtual environment..."
source "$VENV_NAME/bin/activate"

ENV_FILE=".env"
ENV_PATH="$(pwd)/$ENV_FILE"

# Step 1: Create the .env file if it doesn't exist
if [[ ! -f "$ENV_PATH" ]]; then
    echo "🔧 Creating .env file at $ENV_PATH"
    touch "$ENV_PATH"
    chmod 666 "$ENV_PATH"  # rw-rw-r-- for user/group
else
    echo "✅ .env already exists at $ENV_PATH"
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
python3 -m hailo_installation.install


echo "✅ All done! To activate environment later, run:"
echo "    source $VENV_NAME/bin/activate"

# Detect if we’re running on an x86 host
detect_x86() {
    local arch
    arch=$(uname -m)
    if [[ "$arch" =~ ^(x86_64|i[3-6]86)$ ]]; then
        return 0   # true
    else
        return 1   # false
    fi
}

# Install x86‑only dependencies inside the venv
install_x86_deps() {
    echo "🔧 Installing x86 dependencies in $VENV_NAME..."
    # shellcheck disable=SC1091
    source "$VENV_NAME/bin/activate"
    pip install pyhailort tappas-core-bindings
    deactivate
    echo "✅ x86 dependencies installed."
}

check_hailo_installed(){
    # Check if Hailo is installed inside the virtual env on x86 hosts
}