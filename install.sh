#!/bin/bash
set -e

echo "🔧 Creating virtual environment in .venv (if not exists)..."
python3 -m venv .venv

echo "✅ Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing hailo-apps-infra in editable mode..."
pip install --upgrade pip setuptools wheel
pip install -e .

echo "📦 Installing runtime requirements..."
pip install -r requirements.txt

echo "🚀 Running hailo-apps-infra install script..."
python3 -m hailo_apps_infra.install.install

echo "✅ All done! Use this to activate later:"
echo "    source .venv/bin/activate"
