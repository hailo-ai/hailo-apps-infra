# setup.py
from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class CustomInstallCommand(install):
    """Custom installation to run a post-install hook."""
    def run(self):
        # Run the standard install
        install.run(self)

        # Run the post-install logic
        print("🚀 Running post-install hook...")
        try:
            subprocess.check_call([
                sys.executable,
                "hailo-apps-infra/hailo_apps_infra/installation/hailo_installation/post_install.py"
            ])
            print("✅ Post-install completed.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Post-install failed: {e}")
            sys.exit(1)


setup(
    name="hailo-apps-infra",
    version="0.4.0",
    description="Hailo Inferstructure to create Applications",
    author="Hailo",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy",
        "pyyaml",
        "setuptools",
        "opencv-python",
    ],
    python_requires='>=3.7',
    cmdclass={
        'install': CustomInstallCommand,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
