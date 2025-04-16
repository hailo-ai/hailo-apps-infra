#!/usr/bin/env python3

import subprocess
import sys
import os
import platform
import argparse
import urllib.request
import importlib.util
import logging
from pathlib import Path

# Import utilities from common files if available
try:
    from hailo_common.hailo_rpi_common import detect_device_arch, detect_hailo_arch, run_command
except ImportError:
    # Fallback implementations
    def detect_device_arch():
        """
        Detect the host architecture: rpi, arm, or x86.
        Returns:
            str: One of "rpi", "arm", "x86", or "unknown"
        """
        machine = platform.machine().lower()
        system = platform.system().lower()

        if "arm" in machine or "aarch64" in machine:
            # Detect Raspberry Pi based on OS and CPU
            if system == "linux" and (
                "raspberrypi" in platform.uname().node or
                "pi" in platform.uname().node
            ):
                return "rpi"
            else:
                return "arm"
        elif "x86" in machine or "amd64" in machine:
            return "x86"
        else:
            return "unknown"

    def detect_hailo_arch():
        try:
            # Run the hailortcli command to get device information
            result = subprocess.run(['hailortcli', 'fw-control', 'identify'], 
                                   capture_output=True, text=True)

            # Check if the command was successful
            if result.returncode != 0:
                print(f"Error running hailortcli: {result.stderr}")
                return None

            # Search for the "Device Architecture" line in the output
            for line in result.stdout.split('\n'):
                if "Device Architecture" in line:
                    if "HAILO8L" in line:
                        return "hailo8l"
                    elif "HAILO8" in line:
                        return "hailo8"

            print("Could not determine Hailo architecture from device information.")
            return None
        except Exception as e:
            print(f"An error occurred while detecting Hailo architecture: {e}")
            return None

    def run_command(command, error_msg, logger=None):
        """
        Run a shell command and log the output.
        Args:
            command (str): The shell command to run.
            error_msg (str): The error message to log if the command fails.
            logger (logging.Logger, optional): The logger to use. If None, a default logger will be created.
        """
        if logger is not None:
            logger.info(f"Running: {command}")
        else:
            print(f"Running: {command}")
        result = subprocess.run(command, shell=True)
        if result.returncode != 0:
            if logger is not None:
                logger.error(f"{error_msg} (exit code {result.returncode})")
            else:
                print(f"{error_msg} (exit code {result.returncode})")
            exit(result.returncode)

# --- Configuration ---
BASE_URL = "http://dev-public.hailo.ai/2025_01"
DEFAULT_VENV = "hailo_venv"
HAILORT_VERSION = "4.20.0"
TAPPAS_CORE_VERSION = "3.31.0"
DOWNLOAD_DIR = "hailo_temp_resources"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hailo-installer")


def package_is_importable(package_name):
    """Check if a package can be imported in the current Python environment."""
    return importlib.util.find_spec(package_name) is not None


def get_package_version(package_name):
    """Get the version of an installed package."""
    try:
        # Try to import the package and get its version
        package = __import__(package_name)
        return getattr(package, "__version__", "unknown")
    except (ImportError, AttributeError):
        try:
            # Alternative method using pkg_resources if available
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except (ImportError, pkg_resources.DistributionNotFound):
            return None


def get_python_tag():
    """Get the Python tag for the wheel filename."""
    major, minor = sys.version_info[:2]
    return f"cp{major}{minor}-cp{major}{minor}"


def get_platform_tag():
    """Get the platform tag for the wheel filename."""
    machine = platform.machine()
    if "x86_64" in machine:
        return "linux_x86_64"
    elif "aarch64" in machine:
        return "linux_aarch64"
    elif "arm" in machine:
        # For older ARM platforms that are not aarch64
        return "linux_armv7l"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")


def download_file(filename, dest):
    """Download a file from the server."""
    url = f"{BASE_URL}/{filename}"
    logger.info(f"Downloading {url}...")
    
    try:
        Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, dest)
        return True
    except urllib.error.URLError as e:
        logger.error(f"Error downloading {url}: {e}")
        return False


