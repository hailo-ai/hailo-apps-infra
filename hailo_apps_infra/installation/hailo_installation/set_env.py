import os
import logging
import subprocess
from pathlib import Path
import sys
from hailo_common.hailo_rpi_common import detect_device_arch, detect_hailo_arch , detect_pkg_installed
from hailo_common.utils import run_command_with_output, load_config

logger = logging.getLogger("env-setup")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"


def set_environment_vars(config, refresh=False):
    # if not refresh and ENV_PATH.exists():
    #     logger.info("Using existing .env (set refresh=True to regenerate)")
    #     return

    device_arch = config.get("device_arch") or "auto"
    hailo_arch = config.get("hailo_arch") or "auto"
    resource_path = config.get("resource_path") or "auto"
    mz_version = config.get("model_zoo_version") or "auto"

    if mz_version == "auto":
        mz_version = "v2.14.0"
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

    tappas_postproc_dir = run_command_with_output("pkg-config --variable=tappas_postproc_lib_dir hailo-tappas-core")
    model_dir = os.path.join(resource_path, "models")

    os.environ["DEVICE_ARCH"] = device_arch
    os.environ["HAILO_ARCH"] = hailo_arch
    os.environ["RESOURCE_PATH"] = resource_path
    os.environ["TAPPAS_POST_PROC_DIR"] = tappas_postproc_dir
    os.environ["MZ_VERSION"] = mz_version

    logger.info(f"Set DEVICE_ARCH={device_arch}")
    logger.info(f"Set HAILO_ARCH={hailo_arch}")
    logger.info(f"Set TAPPAS_POST_PROC_DIR={tappas_postproc_dir}")
    logger.info(f"Set RESOURCE_PATH={resource_path}")
    logger.info(f"Set MZ_VERSION={mz_version}")

    persist_env_vars(device_arch, hailo_arch, resource_path, tappas_postproc_dir, model_dir, mz_version)


def persist_env_vars(device_arch, hailo_arch, resource_path, tappas_postproc_dir, model_dir, mz_version):
    if ENV_PATH.exists() and not os.access(ENV_PATH, os.W_OK):
        try:
            logger.warning(f"⚠️ .env not writable — trying to fix permissions...")
            ENV_PATH.chmod(0o644)  # rw-r--r--
        except Exception as e:
            logger.error(f"❌ Failed to fix permissions for .env: {e}")
            sys.exit(1)

    with open(ENV_PATH, "w") as f:
        f.write(f"DEVICE_ARCH={device_arch}\n")
        f.write(f"HAILO_ARCH={hailo_arch}\n")
        f.write(f"RESOURCE_PATH={resource_path}\n")
        f.write(f"TAPPAS_POST_PROC_DIR={tappas_postproc_dir}\n")
        f.write(f"MODEL_DIR={model_dir}\n")
        f.write(f"MZ_VERSION={mz_version}\n")

    logger.info(f"✅ Persisted environment variables to {ENV_PATH}")



def main():
    print("DEBUG: MAIN FUNCTION STARTED ✅")

    logger.info("🔧 Validating configuration...")
    config = load_config(PROJECT_ROOT / "hailo_apps_infra" /"config" / "hailo_config" / "config.yaml")

    logger.info("🔧 Setting environment...")
    set_environment_vars(config)
    logger.info("🔗 Linking resources directory...")

    logger.info("Showing environment variables...")
    print("DEBUG: Environment keys set:", list(os.environ.keys()))
    for var in ["DEVICE_ARCH", "HAILO_ARCH", "RESOURCE_PATH", "TAPPAS_POST_PROC_DIR", "MODEL_DIR", "MZ_VERSION"]:
        value = os.environ.get(var)
        if value:
            print(f"{var}={value}")
            logger.info(f"{var}={value}")
        else:
            logger.warning(f"{var} is not set")
    logger.info("✅ Environment setup complete.")

if __name__ == "__main__":
    main()