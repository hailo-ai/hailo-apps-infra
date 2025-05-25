import os
import sys
import argparse
import logging
from pathlib import Path

# Ensure hailo_core is importable from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from hailo_core.hailo_common.installation_utils import (
    detect_system_pkg_version, detect_host_arch,
    detect_hailo_arch, auto_detect_tappas_variant,
    auto_detect_tappas_version, auto_detect_tappas_postproc_dir
)
from hailo_core.hailo_common.config_utils import load_and_validate_config
from hailo_core.hailo_common.defines import *

logger = logging.getLogger("env-setup")


def handle_dot_env(env_path: Path = None) -> Path:
    env_path = env_path or Path(DEFAULT_DOTENV_PATH)
    if not Path(env_path).is_file():
        print(f"🔧 Creating .env file at {env_path}")
        env_path.touch()
    os.chmod(env_path, 0o666)
    return env_path


def _persist_env_vars(env_vars: dict, env_path: Path) -> None:
    if Path(env_path).exists() and not os.access(env_path, os.W_OK):
        print("⚠️ .env not writable — fixing permissions...")
        try:
            env_path.chmod(0o666)
        except Exception as e:
            print(f"❌ Failed to fix .env perms: {e}")
            sys.exit(1)
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            if value is not None:
                f.write(f"{key}={value}\n")
    print(f"✅ Persisted environment variables to {env_path}")



def set_environment_vars(config, env_path: Path = None) -> None:
    host_arch = config.get(HOST_ARCH_KEY, HOST_ARCH_DEFAULT)
    hailo_arch = config.get(HAILO_ARCH_KEY, HAILO_ARCH_DEFAULT)
    resources_path = config.get(RESOURCES_PATH_KEY, DEFAULT_RESOURCES_SYMLINK_PATH)
    model_zoo_version = config.get(MODEL_ZOO_VERSION_KEY, MODEL_ZOO_VERSION_DEFAULT)
    hailort_version = config.get(HAILORT_VERSION_KEY, HAILORT_VERSION_DEFAULT)
    tappas_version = config.get(TAPPAS_VERSION_KEY, TAPPAS_VERSION_DEFAULT)
    virtual_env_name = config.get(VIRTUAL_ENV_NAME_KEY, VIRTUAL_ENV_NAME_DEFAULT)
    tappas_variant = config.get(TAPPAS_VARIANT_KEY, TAPPAS_VARIANT_DEFAULT)
    server_url = config.get(SERVER_URL_KEY, SERVER_URL_DEFAULT)

    if host_arch == AUTO_DETECT:
        logger.warning("⚠️ host_arch is 'auto'. Detecting...")
        host_arch = detect_host_arch()
    if hailo_arch == AUTO_DETECT:
        logger.warning("⚠️ hailo_arch is 'auto'. Detecting...")
        hailo_arch = detect_hailo_arch()
    if hailort_version == AUTO_DETECT:
        logger.warning("⚠️ hailort_version is 'auto'. Detecting...")
        hailort_version = detect_system_pkg_version(HAILORT_PACKAGE) or sys.exit(1)

    if tappas_variant == AUTO_DETECT:
        tappas_variant = auto_detect_tappas_variant()

    if tappas_version == AUTO_DETECT:
        tappas_version = auto_detect_tappas_version(tappas_variant)
   
    tappas_postproc_dir = auto_detect_tappas_postproc_dir(tappas_variant)
    
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
        TAPPAS_VARIANT_KEY: tappas_variant
    }

    os.environ.update({k: v for k, v in env_vars.items() if v is not None})
    _persist_env_vars(env_vars, env_path)


if __name__ == "__main__":
    argparse = argparse.ArgumentParser(description="Set environment variables for Hailo installation.")
    argparse.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the config file (YAML format)."
    )
    argparse.add_argument(
        "--env-path",
        type=str,
        default=DEFAULT_DOTENV_PATH,
        help="Path to the .env file."
    )
    logging.basicConfig(level=logging.INFO)
    handle_dot_env(env_path=Path(argparse.parse_args().env_path))
    config = load_and_validate_config(argparse.parse_args().config)
    set_environment_vars(config, env_path=Path(argparse.parse_args().env_path))
