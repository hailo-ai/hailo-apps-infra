import os
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


def post_install(config_path: Path | str = None,group: str = None,resource_config_path: str = None):
    """
    Post-installation script for Hailo Apps Infra.
    This script performs the following tasks:
    1. Loads and validates the configuration file.
    2. Sets up environment variables based on the configuration.
    3. Creates a symlink to the resources directory.
    4. Downloads resources based on the configuration.
    5. Compiles the post-process C++ code.
    """
    # 1) Load and validate config
    cfg_path = Path(config_path or DEFAULT_CONFIG_PATH)
    logger.info(f"🔧 Validating configuration at {cfg_path}...")
    config = load_config(cfg_path)
    if (validate_config(config) == False):
        logger.error("❌ Invalid configuration. Please check the config file.")
        return
    logger.info("✅ Configuration is valid.")
    
    # 2) Set environment variables
    logger.info("🔧 Setting environment...")
    set_environment_vars(config)

    resource_path = os.getenv(RESOURCES_PATH_KEY, DEFAULT_RESOURCES_SYMLINK_PATH)

    logger.info(f"🔗 Linking resources directory to {resource_path}...")
    create_symlink(RESOURCES_ROOT_PATH_DEFAULT, resource_path)

    logger.info("⬇️ Downloading resources...")
    download_resources(group,resource_config_path)

    logger.info("⚙️ Compiling post-process...")
    compile_postprocess()

    logger.info("✅ Hailo Infra installation complete.")


if __name__ == "__main__":
    post_install()