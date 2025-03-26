import os
import subprocess
import pathlib
import logging
from hailo_apps_infra.install.validate_config import load_config, validate_config
from hailo_apps_infra.install.post_install import run_post_install
from hailo_apps_infra.install.compile_cpp import compile_postprocess


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hailo-installer")

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_command(command, error_msg):
    logger.info(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        logger.error(f"{error_msg} (exit code {result.returncode})")
        exit(result.returncode)


def install():
    logger.info("Loading and validating configuration...")
    config = load_config(PROJECT_ROOT / "config" / "config.yaml")
    validate_config(config)

    logger.info("Running post-install setup...")
    run_post_install(config)

    logger.info("Compiling post-process code...")
    compile_postprocess()

    logger.info("Downloading resources...")
    run_command("./scripts/download_resources.sh --all", "Failed to download models/resources")

    logger.info("Hailo Infra installation completed successfully!")


if __name__ == "__main__":
    install()