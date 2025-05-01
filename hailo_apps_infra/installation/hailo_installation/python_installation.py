#!/usr/bin/env python3
"""
Installer for Hailo Python bindings: pyHailoRT (hailort) and hailo-tappas-core.
Installs into an existing virtual environment or the current Python environment.
Supports downloading wheel files from a base URL if not already present locally.
"""
import argparse
import subprocess
import sys
import os
import logging
import platform
from pathlib import Path
import urllib.request


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_pip_cmd(venv_path: str = None):
    """
    Return the pip command for the target environment.
    If venv_path is given, uses venv_path/bin/pip, otherwise uses current Python's pip.
    """
    if venv_path:
        pip_path = Path(venv_path) / "bin" / "pip"
        if not pip_path.exists():
            logger.error(f"pip not found in virtualenv at '{pip_path}'")
            sys.exit(1)
        return [str(pip_path)]
    return [sys.executable, "-m", "pip"]


def download_wheel(url: str, dest_path: Path):
    """Download a wheel file from URL to dest_path."""
    logger.info(f"Downloading wheel from {url}")
    try:
        urllib.request.urlretrieve(url, str(dest_path))
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        sys.exit(1)


def install_wheel(pip_cmd, wheel_path: Path):
    """Install a wheel file via pip_cmd."""
    if not wheel_path.exists():
        logger.error(f"Wheel file not found: {wheel_path}")
        sys.exit(1)
    cmd = pip_cmd + ["install", str(wheel_path)]
    logger.info(f"Installing wheel: {wheel_path.name}")
    subprocess.check_call(cmd)


def list_installed(pip_cmd):
    """List installed hailo-related packages in the target environment."""
    subprocess.run(pip_cmd + ["list", "--format=columns"])  


def main():
    parser = argparse.ArgumentParser(
        description="Install pyHailoRT (hailort) and hailo-tappas-core into an existing venv or current env"
    )
    parser.add_argument(
        "--venv-path",
        help="Path to existing virtualenv; if omitted, uses current Python environment"
    )
    parser.add_argument(
        "--install-pyhailort", action="store_true",
        help="Install pyHailoRT (hailort) package"
    )
    parser.add_argument(
        "--pyhailort-version",
        help="Version of pyHailoRT (hailort) to install"
    )
    parser.add_argument(
        "--pyhailort-wheel",
        help="Path to pyHailoRT (hailort) wheel file"
    )
    parser.add_argument(
        "--install-tappas-core", action="store_true",
        help="Install hailo-tappas-core package"
    )
    parser.add_argument(
        "--tappas-version",
        help="Version of hailo-tappas-core to install"
    )
    parser.add_argument(
        "--tappas-wheel",
        help="Path to hailo-tappas-core wheel file"
    )
    parser.add_argument(
        "--download-dir",
        default=os.environ.get("DEB_WHL_DIR", "hailo_temp_resources"),
        help="Directory to download wheel files to"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # If wheel paths are provided, assume installation
    if args.pyhailort_wheel:
        args.install_pyhailort = True
    if args.tappas_wheel:
        args.install_tappas_core = True

    if not args.install_pyhailort and not args.install_tappas_core:
        parser.error("No installation target specified; use --install-pyhailort and/or --install-tappas-core or provide wheel paths.")
        exit(1)

    server_url = "http://dev-public.hailo.ai/2025_01"
    if not server_url:
        logger.error("Server URL not found in config.")
        sys.exit(1)

    pip_cmd = get_pip_cmd(args.venv_path)
    logger.debug(f"Using pip command: {' '.join(pip_cmd)}")

    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    # Install pyHailoRT
    if args.install_pyhailort:
        if args.pyhailort_wheel:
            wheel_path = Path(args.pyhailort_wheel)
        else:
            if not args.pyhailort_version:
                parser.error("--pyhailort-version is required when not using --pyhailort-wheel")
                exit(1)
            version = args.pyhailort_version
            py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}-cp{sys.version_info.major}{sys.version_info.minor}"
            machine = platform.machine()
            if "x86_64" in machine:
                platform_tag = "linux_x86_64"
            elif "aarch64" in machine or "arm64" in machine:
                platform_tag = "linux_aarch64"
            else:
                logger.error(f"Unsupported architecture: {machine}")
                sys.exit(1)
            wheel_name = f"hailort-{version}-{py_tag}-{platform_tag}.whl"
            wheel_path = download_dir / wheel_name
            if not wheel_path.exists():
                url = f"{server_url}/{wheel_name}"
                download_wheel(url, wheel_path)
        install_wheel(pip_cmd, wheel_path)

    # Install hailo-tappas-core
    if args.install_tappas_core:
        if args.tappas_wheel:
            wheel_path = Path(args.tappas_wheel)
        else:
            if not args.tappas_version:
                parser.error("--tappas-version is required when not using --tappas-wheel")
                exit(1)
            version = args.tappas_version
            wheel_name = f"tappas_core_python_binding-{version}-py3-none-any.whl"
            wheel_path = download_dir / wheel_name
            if not wheel_path.exists():
                url = f"{server_url}/{wheel_name}"
                download_wheel(url, wheel_path)
        install_wheel(pip_cmd, wheel_path)

    # List installed packages
    list_installed(pip_cmd)
    logger.info("✅ Installation complete.")


if __name__ == "__main__":
    main()