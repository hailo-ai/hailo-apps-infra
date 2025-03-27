#!/bin/bash
set -e

VENV_NAME="infra-venv"

if [ ! -d "$VENV_NAME" ]; then
    echo "🔧 Creating virtual environment in $VENV_NAME..."
    python3 -m venv "$VENV_NAME" --system-site-packages
else
    echo "✅ Virtual environment already exists: $VENV_NAME"
fi

echo "✅ Activating virtual environment..."
source "$VENV_NAME/bin/activate"

echo "📦 Installing hailo-apps-infra in editable mode..."
pip install --upgrade pip setuptools wheel
pip install -e .

echo "📦 Installing runtime requirements..."
pip install -r requirements.txt

echo "🚀 Running hailo-apps-infra install script..."
python3 -m hailo_apps_infra.install.install

echo "✅ All done! Use this to activate later:"
echo "    source $VENV_NAME/bin/activate"
