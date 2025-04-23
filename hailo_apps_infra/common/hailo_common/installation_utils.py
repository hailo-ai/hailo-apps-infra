import argparse
import json
import logging
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from hailo_common.hailo_rpi_common import detect_pkg_installed
from hailo_common.utils import detect_hailo_package_version

logger = logging.getLogger("hailo-utils")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_PATH = PROJECT_ROOT / "resources"

def detect_pip_package_installed(package_name):
    try:
        result = subprocess.run(
            ['pip', 'show', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to detect pip package {package_name}: {e}")
        return False

def detect_pip_package_version(package_name):
    try:
        result = subprocess.run(
            ['pip', 'show', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to detect version for pip package {package_name}: {e}")
        return None

def check_package_info(pkg, pkg_type):
    if pkg_type == "system":
        installed = detect_pkg_installed(pkg)
        version = detect_hailo_package_version(pkg) if installed else None
    elif pkg_type == "pip":
        installed = detect_pip_package_installed(pkg)
        version = detect_pip_package_version(pkg) if installed else None
    else:
        raise ValueError(f"Unknown package type: {pkg_type}")
    return version

def main():
    parser = argparse.ArgumentParser(description="Check package info from installation_utils")
    parser.add_argument("--pkg", required=True, help="Name of the package to check")
    parser.add_argument("--type", required=True, choices=["system", "pip"], help="Package type: 'system' or 'pip'")
    args = parser.parse_args()
    version = check_package_info(args.pkg, args.type)
    print(version)

if __name__ == '__main__':
    main()