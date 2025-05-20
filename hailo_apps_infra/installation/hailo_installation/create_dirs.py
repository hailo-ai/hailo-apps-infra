#!/usr/bin/env python3
import os
import pwd
import grp
import subprocess
from pathlib import Path
from hailo_apps_infra.common.hailo_common.defines import (
    RESOURCES_ROOT_PATH_DEFAULT,
    STORAGE_PATH_DEFAULT
)

def setup_resource_dirs(storage_dir: str = None):   
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

    resource_base = Path(RESOURCES_ROOT_PATH_DEFAULT)

    print()  # blank line
    print(f"🔧 Creating {resource_base} subdirs…")

    # 3) Create each subdir (using sudo so you don’t have to run the whole script as root)
    for sub in ("models/hailo8", "models/hailo8l", "videos", "so"):
        target = resource_base / sub
        subprocess.run(["sudo", "mkdir", "-p", str(target)], check=True)

    # 4) chown -R user:group and chmod -R 755
    subprocess.run([
        "sudo", "chown", "-R",
        f"{install_user}:{grpname}", str(resource_base)
    ], check=True)
    subprocess.run([
        "sudo", "chmod", "-R", "755", str(resource_base)
    ], check=True)

    # 5) Create the storage directory if it doesn't exist
    if storage_dir is not None:
        os.makedirs(storage_dir, exist_ok=True)

if __name__ == "__main__":
    setup_resource_dirs(STORAGE_PATH_DEFAULT)
    print("✅ Resource directories created successfully.")