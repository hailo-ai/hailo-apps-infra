#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.request
import platform
from pathlib import Path


# ─── config loading & env helpers ─────────────────────────────────────────────
from hailo_apps_infra.common.hailo_common.config_utils import (
    load_config,
    validate_config,
)
from hailo_apps_infra.common.hailo_common.core import (
    load_environment,
)

# ─── other imports ────────────────────────────────────────────────────────────
from hailo_apps_infra.common.hailo_common.defines import (
    HOST_ARCH_KEY,
    DEFAULT_CONFIG_PATH,
    HOST_ARCH_DEFAULT,
    HAILORT_VERSION_KEY,
    AUTO_DETECT,
    TAPPAS_POSTPROC_PATH_KEY,
    HAILORT_PACKAGE,
    HAILO_TAPPAS,
    HAILO_TAPPAS_CORE,
    TAPPAS_VERSION_KEY,
    TAPPAS_VARIANT_KEY,
    TAPPAS_VERSION_DEFAULT,
    TAPPAS_VARIANT_DEFAULT,
    MODEL_ZOO_VERSION_KEY,
    MODEL_ZOO_VERSION_DEFAULT,
    VIRTUAL_ENV_NAME_KEY,
    VIRTUAL_ENV_NAME_DEFAULT,
    SERVER_URL_KEY,
    SERVER_URL_DEFAULT,
    RESOURCES_PATH_KEY,
    RESOURCES_PATH_DEFAULT,
    STORAGE_PATH_KEY,
    STORAGE_PATH_DEFAULT,
    DEFAULT_DOTENV_PATH,
    PIP_CMD,
    PYTHON_CMD,
    HAILO_ARCH_KEY,
    HAILO_ARCH_DEFAULT,
    HAILO_TAPPAS_CORE_PYTHON,
)
from hailo_apps_infra.common.hailo_common.installation_utils import (
    detect_system_pkg_version,
    detect_hailo_arch,
    detect_host_arch,
    detect_pkg_installed,
    run_command_with_output,
    run_command,
)



def handle_hailort_version(hailort_version: str) -> str:
    """
    Handle the hailort version based on the provided value.
    If AUTO_DETECT is specified, detect the version automatically.
    """
    if hailort_version == AUTO_DETECT or hailort_version is None:
        print("🔍 Auto-detecting HailoRT version...")
        hailort_version = detect_system_pkg_version(HAILORT_PACKAGE)
        if hailort_version is None:
            print("❌ HailoRT version not found. Please specify a valid version.")
            sys.exit(1)
    return hailort_version


def handle_hailo_arch(hailo_arch: str) -> str:
    """
    Handle the Hailo architecture based on the provided value.
    If AUTO_DETECT is specified, detect the architecture automatically.
    """
    if hailo_arch == AUTO_DETECT or hailo_arch is None:
        print("🔍 Auto-detecting Hailo architecture...")
        hailo_arch = detect_hailo_arch()
        if hailo_arch is None:
            print("❌ Hailo architecture not found. Please specify a valid architecture.")
            sys.exit(1)
    return hailo_arch


def handle_host_arch(host_arch: str) -> str:
    """
    Handle the host architecture based on the provided value.
    If AUTO_DETECT is specified, detect the architecture automatically.
    """
    if host_arch == AUTO_DETECT or host_arch is None:
        print("🔍 Auto-detecting host architecture...")
        host_arch = detect_host_arch()
        if host_arch is None:
            print("❌ Host architecture not found. Please specify a valid architecture.")
            sys.exit(1)
    return host_arch


