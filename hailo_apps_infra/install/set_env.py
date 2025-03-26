import os
import logging
from pathlib import Path
from hailo_apps_infra.common.hailo_rpi_common import detect_device_arch, detect_hailo_arch

logger = logging.getLogger("env-setup")

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def set_environment_vars(config):
    device_arch = config.get("device_arch")
    if not device_arch or device_arch == "auto":
        device_arch = detect_device_arch()

    hailo_arch = config.get("hailo_arch")
    if not hailo_arch or hailo_arch == "auto":
        hailo_arch = detect_hailo_arch()

    resource_path = config.get("resource_path")
    if not resource_path or resource_path == "auto":
        resource_path = "/usr/local/hailo/resources"

    tappas_postproc_dir = os.path.join(resource_path, "postprocess")
    model_dir = os.path.join(resource_path, "models")

    os.environ["DEVICE_ARCH"] = device_arch
    os.environ["HAILO_CHIP_ARCH"] = hailo_arch
    os.environ["TAPPAS_POST_PROC_DIR"] = tappas_postproc_dir
    os.environ["MODEL_ZOO_DIR"] = model_dir

    logger.info(f"Set DEVICE_ARCH={device_arch}")
    logger.info(f"Set HAILO_CHIP_ARCH={hailo_arch}")
    logger.info(f"Set TAPPAS_POST_PROC_DIR={tappas_postproc_dir}")
    logger.info(f"Set MODEL_ZOO_DIR={model_dir}")

    persist_env_vars(device_arch, hailo_arch, tappas_postproc_dir, model_dir)


def persist_env_vars(device_arch, hailo_arch, tappas_postproc_dir, model_dir):
    env_path = PROJECT_ROOT / ".env"
    with open(env_path, "w") as f:
        f.write(f"DEVICE_ARCH={device_arch}\n")
        f.write(f"HAILO_CHIP_ARCH={hailo_arch}\n")
        f.write(f"TAPPAS_POST_PROC_DIR={tappas_postproc_dir}\n")
        f.write(f"MODEL_ZOO_DIR={model_dir}\n")
    logger.info(f"Persisted environment variables to {env_path}")