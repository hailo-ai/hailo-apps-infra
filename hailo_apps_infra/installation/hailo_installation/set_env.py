import os
import logging
from pathlib import Path
import sys
from hailo_common.installation_utils import run_command_with_output,detect_system_pkg_version,detect_host_arch, detect_hailo_arch, detect_pkg_installed
from hailo_common.config_utils import load_config
from hailo_common.defines import (
    HOST_ARCH_KEY,
    HAILO_ARCH_KEY,
    RESOURCES_PATH_KEY,
    MODEL_ZOO_VERSION_KEY,
    HAILORT_VERSION_KEY,
    TAPPAS_VERSION_KEY,
    STORAGE_PATH_KEY,
    TAPPAS_VARIANT_KEY,
    SERVER_URL_KEY,
    VIRTUAL_ENV_NAME_KEY,
    DEFAULT_DOTENV_PATH,
    HOST_ARCH_DEFAULT,
    DEFAULT_RESOURCES_SYMLINK_PATH,
    MODEL_ZOO_VERSION_DEFAULT,
    HAILORT_VERSION_DEFAULT,
    TAPPAS_VERSION_DEFAULT,
    VIRTUAL_ENV_NAME_DEFAULT,
    STORAGE_PATH_DEFAULT,
    TAPPAS_VARIANT_DEFAULT,
    SERVER_URL_DEFAULT,
    AUTO_DETECT,
    HAILORT_PACKAGE,
    HAILO_TAPPAS,
    HAILO_TAPPAS_CORE,
    TAPPAS_POSTPROC_PATH_KEY,
    HAILO_TAPPAS,
    HAILO_TAPPAS_CORE,
    HAILORT_VERSION_DEFAULT,
    TAPPAS_VERSION_DEFAULT,
    TAPPAS_VARIANT_DEFAULT,
    HAILO_ARCH_DEFAULT,
)


# Path for persisting environment variables
ENV_PATH = Path(DEFAULT_DOTENV_PATH)

logger = logging.getLogger("env-setup")

def set_environment_vars(config):
    # Load config values with defaults
    host_arch = config.get(HOST_ARCH_KEY, HOST_ARCH_DEFAULT)
    hailo_arch = config.get(HAILO_ARCH_KEY, HAILO_ARCH_DEFAULT)
    resources_path = config.get(RESOURCES_PATH_KEY, DEFAULT_RESOURCES_SYMLINK_PATH)
    model_zoo_version = config.get(MODEL_ZOO_VERSION_KEY, MODEL_ZOO_VERSION_DEFAULT)
    hailort_version = config.get(HAILORT_VERSION_KEY, HAILORT_VERSION_DEFAULT)
    tappas_version = config.get(TAPPAS_VERSION_KEY, TAPPAS_VERSION_DEFAULT)
    virtual_env_name = config.get(VIRTUAL_ENV_NAME_KEY,VIRTUAL_ENV_NAME_DEFAULT)
    storage_dir = config.get(STORAGE_PATH_KEY, STORAGE_PATH_DEFAULT)
    tappas_variant = config.get(TAPPAS_VARIANT_KEY, TAPPAS_VARIANT_DEFAULT)
    server_url = config.get(SERVER_URL_KEY, SERVER_URL_DEFAULT)

    # Auto-detect values if needed
    if host_arch == AUTO_DETECT:
        logger.warning("⚠️ host_arch is set to 'auto'. Detecting device architecture...")
        host_arch = detect_host_arch()
    if hailo_arch == AUTO_DETECT:
        logger.warning("⚠️ hailo_arch is set to 'auto'. Detecting Hailo architecture...")
        hailo_arch = detect_hailo_arch()
    if hailort_version == AUTO_DETECT:
        logger.warning("⚠️ hailort_version is set to 'auto'. Detecting HailoRT version...")
        hailort_version = detect_system_pkg_version(HAILORT_PACKAGE)
        if not hailort_version:
            logger.error("⚠ Could not detect HailoRT version.")
            sys.exit(1)
    # Detect TAPPAS variant and postproc dir
    if tappas_variant ==  AUTO_DETECT:
        print("⚠️ tappas_variant is set to 'auto'. Detecting TAPPAS variant...")
        if detect_pkg_installed(HAILO_TAPPAS):
            tappas_variant =HAILO_TAPPAS
        elif detect_pkg_installed(HAILO_TAPPAS_CORE):
            tappas_variant = HAILO_TAPPAS_CORE
        else:
            print("⚠ Could not detect TAPPAS variant, Please install TAPPAS or TAPPAS-CORE.")
            sys.exit(1)
    if tappas_version == AUTO_DETECT:
        print("⚠️ tappas_version is set to 'auto'. Detecting TAPPAS version...")
        if tappas_variant ==HAILO_TAPPAS:
            tappas_version = detect_system_pkg_version(HAILO_TAPPAS)
        elif tappas_variant == HAILO_TAPPAS_CORE:
            tappas_version = detect_system_pkg_version(HAILO_TAPPAS_CORE)
        else:
            print("⚠ Could not detect TAPPAS version.")
            sys.exit(1)

    tappas_postproc_dir = None
    if tappas_variant ==HAILO_TAPPAS:
        tappas_workspace = run_command_with_output("pkg-config --variable=tappas_workspace {HAILO_TAPPAS}")
        tappas_postproc_dir = f"{tappas_workspace}/apps/h8/gstreamer/libs/post_processes/"
    elif tappas_variant == HAILO_TAPPAS_CORE:
        tappas_postproc_dir = run_command_with_output("pkg-config --variable=tappas_postproc_lib_dir {HAILO_TAPPAS_CORE}")



    # Log final config
    logger.info("Using configuration values:")
    for key, val in {
        HOST_ARCH_KEY: host_arch,
        HAILO_ARCH_KEY: hailo_arch,
        RESOURCES_PATH_KEY: resources_path,
        MODEL_ZOO_VERSION_KEY: model_zoo_version,
        HAILORT_VERSION_KEY: hailort_version,
        TAPPAS_VERSION_KEY: tappas_version,
        VIRTUAL_ENV_NAME_KEY: virtual_env_name,
        SERVER_URL_KEY: server_url,
        STORAGE_PATH_KEY: storage_dir,
        TAPPAS_VARIANT_KEY: tappas_variant,
    }.items():
        logger.info(f"  {key}: {val}")

    # Set environment vars in process
    os.environ.update({
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
    })

    persist_env_vars(
        host_arch,
        hailo_arch,
        resources_path,
        tappas_postproc_dir,
        model_zoo_version,
        hailort_version,
        tappas_version,
        virtual_env_name,
        server_url,
        storage_dir,
        tappas_variant
    )


def persist_env_vars(host_arch, hailo_arch, resources_path, tappas_postproc_dir,
                     model_zoo_version, hailort_version, tappas_version,
                     virtual_env_name, server_url, storage_dir, tappas_variant):
    if ENV_PATH.exists() and not os.access(ENV_PATH, os.W_OK):
        try:
            logger.warning(f"⚠️ .env not writable — trying to fix permissions...")
            ENV_PATH.chmod(0o644)
        except Exception as e:
            logger.error(f"❌ Failed to fix permissions for .env: {e}")
            sys.exit(1)

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

    with open(ENV_PATH, "w") as f:
        for key, value in env_vars.items():
            if value is not None:
                f.write(f"{key}={value}\n")

    logger.info(f"✅ Persisted environment variables to {ENV_PATH}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    set_environment_vars(config)
