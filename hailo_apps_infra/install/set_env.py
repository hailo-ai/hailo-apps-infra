import os
import logging
import subprocess
from pathlib import Path
from hailo_apps_infra.common.hailo_rpi_common import detect_device_arch, detect_hailo_arch , detect_pkg_installed

logger = logging.getLogger("env-setup")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def set_environment_vars(config, refresh=False):
    if not refresh and ENV_PATH.exists():
        logger.info("Using existing .env (set refresh=True to regenerate)")
        return

    device_arch = config.get("device_arch") or "auto"
    hailo_arch = config.get("hailo_arch") or "auto"
    resource_path = config.get("resource_path") or "auto"

    if device_arch == "auto":
        device_arch = detect_device_arch()
    if hailo_arch == "auto":
        hailo_arch = detect_hailo_arch()
    if resource_path == "auto":
        resource_path = "/usr/local/hailo/resources"

    # TAPPAS dir detection
    if detect_pkg_installed("hailo-tappas"):
        tappas_variant = "tappas"
    elif detect_pkg_installed("hailo-tappas-core"):
        tappas_variant = "tappas-core"
    else:
        tappas_variant = "none"
        logger.warning("⚠ Could not detect TAPPAS variant.")

    tappas_postproc_dir = os.path.join(resource_path, "postproc", tappas_variant) if tappas_variant != "none" else ""
    model_dir = os.path.join(resource_path, "models")

    os.environ["DEVICE_ARCH"] = device_arch
    os.environ["HAILO_ARCH"] = hailo_arch
    os.environ["RESOURCE_PATH"] = resource_path
    os.environ["TAPPAS_POST_PROC_DIR"] = tappas_postproc_dir

    logger.info(f"Set DEVICE_ARCH={device_arch}")
    logger.info(f"Set HAILO_ARCH={hailo_arch}")
    logger.info(f"Set TAPPAS_POST_PROC_DIR={tappas_postproc_dir}")
    logger.info(f"Set RESOURCE_PATH={resource_path}")

    persist_env_vars(device_arch, hailo_arch, resource_path, tappas_postproc_dir, model_dir)


def persist_env_vars(device_arch, hailo_arch, resource_path, tappas_postproc_dir, model_dir):
    with open(ENV_PATH, "w") as f:
        f.write(f"DEVICE_ARCH={device_arch}\n")
        f.write(f"HAILO_ARCH={hailo_arch}\n")
        f.write(f"RESOURCE_PATH={resource_path}\n")
        f.write(f"TAPPAS_POST_PROC_DIR={tappas_postproc_dir}\n")
    logger.info(f"✅ Persisted environment variables to {ENV_PATH}")
