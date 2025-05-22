#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import os

# Ensure hailo_core is importable from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/dev/hailo-apps-infra/hailo_apps_infra
sys.path.insert(0, str(PROJECT_ROOT))

from hailo_core.hailo_installation.create_dirs  import setup_resource_dirs
from hailo_core.hailo_installation.download_resources import download_resources
from hailo_core.hailo_installation.compile_cpp import compile_postprocess
from hailo_core.hailo_common.installation_utils import (
    create_symlink,
)
from hailo_core.hailo_common.config_utils import (
    load_and_validate_config,
)
from hailo_core.hailo_common.core import load_environment
from hailo_core.hailo_common.defines import (
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_PATH_KEY,
    RESOURCES_PATH_DEFAULT,
    REPO_ROOT,
    RESOURCES_GROUP_DEFAULT,
    DEFAULT_CONFIG_PATH,
)
from hailo_core.hailo_installation.set_env import (
    handle_dot_env,
    set_environment_vars
)

def post_install():
    """
    Post-installation script for Hailo Apps Infra.
    This script sets up the environment, creates resource directories,
    downloads resources, and compiles post-process.
    """
    parser = argparse.ArgumentParser(
        description="Post-installation script for Hailo Apps Infra"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Name of the virtualenv to create"
    )
    parser.add_argument(
        "--group",
        type=str,
        default=RESOURCES_GROUP_DEFAULT,
        help="HailoRT version to install"
    )  
    parser.add_argument(
        "--dotenv",
        type=str,
        default=str(REPO_ROOT / ".env"),
        help="Path to the .env file"
    )  
    args = parser.parse_args()
    handle_dot_env(args.dotenv)  # this loads the .env file if it exists
    config = load_and_validate_config(args.config)
    set_environment_vars(config,args.dotenv)  # this sets env vars like HAILO_ARCH

    load_environment()  # this sets env vars like HAILO_ARCH

    setup_resource_dirs()
    print("✅ Resource directories created successfully.")

    print(f"🔗 Linking resources directory to {os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT)}...")
    create_symlink(RESOURCES_ROOT_PATH_DEFAULT, os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT))

    print("⬇️ Downloading resources...")
    download_resources(group=args.group)
    print(f"Resources downloaded to {os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT)}")

    print("⚙️ Compiling post-process...")
    compile_postprocess()

    print("✅ Hailo Infra Post-instllation complete.")

def main():
    """
    Main function to run the post-installation script.
    """
    post_install()

if __name__ == "__main__":
    main()
    # This script is intended to be run as a post-installation step