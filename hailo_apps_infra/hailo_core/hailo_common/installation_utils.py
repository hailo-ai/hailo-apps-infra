"""
Installation-related utilities.
"""
import platform
import shlex
import subprocess
from pathlib import Path
import sys
from .defines import (
    X86_POSSIBLE_NAME,
    ARM_POSSIBLE_NAME,
    RPI_POSSIBLE_NAME,
    HAILO8_ARCH_CAPS,
    HAILO8L_ARCH_CAPS,
    HAILO_FW_CONTROL_CMD,
    X86_NAME_I,
    RPI_NAME_I,
    ARM_NAME_I,
    LINUX_SYSTEM_NAME_I,
    UNKNOWN_NAME_I,
    HAILO8_ARCH,
    HAILO8L_ARCH,
    PIP_CMD, 
    HAILORT_PACKAGE,
    HAILO_TAPPAS_CORE_PYTHON,
    HAILO_TAPPAS,
    HAILO_TAPPAS_CORE,
    HAILO_TAPPAS_CORE_PYTHON_NAMES,
    HAILO10H_ARCH_CAPS,
    HAILO10H_ARCH,
)
#logger = __import__('logging').getLogger("hailo_install")

def detect_pkg_config_version(pkg_name: str) -> str:
    """
    Get the version of a package using pkg-config.
    Returns an empty string if the package is not found.
    """
    try:
        version = subprocess.check_output(
            ["pkg-config", "--modversion", pkg_name],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return version.strip()
    except subprocess.CalledProcessError:
        return ""

def auto_detect_pkg_config(pkg_name: str) -> bool:
    """
    Automatically detect the version of a package using pkg-config.
    Returns the version if found, otherwise returns an empty string.
    """
    try:
        version = subprocess.check_output(
            ["pkg-config", "--exists", pkg_name],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def detect_system_pkg_version(pkg_name: str) -> str:
    """
    Get the installed version of a system package via dpkg-query.
    Returns an empty string if the package is not installed.
    """
    try:
        version = subprocess.check_output(
            ["dpkg-query", "-W", f"-f=${{Version}}", pkg_name],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return version.strip()
    except subprocess.CalledProcessError:
        return ""
    
def detect_host_arch() -> str:  
    """Detect host: rpi, arm, x86, or unknown."""  
    machine_name = platform.machine().lower()  
    system_name = platform.system().lower()  
    if machine_name in X86_POSSIBLE_NAME:   
        return X86_NAME_I
    if machine_name in ARM_POSSIBLE_NAME:
        if system_name == LINUX_SYSTEM_NAME_I and platform.uname().node in RPI_POSSIBLE_NAME:  
            return RPI_NAME_I
        return ARM_NAME_I
    return UNKNOWN_NAME_I 
  
def detect_hailo_arch() -> str | None:
    """Use hailortcli to identify Hailo architecture."""
    try:
        # split into ["hailortcli","fw-control","identify"]
        args = shlex.split(HAILO_FW_CONTROL_CMD)
        res = subprocess.run(args, capture_output=True, text=True)
        if res.returncode != 0:
            return None
        for line in res.stdout.splitlines():
            if HAILO8L_ARCH_CAPS in line:
                return HAILO8L_ARCH
            if HAILO8_ARCH_CAPS in line:
                return HAILO8_ARCH
            if HAILO10H_ARCH_CAPS in line:
                return HAILO10H_ARCH
    except Exception:
        return None
    return None

def detect_pkg_installed(pkg_name: str) -> bool:
    """
    Check if a package is installed on the system.
    Args:
        pkg_name (str): The name of the package to check.
    Returns:
        bool: True if the package is installed, False otherwise.
    """
    try:
        subprocess.check_output(["dpkg", "-s", pkg_name])
        return True
    except subprocess.CalledProcessError:
        return False
    
def detect_pip_package_installed(pkg: str) -> bool:
    """Check if a pip package is installed."""
    try:
        result = subprocess.run(
            [PIP_CMD, 'show', pkg], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=None
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_pip_package_version(pkg: str) -> str | None:
    """Get pip package version if installed."""
    try:
        output = run_command_with_output([PIP_CMD, 'show', pkg])
        for line in output.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
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
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        if logger is not None:
            logger.error(f"{error_msg} (exit code {result.returncode})")
        else:
            print(f"{error_msg} (exit code {result.returncode})")
        exit(result.returncode)


def run_command_with_output(cmd: list[str]) -> str:
    """Run a shell command and return stdout."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result.stdout


def create_symlink(src: str, dst: str) -> None:
    """Create or replace a symlink."""
    import os
    if os.path.islink(dst) or os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)

def auto_detect_hailort_python_bindings() -> bool:
    """
    Automatically detect the installed HailoRT version for Python.
    Returns:
        bool: True if HailoRT Python bindings are installed, False otherwise.
    """
    if detect_pip_package_installed(HAILORT_PACKAGE):
        return True
    return False

def auto_detect_hailort_version() -> str:
    """
    Automatically detect the installed HailoRT version.
    Returns:
        str: The detected HailoRT version.
    """
    if detect_pkg_installed(HAILORT_PACKAGE):
        return detect_system_pkg_version(HAILORT_PACKAGE)
    else:
        print("⚠ Could not detect HailoRT version, please install HailoRT.")
        return None
    
def auto_detect_tappas_variant() -> str:
    """
    Automatically detect the TAPPAS variant based on installed packages.
    Returns:
        str: The detected TAPPAS variant.
    """
    if detect_pkg_installed(HAILO_TAPPAS) or auto_detect_pkg_config(HAILO_TAPPAS):
        return HAILO_TAPPAS
    elif detect_pkg_installed(HAILO_TAPPAS_CORE) or auto_detect_pkg_config(HAILO_TAPPAS_CORE) or auto_detect_pkg_config("hailo-all"):
        return HAILO_TAPPAS_CORE
    else:
        print("⚠ Could not detect TAPPAS variant, please install TAPPAS or TAPPAS-CORE.")
        return None



def auto_detect_installed_tappas_python_bindings() -> bool:
    """
    Automatically detect the installed TAPPAS version for Python.
    Returns:
        str: The detected TAPPAS version.
    """
    if detect_pip_package_installed(HAILO_TAPPAS):
        print("Detected TAPPAS Python bindings.")
        return True
    else:
        for pkg in HAILO_TAPPAS_CORE_PYTHON_NAMES:
            if detect_pip_package_installed(pkg):
                print(f"Detected {pkg} Python bindings.")
                return True
    print("⚠ Could not detect TAPPAS Python bindings, please install TAPPAS or TAPPAS-CORE.")
    return False

def auto_detect_tappas_version(tappas_variant: str) -> str:
    """
    Automatically detect the TAPPAS version based on the variant.
    Args:
        tappas_variant (str): The TAPPAS variant (HAILO_TAPPAS or HAILO_TAPPAS_CORE).
    Returns:
        str: The detected TAPPAS version.
    """
    if tappas_variant == HAILO_TAPPAS:
        return detect_pkg_config_version(HAILO_TAPPAS)
    elif tappas_variant == HAILO_TAPPAS_CORE:
        return detect_pkg_config_version(HAILO_TAPPAS_CORE)
    else:
        print("⚠ Could not detect TAPPAS version.")
        return None

def auto_detect_tappas_postproc_dir(tappas_variant: str) -> str:
    """
    Automatically detect the TAPPAS post-processing directory based on the variant.
    Args:
        tappas_variant (str): The TAPPAS variant (HAILO_TAPPAS or HAILO_TAPPAS_CORE).
    Returns:
        str: The detected TAPPAS post-processing directory.
    """
    if tappas_variant == HAILO_TAPPAS:
        workspace = run_command_with_output(
            ["pkg-config", "--variable=tappas_workspace", HAILO_TAPPAS]
        )
        return f"{workspace}/apps/h8/gstreamer/libs/post_processes/"
    elif tappas_variant == HAILO_TAPPAS_CORE:
        return run_command_with_output(
            ["pkg-config", "--variable=tappas_postproc_lib_dir", HAILO_TAPPAS_CORE]
        )
    else:
        print("⚠ Could not detect TAPPAS variant.")
        sys.exit(1)
    