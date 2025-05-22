from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
import runpy
import sys
import os


# compute absolute paths to your sub‐dirs
root_dir = os.path.abspath(os.path.dirname(__file__))
core_dir = os.path.join(root_dir, 'hailo_apps_infra', 'hailo_core')
apps_dir = os.path.join(root_dir, 'hailo_apps_infra', 'hailo_apps')

class CustomInstallCommand(install):
    def run(self):
        # Run the regular installation
        super().run()

        if len(sys.argv) < 2 or sys.argv[1] != "install":
            return

        # Run your post_install logic here
        print("🚀 Running post-install hook...")
        try:
            runpy.run_module("hailo_apps_infra.hailo_core.hailo_installation.post_install", run_name="__main__")
            print("✅ Post-install completed.")
        except Exception as e:
            print(f"❌ Post-install failed: {e}")
            sys.exit(1)

class CustomDevelopCommand(develop):
    def run(self):
        develop.run(self)
        print("🚀 Running post-install hook (develop)…")
        try:
            runpy.run_module(
                "hailo_apps_infra.hailo_core.hailo_installation.post_install",
                run_name="__main__",
            )
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
        # first install the two local sub‐packages:
        #f"hailo-apps @ file://{apps_dir}",
        #f"hailo-core @ file://{core_dir}",

    ],
    python_requires=">=3.7",
    cmdclass={
        "install": CustomInstallCommand,
        "develop": CustomDevelopCommand,
    },
    entry_points={
        "console_scripts": {
            "hailo-post-install = hailo_core.hailo_installation.post_install:main",
            "hailo-detect = hailo_apps_infra.hailo_apps.hailo_pipelines.detection_pipeline:main",
            "hailo-depth = hailo_apps_infra.hailo_apps.hailo_pipelines.depth_pipeline:main",
            "hailo-pose = hailo_apps_infra.pipelines.hailo_pipelines.pose_estimation_pipeline:main",
            "hailo-seg = hailo_apps_infra.hailo_apps.hailo_pipelines.instance_segmentation_pipeline:main",
            "hailo-simple-detect = hailo_apps_infra.hailo_apps.hailo_pipelines.detection_pipeline_simple:main",
        }
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
