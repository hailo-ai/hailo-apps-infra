#!/usr/bin/env python3

import os
from pathlib import Path

from hailo_apps_infra.installation.hailo_installation.create_dirs import setup_resource_dirs
from hailo_apps_infra.installation.hailo_installation.download_resources import download_resources
from hailo_apps_infra.installation.hailo_installation.compile_cpp import compile_postprocess
from hailo_apps_infra.common.hailo_common.installation_utils import (
    create_symlink,
)
from hailo_apps_infra.common.hailo_common.defines import (
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_PATH_KEY,
    RESOURCES_PATH_DEFAULT,
    STORAGE_PATH_KEY,
    STORAGE_PATH_DEFAULT,
    REPO_ROOT,
    HAILO_APPS_INFRA_PATH_KEY,
    )

def post_install():
    print("Creating directories for resources and storage...")
    storage_path = os.getenv(STORAGE_PATH_KEY,STORAGE_PATH_DEFAULT)
    setup_resource_dirs(storage_path)
    print("✅ Resource directories created successfully.")

    print(f"🔗 Linking resources directory to {os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT)}...")
    create_symlink(RESOURCES_ROOT_PATH_DEFAULT, os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT))

    print("⬇️ Downloading resources...")
    download_resources()

    print("⚙️ Compiling post-process...")
    compile_postprocess(os.getenv(HAILO_APPS_INFRA_PATH_KEY, REPO_ROOT))

    print("✅ Hailo Infra installation complete.")

if __name__ == "__main__":
    post_install()
    # This script is intended to be run as a post-installation step