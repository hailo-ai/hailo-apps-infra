import os
import pathlib
import logging
from pathlib import Path

from hailo_common.utils import run_command, create_symlink, load_config
from hailo_common.get_config_values import get_config_value, get_default_config_value
from hailo_installation.set_env import set_environment_vars
from hailo_installation.download_resources import download_resources
from hailo_installation.validate_config import validate_config
from hailo_installation.compile_cpp import compile_postprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post-install")

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def post_install():
    logger.info("🔧 Validating configuration...")
    config = load_config(PROJECT_ROOT / "hailo_apps_infra" / "config" / "hailo_config" / "config.yaml")
    validate_config(config)

    logger.info("🔧 Setting environment...")
    set_environment_vars(config)

    resource_path = get_config_value('resources_path') or get_default_config_value('resources_path')    

    logger.info(f"🔗 Linking resources directory to {resource_path}...")
    create_symlink(resource_path, PROJECT_ROOT / "resources")

    logger.info("⬇️ Downloading resources...")
    download_resources(group="default")

    logger.info("⚙️ Compiling post-process...")
    compile_postprocess()

    logger.info("✅ Hailo Infra installation complete.")


if __name__ == "__main__":
    post_install()