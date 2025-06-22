#!/usr/bin/env python3
from pathlib import Path
import sys
# Ensure hailo_core is importable from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/dev/hailo-apps-infra/hailo_apps_infra
sys.path.insert(0, str(PROJECT_ROOT))

# ─── other imports ────────────────────────────────────────────────────────────
import os
import pwd
import grp
import subprocess

from hailo_core.hailo_common.defines import (
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

if __name__ == "__main__":
    setup_resource_dirs()
    print("✅ Resource directories created successfully.")