def handle_tappas(tappas_version: str, tappas_variant: str) -> tuple:
    """
    Handle the TAPPAS version and variant based on the provided values.
    """
    if tappas_variant == AUTO_DETECT:
        print("⚠️ tappas_variant is set to 'auto'. Detecting TAPPAS variant...")
        if detect_pkg_installed(HAILO_TAPPAS):
            tappas_variant = HAILO_TAPPAS
            print("✅ Detected TAPPAS variant.")
        elif detect_pkg_installed(HAILO_TAPPAS_CORE):
            tappas_variant = HAILO_TAPPAS_CORE
            print("✅ Detected TAPPAS-CORE variant.")
        else:
            print("⚠ Could not detect TAPPAS variant, please install TAPPAS or TAPPAS-CORE.")
            sys.exit(1)

    if tappas_version == AUTO_DETECT:
        print("⚠️ tappas_version is set to 'auto'. Detecting TAPPAS version...")
        tappas_version = detect_system_pkg_version(
            HAILO_TAPPAS if tappas_variant == HAILO_TAPPAS else HAILO_TAPPAS_CORE
        )
        if tappas_version is None:
            print("⚠ Could not detect TAPPAS version.")
            sys.exit(1)
        print(f"✅ Detected TAPPAS version: {tappas_version}")

    if tappas_variant == HAILO_TAPPAS:
        # use a list so subprocess.run() finds the executable
        workspace = run_command_with_output(
            ["pkg-config", "--variable=tappas_workspace", HAILO_TAPPAS]
        )
        tappas_postproc_dir = f"{workspace}/apps/h8/gstreamer/libs/post_processes/"

    elif tappas_variant == HAILO_TAPPAS_CORE:
        tappas_postproc_dir = run_command_with_output(
            ["pkg-config", "--variable=tappas_postproc_lib_dir", HAILO_TAPPAS_CORE]
        )

    else:
        print("⚠ Could not detect TAPPAS variant.")
        sys.exit(1)
    return tappas_version, tappas_variant, tappas_postproc_dir


def handle_virtualenv(
    venv_name: str,
    python_cmd: str,
    tappas_variant: str
) -> tuple[bool, bool, str, str]:
    """
    Ensure a virtualenv exists (create if needed) using run_command,
    then re-check inside it whether 'hailort' and tappas_pip_pkg need installing
    via run_command_with_output.
    Returns updated flags: (install_pyhailort, install_tappas_core , venv_pip , venv_python ).
    """
    venv_path = Path(venv_name)

    install_tappas_core = True
    install_pyhailort = True
    if tappas_variant == HAILO_TAPPAS_CORE:
        tappas_variant = HAILO_TAPPAS_CORE_PYTHON

    try:
        run_command_with_output([PIP_CMD, "show", HAILORT_PACKAGE])
        install_pyhailort = False
    except Exception:
        print(1)
        install_pyhailort = True

    try:
        run_command_with_output([PIP_CMD, "show", tappas_variant])
        install_tappas_core = False
    except Exception:
        install_tappas_core = True

    # 1) Create or skip creation
    if venv_path.is_dir():
        print(f"✅ Virtualenv '{venv_name}' exists. Activating…")
    else:
        print(f"🔧 Creating virtualenv '{venv_name}'…")
        # build the venv command string
        cmd = f"{python_cmd} -m venv"
        if not (install_pyhailort and install_tappas_core):
            cmd += " --system-site-packages"
            print("Using system site packages")
        cmd += f" {venv_name}"
        run_command(cmd, f"Failed to create virtualenv '{venv_name}'")
        print("✅ Created. Activating…")

    # 2) Print activation instruction
    print(f"To activate, run:\n    source {venv_path/'bin'/'activate'}")

    # 3) Re-check inside venv with its pip
    venv_python = os.path.join(venv_path , "bin" , "python3")
    venv_pip = os.path.join(venv_path , "bin" , "pip3")

        # if we’re not already that interpreter, re‐exec
    if os.path.abspath(sys.executable) != os.path.abspath(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)

    try:
        run_command_with_output([venv_pip, "show", HAILORT_PACKAGE])
        install_pyhailort = False
        print(f"✅ HailoRT {HAILORT_PACKAGE} already installed.")
    except Exception:
        install_pyhailort = True

    try:
        run_command_with_output([venv_pip, "show", tappas_variant])
        install_tappas_core = False
        print(f"✅ TAPPAS {tappas_variant} already installed.")
    except Exception:
        install_tappas_core = True

    return install_pyhailort, install_tappas_core , venv_pip , venv_python


def handle_set_and_persist_env(
    host_arch, hailo_arch, resources_path, tappas_postproc_dir,
    model_zoo_version, hailort_version, tappas_version,
    virtual_env_name, server_url, storage_dir, tappas_variant
) -> None:
    env_vars = {
        HOST_ARCH_KEY: host_arch,
        HAILO_ARCH_KEY: hailo_arch,
        RESOURCES_PATH_KEY: resources_path,
        TAPPAS_POSTPROC_PATH_KEY: tappas_postproc_dir,
        MODEL_ZOO_VERSION_KEY: model_zoo_version,
        HAILORT_VERSION_KEY: hailort_version,
        TAPPAS_VERSION_KEY: tappas_version,
        VIRTUAL_ENV_NAME_KEY: virtual_env_name,
        SERVER_URL_KEY: server_url,
        STORAGE_PATH_KEY: storage_dir,
        TAPPAS_VARIANT_KEY: tappas_variant
    }
    os.environ.update({k: v for k, v in env_vars.items() if v is not None})
    _persist_env_vars(env_vars)


