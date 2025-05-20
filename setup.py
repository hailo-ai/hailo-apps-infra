from setuptools import setup, find_packages
from setuptools.command.install import install
import runpy
import sys


class CustomInstallCommand(install):
    def run(self):
        # Run the regular installation
        install.run(self)

        # Run your post_install logic here
        print("🚀 Running post-install hook...")
        try:
            runpy.run_module("hailo_apps_infra.installation.hailo_installation.post_install", run_name="__main__")
            print("✅ Post-install completed.")
        except Exception as e:
            print(f"❌ Post-install failed: {e}")
            sys.exit(1)


setup(
    name="hailo-apps-infra",
    version="0.4.0",
    description="Infra package to install all modular Hailo apps",
    author="Hailo",
    packages=find_packages(
        include=["hailo_apps_infra*"]
    ),
    include_package_data=True,
    install_requires=[
        "numpy<2.0.0",
        "setproctitle",
        "opencv-python",
        "python-dotenv",
        "pyyaml",
    ],
    python_requires=">=3.7",
    cmdclass={
        "install": CustomInstallCommand,
    },
    entry_points={
        "console_scripts": {
            "hailo-infra-install = install:main",
            "hailo-detect = hailo_apps_infra.pipelines.hailo_pipelines.detection_pipeline:main",
            "hailo-depth = hailo_apps_infra.pipelines.hailo_pipelines.depth_pipeline:main",
            "hailo-pose = hailo_apps_infra.pipelines.hailo_pipelines.pose_estimation_pipeline:main",
            "hailo-seg = hailo_apps_infra.pipelines.hailo_pipelines.instance_segmentation_pipeline:main",
            "hailo-simple-detect = hailo_apps_infra.pipelines.hailo_pipelines.detection_pipeline_simple:main",
        }
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
