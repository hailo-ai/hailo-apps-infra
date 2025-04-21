import os
import logging
import subprocess
from pathlib import Path
import sys
from hailo_common.hailo_rpi_common import detect_device_arch, detect_hailo_arch, detect_pkg_installed
from hailo_common.utils import run_command_with_output, load_config

logger = logging.getLogger("env-setup")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"


def set_environment_vars(config, refresh=False):
    # if not refresh and ENV_PATH.exists():
    #     logger.info("Using existing .env (set refresh=True to regenerate)")
    #     return

    # Get configuration values with fallbacks to "auto"
    device_arch = config.get("device_arch") or "auto"
    hailo_arch = config.get("hailo_arch") or "auto"
    resources_path = config.get("resources_path") or "auto"
    model_zoo_version = config.get("model_zoo_version") or "auto"
    
    # Get additional configuration parameters matching config.yaml
    hailort_version = config.get("hailort_version") or "auto"
    tappas_version = config.get("tappas_version") or "auto"
    apps_infra_version = config.get("apps_infra_version") or "auto"
    auto_symlink = config.get("auto_symlink") or "auto"
    virtual_env_name = config.get("virtual_env_name") or "auto"
    server_url = config.get("server_url") or "auto"
    deb_whl_dir = config.get("deb_whl_dir") or "auto"

    # Process auto values with defaults
    if model_zoo_version == "auto":
        model_zoo_version = "v2.14.0"
    if device_arch == "auto":
        device_arch = detect_device_arch()
    if hailo_arch == "auto":
        hailo_arch = detect_hailo_arch()
    if resources_path == "auto":
        resources_path = "/usr/local/hailo/resources"
    if hailort_version == "auto":
        hailort_version = "4.20.0"
    if tappas_version == "auto":
        tappas_version = "3.31.0"
    if apps_infra_version == "auto":
        apps_infra_version = "25.3.1"
    if auto_symlink == "auto":
        auto_symlink = True
    if virtual_env_name == "auto":
        virtual_env_name = "hailo_infra_venv"
    if server_url == "auto":
        server_url = "http://dev-public.hailo.ai/2025_01"
    if deb_whl_dir == "auto":
        deb_whl_dir = "hailo_temp_resources"
        
    # Log all configuration values
    logger.info("Using configuration values:")
    logger.info(f"  Device Architecture: {device_arch}")
    logger.info(f"  Hailo Architecture: {hailo_arch}")
    logger.info(f"  Resources Path: {resources_path}")
    logger.info(f"  Model Zoo Version: {model_zoo_version}")
    logger.info(f"  HailoRT Version: {hailort_version}")
    logger.info(f"  TAPPAS Version: {tappas_version}")
    logger.info(f"  Apps Infra Version: {apps_infra_version}")
    logger.info(f"  Auto Symlink: {auto_symlink}")
    logger.info(f"  Virtual Environment Name: {virtual_env_name}")
    logger.info(f"  Server URL: {server_url}")
    logger.info(f"  Deb/Wheel Directory: {deb_whl_dir}")

    # TAPPAS dir detection
    if detect_pkg_installed("hailo-tappas"):
        tappas_variant = "tappas"
    elif detect_pkg_installed("hailo-tappas-core"):
        tappas_variant = "tappas-core"
    else:
        tappas_variant = "none"
        logger.warning("⚠ Could not detect TAPPAS variant.")

    tappas_postproc_dir = run_command_with_output("pkg-config --variable=tappas_postproc_lib_dir hailo-tappas-core")
    model_dir = os.path.join(resources_path, "models")

    # Set environment variables in current process
    os.environ["DEVICE_ARCH"] = device_arch
    os.environ["HAILO_ARCH"] = hailo_arch
    os.environ["RESOURCES_PATH"] = resources_path
    os.environ["TAPPAS_POST_PROC_DIR"] = tappas_postproc_dir
    os.environ["MODEL_DIR"] = model_dir
    os.environ["MODEL_ZOO_VERSION"] = model_zoo_version
    os.environ["HAILORT_VERSION"] = hailort_version
    os.environ["TAPPAS_VERSION"] = tappas_version
    os.environ["APPS_INFRA_VERSION"] = apps_infra_version
    os.environ["AUTO_SYMLINK"] = str(auto_symlink)
    os.environ["VIRTUAL_ENV_NAME"] = virtual_env_name
    os.environ["SERVER_URL"] = server_url
    os.environ["DEB_WHL_DIR"] = deb_whl_dir
    os.environ["TAPPAS_VARIANT"] = tappas_variant

    # Persist environment variables to .env file
    persist_env_vars(
        device_arch, 
        hailo_arch, 
        resources_path, 
        tappas_postproc_dir, 
        model_dir, 
        model_zoo_version,
        hailort_version,
        tappas_version,
        apps_infra_version,
        auto_symlink,
        virtual_env_name,
        server_url,
        deb_whl_dir,
        tappas_variant
    )


def persist_env_vars(device_arch, hailo_arch, resources_path, tappas_postproc_dir, model_dir, model_zoo_version,
                    hailort_version, tappas_version, apps_infra_version, auto_symlink, virtual_env_name, 
                    server_url, deb_whl_dir, tappas_variant):
    """
    Persist environment variables to .env file.
    Updated to match config.yaml parameters.
    """
    if ENV_PATH.exists() and not os.access(ENV_PATH, os.W_OK):
        try:
            logger.warning(f"⚠️ .env not writable — trying to fix permissions...")
            ENV_PATH.chmod(0o644)  # rw-r--r--
        except Exception as e:
            logger.error(f"❌ Failed to fix permissions for .env: {e}")
            sys.exit(1)

    # Create dictionary for all environment variables
    env_vars = {
        "DEVICE_ARCH": device_arch,
        "HAILO_ARCH": hailo_arch,
        "RESOURCES_PATH": resources_path,
        "TAPPAS_POST_PROC_DIR": tappas_postproc_dir,
        "MODEL_DIR": model_dir,
        "MODEL_ZOO_VERSION": model_zoo_version,
        "HAILORT_VERSION": hailort_version,
        "TAPPAS_VERSION": tappas_version,
        "APPS_INFRA_VERSION": apps_infra_version,
        "AUTO_SYMLINK": str(auto_symlink),
        "VIRTUAL_ENV_NAME": virtual_env_name,
        "SERVER_URL": server_url,
        "DEB_WHL_DIR": deb_whl_dir,
        "TAPPAS_VARIANT": tappas_variant
    }

    # Write all variables to .env file
    with open(ENV_PATH, "w") as f:
        for key, value in env_vars.items():
            if value is not None:
                f.write(f"{key}={value}\n")
                
    logger.info(f"✅ Persisted environment variables to {ENV_PATH}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    config = load_config()
    set_environment_vars(config)