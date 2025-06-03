#!/usr/bin/env python3
"""
Installer for Hailo Python bindings: pyHailoRT (hailort) and hailo-tappas-core.
Installs into an existing virtual environment or the current Python environment.
Supports downloading wheel files from a base URL if not already present locally.
"""
import sys
from pathlib import Path
# Ensure hailo_core is importable from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/dev/hailo-apps-infra/hailo_apps_infra
sys.path.insert(0, str(PROJECT_ROOT))
# ─── other imports ────────────────────────────────────────────────────────────
import argparse
import subprocess
import os
import logging
import platform
import urllib.request
from hailo_core.hailo_common.defines import (
    SERVER_URL_DEFAULT,
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCE_STORAGE_DIR_NAME,
)

DOWNLOAD_DIR = Path(RESOURCES_ROOT_PATH_DEFAULT) / RESOURCE_STORAGE_DIR_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_pip_cmd(venv_path: str = None):
    if venv_path:
        pip_path = Path(venv_path) / "bin" / "pip"
        if not pip_path.exists():
            logger.error(f"pip not found in virtualenv at '{pip_path}'")
            sys.exit(1)
        return [str(pip_path)]
    return [sys.executable, "-m", "pip"]

def download_wheel(url: str, dest_path: Path):
    logger.info(f"Downloading wheel from {url}")
    try:
        # Build a Request with a common User-Agent
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out_file:
            out_file.write(resp.read())

        logger.info(f"✅ Downloaded: {dest_path}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def get_platform_tag():
    machine = platform.machine()
    if "x86_64" in machine:
        return "linux_x86_64"
    elif "aarch64" in machine or "arm64" in machine:
        return "linux_aarch64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

def get_python_tag():
    return f"cp{sys.version_info.major}{sys.version_info.minor}-cp{sys.version_info.major}{sys.version_info.minor}"

def download_pyhailort_wheel(version: str, download_dir: Path = DOWNLOAD_DIR, server_url: str = SERVER_URL_DEFAULT) -> Path:
    py_tag = get_python_tag()
    platform_tag = get_platform_tag()
    wheel_name = f"hailort-{version}-{py_tag}-{platform_tag}.whl"
    wheel_path = download_dir / wheel_name
    if not wheel_path.exists():
        url = f"{server_url}/{wheel_name}"
        download_wheel(url, wheel_path)
    else:
        logger.info(f"Already exists: {wheel_path}")
    return wheel_path

def download_tappas_core_wheel(version: str, download_dir: Path = DOWNLOAD_DIR, server_url: str = SERVER_URL_DEFAULT) -> Path:
    wheel_name = f"tappas_core_python_binding-{version}-py3-none-any.whl"
    wheel_path = download_dir / wheel_name
    if not wheel_path.exists():
        url = f"{server_url}/{wheel_name}"
        download_wheel(url, wheel_path)
    else:
        logger.info(f"Already exists: {wheel_path}")
    return wheel_path

def install_wheel(pip_cmd, wheel_path: Path):
    if not wheel_path.exists():
        logger.error(f"Wheel file not found: {wheel_path}")
        sys.exit(1)
    cmd = pip_cmd + ["install", str(wheel_path)]
    logger.info(f"Installing wheel: {wheel_path.name}")
    subprocess.check_call(cmd)

def install_pyhailort(version: str, venv_path: str):
    pip_cmd = get_pip_cmd(venv_path)
    wheel_path = download_pyhailort_wheel(version)
    install_wheel(pip_cmd, wheel_path)

def install_tappas_core(version: str, venv_path: str):
    pip_cmd = get_pip_cmd(venv_path)
    wheel_path = download_tappas_core_wheel(version)
    install_wheel(pip_cmd, wheel_path)

def list_installed(pip_cmd):
    subprocess.run(pip_cmd + ["list", "--format=columns"])

def main():
    parser = argparse.ArgumentParser(description="Install pyHailoRT (hailort) and hailo-tappas-core")
    parser.add_argument("--venv-path", help="Path to existing virtualenv")
    parser.add_argument("--install-pyhailort", action="store_true")
    parser.add_argument("--pyhailort-version")
    parser.add_argument("--install-tappas-core", action="store_true")
    parser.add_argument("--tappas-version")
    args = parser.parse_args()


    if not args.install_pyhailort and not args.install_tappas_core:
        parser.error("Specify --install-pyhailort and/or --install-tappas-core")

    venv = args.venv_path
    if args.venv_path is None:
        venv = os.environ.get("VIRTUAL_ENV")
        if not venv and hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
            venv = sys.prefix
        if venv:
            args.venv_path = venv
            logger.info(f"🔍 Detected active virtualenv at '{venv}', using it.")

    pip_cmd = get_pip_cmd(args.venv_path)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if args.install_pyhailort:
        install_pyhailort(args.pyhailort_version, args.venv_path)

    if args.install_tappas_core:
        install_tappas_core(args.tappas_version, args.venv_path)

    list_installed(pip_cmd)
    logger.info("✅ Installation complete.")

if __name__ == "__main__":
    main()
