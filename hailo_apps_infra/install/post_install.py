import os
import pathlib
import logging
from hailo_apps_infra.install.set_env import set_environment_vars

logger = logging.getLogger("post-install")

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def create_symlink(resource_path):
    resources_link = PROJECT_ROOT / "resources"
    resources_target = pathlib.Path(resource_path)
    if resources_link.exists():
        if resources_link.is_symlink():
            logger.info("Symlink to resources already exists.")
            return
        else:
            logger.warning(f"Path {resources_link} exists and is not a symlink. Please remove it manually.")
            return
    logger.info(f"Creating symlink: {resources_link} -> {resources_target}")
    resources_link.symlink_to(resources_target, target_is_directory=True)


def run_post_install(config):
    resource_path = config.get("resource_path")
    if not resource_path or resource_path == "auto":
        resource_path = "/usr/local/hailo/resources"
    config["resource_path"] = resource_path

    set_environment_vars(config)
    create_symlink(resource_path)
    logger.info("Post-install setup completed.")