def _persist_env_vars(env_vars: dict) -> None:
    if DEFAULT_DOTENV_PATH.exists() and not os.access(DEFAULT_DOTENV_PATH, os.W_OK):
        print("⚠️ .env not writable — fixing permissions...")
        try:
            DEFAULT_DOTENV_PATH.chmod(0o666)
        except Exception as e:
            print(f"❌ Failed to fix .env perms: {e}")
            sys.exit(1)
    with open(DEFAULT_DOTENV_PATH, 'w') as f:
        for key, value in env_vars.items():
            if value is not None:
                f.write(f"{key}={value}\n")
    print(f"✅ Persisted environment variables to {DEFAULT_DOTENV_PATH}")


def load_and_validate_config(config_path: str) -> dict:
    """
    Load and validate the configuration file.
    Returns the loaded configuration as a dictionary.
    """
    cfg_path = Path(config_path or DEFAULT_CONFIG_PATH)
    config = load_config(cfg_path)
    if not validate_config(config):
        print("❌ Invalid configuration. Please check the config file.")
        sys.exit(1)
    return config

def handle_dot_env() -> None:
    if not DEFAULT_DOTENV_PATH.is_file():
        print(f"🔧 Creating .env file at {DEFAULT_DOTENV_PATH}")
        DEFAULT_DOTENV_PATH.touch()
        os.chmod(DEFAULT_DOTENV_PATH, 0o666)
    else:
        print(f"✅ .env already exists at {DEFAULT_DOTENV_PATH}")
        os.chmod(DEFAULT_DOTENV_PATH, 0o666)

def pre_install(config_path: str = None) -> dict:
    config = load_and_validate_config(config_path)
    print("✅ Configuration loaded successfully.")

    storage_dir = config.get(STORAGE_PATH_KEY, STORAGE_PATH_DEFAULT)
    server_url = config.get(SERVER_URL_KEY, SERVER_URL_DEFAULT)
    virtual_env_name = config.get(VIRTUAL_ENV_NAME_KEY, VIRTUAL_ENV_NAME_DEFAULT)

    hailort_version = handle_hailort_version(config.get(HAILORT_VERSION_KEY))
    tappas_version, tappas_variant, tappas_postproc_dir = handle_tappas(
        config.get(TAPPAS_VERSION_KEY, TAPPAS_VERSION_DEFAULT),
        config.get(TAPPAS_VARIANT_KEY, TAPPAS_VARIANT_DEFAULT)
    )

    install_pyhailort, install_tappas_core, venv_pip_cmd, venv_python_cmd = handle_virtualenv(
        virtual_env_name, PYTHON_CMD, tappas_variant
    )

    handle_dot_env()
    handle_set_and_persist_env(
        handle_host_arch(config.get(HOST_ARCH_KEY, HOST_ARCH_DEFAULT)),
        handle_hailo_arch(config.get(HAILO_ARCH_KEY, HAILO_ARCH_DEFAULT)),
        config.get(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT),
        tappas_postproc_dir,
        config.get(MODEL_ZOO_VERSION_KEY, MODEL_ZOO_VERSION_DEFAULT),
        hailort_version,
        tappas_version,
        virtual_env_name,
        server_url,
        storage_dir,
        tappas_variant
    )

    load_environment()
    print("✅ Environment variables set successfully.")

    return {
        "config": config,
        "hailort_version": hailort_version,
        "tappas_version": tappas_version,
        "tappas_variant": tappas_variant,
        "tappas_postproc_dir": tappas_postproc_dir,
        "venv_pip_cmd": venv_pip_cmd,
        "venv_python_cmd": venv_python_cmd,
        "install_pyhailort": install_pyhailort,
        "install_tappas_core": install_tappas_core,
        "storage_dir": storage_dir,
        "server_url": server_url,
    }

def main():
    arg_parser = argparse.ArgumentParser(
        description="Pre-installation script for Hailo applications."
    )
    arg_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to the configuration file."
    )
    args = arg_parser.parse_args()
    config_path = args.config
    pre_install(config_path)
    print("✅ Pre-installation completed successfully.")