def create_virtualenv(venv_dir):
    """Create a virtual environment."""
    if os.path.exists(venv_dir):
        logger.info(f"Using existing virtualenv: {venv_dir}")
        return True
    
    logger.info(f"Creating virtualenv: {venv_dir}")
    try:
        subprocess.run([sys.executable, "-m", "virtualenv", venv_dir], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtualenv: {e}")
        return False


def install_wheels(venv_dir, wheels):
    """Install wheels into a virtualenv."""
    pip_path = os.path.join(venv_dir, "bin", "pip")
    
    # Upgrade pip first
    try:
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e}")
        return False
    
    # Install each wheel
    for wheel in wheels:
        if not os.path.exists(wheel):
            logger.error(f"Wheel file not found: {wheel}")
            return False
        
        logger.info(f"Installing wheel: {wheel}")
        try:
            subprocess.run([pip_path, "install", wheel], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install wheel {wheel}: {e}")
            return False
    
    return True


def print_installed_versions(venv_dir=None):
    """Print installed versions of Hailo packages."""
    if venv_dir:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
        logger.info(f"\n✅ Installed packages in virtualenv {venv_dir}:\n")
        for line in result.stdout.splitlines():
            if "hailo" in line.lower() or "tappas" in line.lower():
                print(line)
    else:
        # Print system packages
        hailort_ver = get_package_version("hailort") or "not installed"
        tappas_ver = get_package_version("hailo_tappas") or "not installed"
        print(f"hailort: {hailort_ver}")
        print(f"hailo_tappas: {tappas_ver}")


def main():
    parser = argparse.ArgumentParser(description="Hailo Python Bindings Installer")
    parser.add_argument("--venv-name", default=DEFAULT_VENV, 
                        help=f"Name of the virtualenv (default: {DEFAULT_VENV})")
    parser.add_argument("--hailort-version", default=HAILORT_VERSION,
                        help=f"HailoRT version to install (default: {HAILORT_VERSION})")
    parser.add_argument("--tappas-version", default=TAPPAS_CORE_VERSION,
                        help=f"TAPPAS core version to install (default: {TAPPAS_CORE_VERSION})")
    parser.add_argument("--hailort-wheel", 
                        help="Path to HailoRT wheel file (if already downloaded)")
    parser.add_argument("--tappas-wheel", 
                        help="Path to TAPPAS wheel file (if already downloaded)")
    parser.add_argument("--force-venv", action="store_true",
                        help="Force installation in virtualenv even if packages are installed globally")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Detect system architecture
    device_arch = detect_device_arch()
    hailo_arch = detect_hailo_arch()
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    logger.info(f"System details:")
    logger.info(f"  - Device architecture: {device_arch}")
    logger.info(f"  - Hailo architecture: {hailo_arch}")
    logger.info(f"  - Python version: {py_ver}")
    
    # Check if packages are already installed globally
    hailort_installed = package_is_importable("hailort")
    tappas_installed = package_is_importable("hailo_tappas")
    
    if hailort_installed and tappas_installed and not args.force_venv:
        logger.info("✅ 'hailort' and 'hailo_tappas' are already installed globally.")
        hailort_ver = get_package_version("hailort")
        tappas_ver = get_package_version("hailo_tappas")
        logger.info(f"  - hailort version: {hailort_ver}")
        logger.info(f"  - hailo_tappas version: {tappas_ver}")
        return
    
    # Prepare for installation in virtualenv
    venv_dir = args.venv_name
    
    # Determine wheel paths (either from args or construct default paths)
    py_tag = get_python_tag()
    platform_tag = get_platform_tag()
    
    if args.hailort_wheel:
        hailort_wheel_path = args.hailort_wheel
    else:
        hailort_whl_name = f"hailort-{args.hailort_version}-{py_tag}-{platform_tag}.whl"
        hailort_wheel_path = os.path.join(DOWNLOAD_DIR, hailort_whl_name)
        
    if args.tappas_wheel:
        tappas_wheel_path = args.tappas_wheel
    else:
        tappas_whl_name = f"tappas_core_python_binding-{args.tappas_version}-py3-none-any.whl"
        tappas_wheel_path = os.path.join(DOWNLOAD_DIR, tappas_whl_name)
    
    # Download wheels if needed
    if not os.path.exists(hailort_wheel_path):
        hailort_whl_name = os.path.basename(hailort_wheel_path)
        if not download_file(hailort_whl_name, hailort_wheel_path):
            logger.error(f"Failed to download HailoRT wheel: {hailort_whl_name}")
            return
    else:
        logger.info(f"Found cached wheel: {hailort_wheel_path}")
    
    if not os.path.exists(tappas_wheel_path):
        tappas_whl_name = os.path.basename(tappas_wheel_path)
        if not download_file(tappas_whl_name, tappas_wheel_path):
            logger.error(f"Failed to download TAPPAS wheel: {tappas_whl_name}")
            return
    else:
        logger.info(f"Found cached wheel: {tappas_wheel_path}")
    
    # Create or reuse virtualenv
    if not create_virtualenv(venv_dir):
        logger.error("Failed to set up virtualenv")
        return
    
    # Install wheels
    if not install_wheels(venv_dir, [hailort_wheel_path, tappas_wheel_path]):
        logger.error("Failed to install wheels")
        return
    
    # Print installed versions
    print_installed_versions(venv_dir)
    
    logger.info(f"""
✅ Installation complete.
   To activate the environment, run:
     source {venv_dir}/bin/activate
""")


if __name__ == "__main__":
    main()