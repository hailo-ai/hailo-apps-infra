import os
import logging
import subprocess
from pathlib import Path
import sys
from hailo_common.hailo_rpi_common import detect_host_arch, detect_hailo_arch, detect_pkg_installed
from hailo_common.utils import run_command_with_output, detect_hailo_package_version
from hailo_common.get_config_values import load_config, get_default_config_value

logger = logging.getLogger("env-setup")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"

def set_environment_vars(config, refresh=False):
    # Load config values with defaults
    host_arch = config.get("host_arch", get_default_config_value("host_arch"))
    hailo_arch = config.get("hailo_arch", get_default_config_value("hailo_arch"))
    resources_path = config.get("resources_path", get_default_config_value("resources_path"))
    model_zoo_version = config.get("model_zoo_version", get_default_config_value("model_zoo_version"))
    hailort_version = config.get("hailort_version", get_default_config_value("hailort_version"))
    tappas_version  = config.get("tappas_version", get_default_config_value("tappas_version"))
    apps_infra_version = config.get("apps_infra_version", get_default_config_value("apps_infra_version"))
    virtual_env_name = config.get("virtual_env_name", get_default_config_value("virtual_env_name"))
    deb_whl_dir = config.get("deb_whl_dir", get_default_config_value("deb_whl_dir"))
    tappas_variant = config.get("tappas_variant", get_default_config_value("tappas_variant"))
    tappas_postproc_dir = None
    server_url = config.get("server_url", get_default_config_value("server_url"))

    # Auto-detect values if needed
    if host_arch in ("auto", None):
        logger.warning("⚠️ host_arch is set to 'auto'. Detecting device architecture...")
        host_arch = detect_host_arch()
    if hailo_arch in ("auto", None):
        logger.warning("⚠️ hailo_arch is set to 'auto'. Detecting Hailo architecture...")
        hailo_arch = detect_hailo_arch()
    if resources_path in ("auto", None):
        logger.warning("⚠️ resources_path is set to 'auto'. Using default path...")
        resources_path = get_default_config_value("resources_path")
    if hailort_version in ("auto", None):
        logger.warning("⚠️ hailort_version is set to 'auto'. Detecting HailoRT version...")
        hailort_version = detect_hailo_package_version("hailort")
        if not hailort_version:
            logger.error("⚠ Could not detect HailoRT version.")
            sys.exit(1)
    # Detect TAPPAS variant and postproc dir
    if tappas_variant in ("auto", None):
        logger.warning("⚠️ tappas_variant is set to 'auto'. Detecting TAPPAS variant...")
        if detect_pkg_installed("tappas"):
            tappas_variant = "tappas"
            tappas_workspace = run_command_with_output("pkg-config --variable=tappas_workspace hailo_tappas")
            tappas_postproc_dir = f"{tappas_workspace}/apps/h8/gstreamer/libs/post_processes/"
        elif detect_pkg_installed("tappas-core"):
            tappas_variant = "tappas-core"
            tappas_postproc_dir = run_command_with_output("pkg-config --variable=tappas_postproc_lib_dir hailo-tappas-core")
        else:
            logger.error("⚠ Could not detect TAPPAS variant.")
            sys.exit(1)
    if tappas_version in ("auto", None):
        logger.warning("⚠️ tappas_version is set to 'auto'. Detecting TAPPAS version...")
        if tappas_variant == "tappas":
            tappas_version = detect_hailo_package_version("tappas")
        elif tappas_variant == "tappas-core":
            tappas_version = detect_hailo_package_version("tappas-core")
        else:
            logger.error("⚠ Could not detect TAPPAS version.")
            sys.exit(1)

    # Prevent NoneType when setting env
    if tappas_postproc_dir is None:
        logger.warning("⚠️ TAPPAS_POST_PROC_DIR was not detected; defaulting to empty string.")
        tappas_postproc_dir = ""

    # Log final config
    logger.info("Using configuration values:")
    for key, val in {
        "Host Architecture": host_arch,
        "Hailo Architecture": hailo_arch,
        "Resources Path": resources_path,
        "Model Zoo Version": model_zoo_version,
        "HailoRT Version": hailort_version,
        "TAPPAS Version": tappas_version,
        "Apps Infra Version": apps_infra_version,
        "Virtual Environment Name": virtual_env_name,
        "Server URL": server_url,
        "Deb/Wheel Directory": deb_whl_dir,
        "TAPPAS Variant": tappas_variant,
        "TAPPAS Dir": tappas_postproc_dir
    }.items():
        logger.info(f"  {key}: {val}")

    # Set environment vars in process
    os.environ.update({
        "HOST_ARCH": host_arch,
        "HAILO_ARCH": hailo_arch,
        "RESOURCES_PATH": resources_path,
        "TAPPAS_POST_PROC_DIR": tappas_postproc_dir,
        "MODEL_DIR": os.path.join(resources_path, "models"),
        "MODEL_ZOO_VERSION": model_zoo_version,
        "HAILORT_VERSION": hailort_version,
        "TAPPAS_VERSION": tappas_version,
        "APPS_INFRA_VERSION": apps_infra_version,
        "VIRTUAL_ENV_NAME": virtual_env_name,
        "SERVER_URL": server_url,
        "DEB_WHL_DIR": deb_whl_dir,
        "TAPPAS_VARIANT": tappas_variant
    })

    persist_env_vars(
        host_arch,
        hailo_arch,
        resources_path,
        tappas_postproc_dir,
        os.path.join(resources_path, "models"),
        model_zoo_version,
        hailort_version,
        tappas_version,
        apps_infra_version,
        virtual_env_name,
        server_url,
        deb_whl_dir,
        tappas_variant
    )


def persist_env_vars(host_arch, hailo_arch, resources_path, tappas_postproc_dir, model_dir,
                     model_zoo_version, hailort_version, tappas_version, apps_infra_version,
                     virtual_env_name, server_url, deb_whl_dir, tappas_variant):
    if ENV_PATH.exists() and not os.access(ENV_PATH, os.W_OK):
        try:
            logger.warning(f"⚠️ .env not writable — trying to fix permissions...")
            ENV_PATH.chmod(0o644)
        except Exception as e:
            logger.error(f"❌ Failed to fix permissions for .env: {e}")
            sys.exit(1)

    env_vars = {
        "HOST_ARCH": host_arch,
        "HAILO_ARCH": hailo_arch,
        "RESOURCES_PATH": resources_path,
        "TAPPAS_POST_PROC_DIR": tappas_postproc_dir,
        "MODEL_DIR": model_dir,
        "MODEL_ZOO_VERSION": model_zoo_version,
        "HAILORT_VERSION": hailort_version,
        "TAPPAS_VERSION": tappas_version,
        "APPS_INFRA_VERSION": apps_infra_version,
        "VIRTUAL_ENV_NAME": virtual_env_name,
        "SERVER_URL": server_url,
        "DEB_WHL_DIR": deb_whl_dir,
        "TAPPAS_VARIANT": tappas_variant
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
