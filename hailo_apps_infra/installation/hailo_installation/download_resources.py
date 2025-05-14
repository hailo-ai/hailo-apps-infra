#!/usr/bin/env python3
import argparse
import logging
import os
import urllib.request
from pathlib import Path

from hailo_common.common import detect_hailo_arch
from hailo_common.utils import load_config, load_environment

from hailo_common.defines import (
    DEFAULT_RESOURCES_CONFIG_PATH,
    HAILO_ARCH_KEY,
    RESOURCES_PATH_KEY,
    RESOURCES_PATH_DEFAULT,
    MODEL_ZOO_VERSION_KEY,
    MODEL_ZOO_VERSION_DEFAULT,
    RESOURCES_CONFIG_DEFAULTS_KEY,
    RESOURCES_MODEL_ZOO_URL_KEY,
    RESOURCES_CONFIG_GROUPS_KEY,
    RESOURCES_CONFIG_VIDEOS_KEY,
    RESOURCES_GROUP_DEFAULT,
    RESOURCES_GROUP_ALL,
    RESOURCES_GROUP_COMBINED,
    RESOURCES_GROUP_HAILO8,
    RESOURCES_GROUP_HAILO8L,
    RESOURCES_GROUP_RETRAIN,
    RESOURCES_MODELS_DIR_NAME,
    RESOURCES_VIDEOS_DIR_NAME,
)

logger = logging.getLogger("resource-downloader")
logging.basicConfig(level=logging.INFO)


def download_file(url: str, dest_path: Path):
    if dest_path.exists():
        logger.info(f"✅ {dest_path.name} already exists, skipping.")
        return
    logger.info(f"⬇ Downloading {url} → {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest_path)
    logger.info(f"✅ Downloaded to {dest_path}")


def download_resources(group: str = None):
    # Load the YAML config
    cfg_path = Path(DEFAULT_RESOURCES_CONFIG_PATH)
    config = load_config(cfg_path)

    # Determine Hailo architecture
    hailo_arch = os.getenv(HAILO_ARCH_KEY, detect_hailo_arch())
    logger.info(f"Detected Hailo architecture: {hailo_arch}")

    # Where to store resources
    resource_root = Path(os.getenv(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT))

    # Which model zoo version
    model_zoo_version = os.getenv(
        MODEL_ZOO_VERSION_KEY,
        MODEL_ZOO_VERSION_DEFAULT
    )
    logger.info(f"Using Model Zoo version: {model_zoo_version}")

    # Select groups
    if group is None or group == RESOURCES_GROUP_DEFAULT:
        groups = [RESOURCES_GROUP_COMBINED, hailo_arch]
    elif group == RESOURCES_GROUP_ALL:
        groups = [RESOURCES_GROUP_ALL]
    elif group in config.get(RESOURCES_CONFIG_GROUPS_KEY, {}):
        groups = [group]
    else:
        logger.error(f"Unknown group '{group}'")
        return

    # Flatten and dedupe
    seen = set()
    items = []
    for grp in groups:
        for entry in config[RESOURCES_CONFIG_GROUPS_KEY].get(grp, []):
            name = entry if isinstance(entry, str) else next(iter(entry.keys()))
            if name not in seen:
                seen.add(name)
                items.append(entry)

    # Download models
    base_url = config[RESOURCES_CONFIG_DEFAULTS_KEY][RESOURCES_MODEL_ZOO_URL_KEY]
    for entry in items:
        if isinstance(entry, str):
            name = entry
            url = f"{base_url}/{model_zoo_version}/{hailo_arch}/{name}.hef"
        else:
            name, url = next(iter(entry.items()))

        dest = resource_root / RESOURCES_MODELS_DIR_NAME / hailo_arch / f"{name}.hef"
        download_file(url, dest)

    # Download videos
    for vid_name, vid_cfg in config.get(RESOURCES_CONFIG_VIDEOS_KEY, {}).items():
        url = vid_cfg["url"]
        ext = Path(url).suffix or ".mp4"
        filename = vid_cfg.get("filename", f"{vid_name}{ext}")
        dest = resource_root / RESOURCES_VIDEOS_DIR_NAME / filename
        download_file(url, dest)


def main():
    parser = argparse.ArgumentParser(
        description="Install and download Hailo resources"
    )
    parser.add_argument(
        "--group",
        type=str,
        default=RESOURCES_GROUP_DEFAULT,
        help="Which resource group to download"
    )
    args = parser.parse_args()

    # Populate env defaults
    load_environment()
    download_resources(group=args.group)


if __name__ == "__main__":
    main()
