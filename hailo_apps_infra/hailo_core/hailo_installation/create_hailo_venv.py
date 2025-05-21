#!/usr/bin/env python3
import sys
from pathlib import Path
import argparse
import shutil
# Ensure hailo_core is importable from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/dev/hailo-apps-infra/hailo_apps_infra
sys.path.insert(0, str(PROJECT_ROOT))

# ─── other imports ────────────────────────────────────────────────────────────
from hailo_core.hailo_common.defines import (
    VIRTUAL_ENV_NAME_DEFAULT,
    VENV_CREATE_CMD,
    TAPPAS_VERSION_DEFAULT,
    AUTO_DETECT,
    HAILORT_VERSION_DEFAULT
)


from hailo_core.hailo_common.installation_utils import (
    auto_detect_hailort_python_bindings,
    auto_detect_installed_tappas_python_bindings,
    run_command,
    auto_detect_tappas_version,
    auto_detect_tappas_variant,
    auto_detect_hailort_version,
)

from hailo_core.hailo_installation.python_installation import (
    install_tappas_core,
    install_pyhailort
)

def is_virtualenv(path: Path) -> bool:
    return (path / "bin" / "python").exists() and (path / "pyvenv.cfg").exists()

def remove_virtualenv(path: Path):
    if is_virtualenv(path):
        print(f"🧹 Removing existing virtualenv at: {path}")
        shutil.rmtree(path)
    else:
        print(f"⚠️ Path does not appear to be a virtualenv: {path}")

def create_hailo_virtualenv(virtual_env_name: str = VIRTUAL_ENV_NAME_DEFAULT,tappas_version: str = TAPPAS_VERSION_DEFAULT, pyhailort_version: str = HAILORT_VERSION_DEFAULT):
    """
    Create a Hailo virtualenv and install Hailo packages if needed.
    Args:
        virtual_env_name (str): Name of the virtualenv to create.
        tappas_version (str): TAPPAS version to install.
    """
    # Check if the virtualenv name is valid
    venv_path = Path(virtual_env_name).resolve()
    if is_virtualenv(venv_path):
        remove_virtualenv(venv_path)
    
    if tappas_version == AUTO_DETECT or tappas_version is None:
        tappas_version = auto_detect_tappas_version(auto_detect_tappas_variant())
    if pyhailort_version == AUTO_DETECT or pyhailort_version is None:
        pyhailort_version = auto_detect_hailort_version()

    if not pyhailort_version or not tappas_version:
        print("⚠️ Could not detect HailoRT or TAPPAS version, please install them manually, or with our script at hailo-apps-infra/scripts/hailo_installation_script.sh.")
        return
    pytappas_installed = auto_detect_installed_tappas_python_bindings()
    pyhailort_installed = auto_detect_hailort_python_bindings()

    if pytappas_installed and pyhailort_installed:
        print("⚠️ TAPPAS and HailoRT Python bindings are already installed.")
        cmd = f"{VENV_CREATE_CMD} --system-site-packages {virtual_env_name}"
        run_command(cmd, f"Failed to create virtualenv '{virtual_env_name}'")
        print(f"To activate, run:\n    source {virtual_env_name}/bin/activate")
        return
    if pytappas_installed:
        print("⚠️ TAPPAS Python bindings are already installed.")
        cmd = f"{VENV_CREATE_CMD} --system-site-packages {virtual_env_name}"
        run_command(cmd, f"Failed to create virtualenv '{virtual_env_name}'")
        print("Installing HailoRT Python bindings...")
        # Download and install the HailoRT wheel
        install_pyhailort(pyhailort_version, str(venv_path))
        print(f"To activate, run:\n    source {virtual_env_name}/bin/activate")
        return
    elif pyhailort_installed:
        print("⚠️ HailoRT Python bindings are already installed.")
        cmd = f"{VENV_CREATE_CMD} --system-site-packages {virtual_env_name}"
        run_command(cmd, f"Failed to create virtualenv '{virtual_env_name}'")
        print("installing TAPPAS Python bindings...")
        install_tappas_core(tappas_version, str(venv_path))
        print(f"To activate, run:\n    source {virtual_env_name}/bin/activate")
        return
    else:
        print("🔧 Creating virtualenv without system site packages...")
        cmd = f"{VENV_CREATE_CMD} {virtual_env_name}"
        run_command(cmd, f"Failed to create virtualenv '{virtual_env_name}'")
        print(f"To activate, run:\n    source {virtual_env_name}/bin/activate")
        print("Installing Hailo-Tappas-Core Python bindings...")
        install_tappas_core(tappas_version, str(venv_path))
        print("Installing HailoRT Python bindings...")
        install_pyhailort(pyhailort_version, str(venv_path))
        print(f"To activate, run:\n    source {virtual_env_name}/bin/activate")
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a Hailo virtualenv and install Hailo packages if needed"
    )
    parser.add_argument(
        "--virtualenv",
        type=str,
        default=VIRTUAL_ENV_NAME_DEFAULT,
        help="Name of the virtualenv to create"
    )
    parser.add_argument(
        "--tappas-version",
        type=str,
        default=TAPPAS_VERSION_DEFAULT,
        help="TAPPAS version to install"
    )
    parser.add_argument(
        "--pyhailort-version",
        type=str,
        default=HAILORT_VERSION_DEFAULT,
        help="HailoRT version to install"
    )
    args = parser.parse_args()
    # Create the virtualenv
    create_hailo_virtualenv(args.virtualenv, args.tappas_version, args.pyhailort_version)
    print("✅ Hailo virtualenv created successfully.")
