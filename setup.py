# setup.py
from setuptools import setup
from setuptools.command.install import install
import os
import sys
import subprocess

class CustomInstallCommand(install):
    def run(self):
        # Run the regular installation
        install.run(self)

        # Run your post_install logic here
        print("🚀 Running post-install hook...")

        cmd = [sys.executable, "hailo-apps-infra/hailo_apps_infra/installation/hailo_installation/post_install.py"]
        subprocess.check_call(cmd)
        print("✅ Post-install completed.")

setup()
