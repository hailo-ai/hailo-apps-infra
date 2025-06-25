#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import os
import shutil
import os
import pwd
import grp
import subprocess

from hailo_apps.hailo_app_python.core.common.defines import (
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_DIRS_MAP
)

from hailo_apps.hailo_app_python.core.installation.download_resources import download_resources
from hailo_apps.hailo_app_python.core.installation.compile_cpp import compile_postprocess
from hailo_apps.hailo_app_python.core.common.installation_utils import (
    create_symlink,
)
from hailo_apps.hailo_app_python.core.common.config_utils import (
    load_and_validate_config,
)
from hailo_apps.hailo_app_python.core.common.core import load_environment
from hailo_apps.hailo_app_python.core.common.defines import (
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_PATH_KEY,
    RESOURCES_PATH_DEFAULT,
    REPO_ROOT,
    RESOURCES_GROUP_DEFAULT,
    DEFAULT_CONFIG_PATH,
    DEFAULT_DOTENV_PATH,
)
from hailo_apps.hailo_app_python.core.installation.set_env import (
    handle_dot_env,
    set_environment_vars
)
from hailo_apps.hailo_app_python.core.common.defines import (
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_DIRS_MAP
)

def setup_resource_dirs():   
    """
    Create resource directories for Hailo applications.
    This function creates the necessary directories for storing models and videos.
    It also sets the ownership and permissions for these directories.
    """
    # 1) Figure out which user actually invoked sudo (or fallback to the current user)
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        install_user = sudo_user
    else:
        install_user = pwd.getpwuid(os.getuid()).pw_name

    # 2) Lookup that user's primary group name
    pw   = pwd.getpwnam(install_user)
    grpname = grp.getgrgid(pw.pw_gid).gr_name


    # 3) Create each subdir (using sudo so you don’t have to run the whole script as root)
    for sub in RESOURCES_DIRS_MAP:
        target = sub
        subprocess.run(["sudo", "mkdir", "-p", str(target)], check=True)

    # 4) chown -R user:group and chmod -R 755
    subprocess.run([
        "sudo", "chown", "-R",
        f"{install_user}:{grpname}", str(RESOURCES_ROOT_PATH_DEFAULT)
    ], check=True)
    subprocess.run([
        "sudo", "chmod", "-R", "755", str(RESOURCES_ROOT_PATH_DEFAULT)
    ], check=True)

    # # 5) Create the storage directory if it doesn't exist
    # if storage_dir is not None:
    #     os.makedirs(storage_dir, exist_ok=True)

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
        default=DEFAULT_DOTENV_PATH,
        help="Path to the .env file to load environment variables from"
    )          
    args = parser.parse_args()
    handle_dot_env()  # this loads the .env file if it exists
    config = load_and_validate_config(args.config)
    set_environment_vars(config, args.dotenv)  # this sets env vars like HAILO_ARCH

    load_environment()  # this sets env vars like HAILO_ARCH

    setup_resource_dirs()
    print("✅ Resource directories created successfully.")

    # Make sure the resources directory doesnt exist before creating a symlink
    resources_path = Path(os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT))
    if resources_path.exists():
        if resources_path.is_symlink():
            print(f"⚠️ Warning: {resources_path} already exists (symlink). Removing it...")
            resources_path.unlink()
        elif resources_path.is_dir():
            print(f"⚠️ Warning: {resources_path} already exists (dir). Removing it...")
            shutil.rmtree(resources_path)
        else:
            print(f"⚠️ Warning: {resources_path} already exists (file). Removing it...")
            resources_path.unlink()
    # Create symlink for resources directory
    print(f"🔗 Linking resources directory to {resources_path}...")
    create_symlink(RESOURCES_ROOT_PATH_DEFAULT, resources_path)

    print("⬇️ Downloading resources...")
    download_resources(group=args.group)
    print(f"Resources downloaded to {resources_path}")

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