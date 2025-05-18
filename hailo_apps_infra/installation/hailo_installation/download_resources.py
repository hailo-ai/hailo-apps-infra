#!/usr/bin/env python3
import argparse
import logging
import os
import urllib.request
from pathlib import Path



# ─── load_config, load_environment ────────────────────────────────────────────────
try:
    from hailo_apps_infra.common.hailo_common.config_utils import load_config
except ImportError:
    from ...common.hailo_common.config_utils import load_config

try:
    from hailo_apps_infra.common.hailo_common.core import load_environment
except ImportError:
    from ...common.hailo_common.core import load_environment


# ─── all the defines ──────────────────────────────────────────────────────────────
from hailo_apps_infra.common.hailo_common.defines import (
        DEFAULT_RESOURCES_CONFIG_PATH,
        HAILO_ARCH_KEY,
        MODEL_ZOO_URL,
        MODEL_ZOO_VERSION_KEY,
        MODEL_ZOO_VERSION_DEFAULT,
        RESOURCES_GROUPS_MAP,
        RESOURCES_GROUP_DEFAULT,
        HAILO8_ARCH,
        HAILO8L_ARCH,
        RESOURCES_GROUP_HAILO8,
        RESOURCES_GROUP_HAILO8L,
        RESOURCES_ROOT_PATH_DEFAULT,
        RESOURCES_MODELS_DIR_NAME,
        RESOURCES_VIDEOS_DIR_NAME,
        HAILO_FILE_EXTENSION,
        RESOURCES_GROUP_ALL,
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

def download_resources(group: str = None,
                       resource_config_path: str = None):
    # 1) Load your YAML config (expects a mapping: group -> [entries])
    cfg_path = Path(resource_config_path or DEFAULT_RESOURCES_CONFIG_PATH)
    config = load_config(cfg_path)

    # 2) Detect architecture & version
    hailo_arch = os.getenv(HAILO_ARCH_KEY)
    logger.info(f"Detected Hailo architecture: {hailo_arch}")

    model_zoo_version = os.getenv(
        MODEL_ZOO_VERSION_KEY,
        MODEL_ZOO_VERSION_DEFAULT
    )
    logger.info(f"Using Model Zoo version: {model_zoo_version}")


    # 3) Build list of groups to fetch
    groups = [RESOURCES_GROUP_DEFAULT]

    if group != RESOURCES_GROUP_DEFAULT:
        if group in RESOURCES_GROUPS_MAP:
            groups.append(group)
        else:
            logger.warning(f"Unknown group '{group}', skipping.")

    else:
        if hailo_arch == HAILO8_ARCH:
            groups.append(RESOURCES_GROUP_HAILO8)
            print(f"Detected Hailo architecture: {hailo_arch} → adding Hailo8 resources")
        elif hailo_arch == HAILO8L_ARCH:
            groups.append(RESOURCES_GROUP_HAILO8L)
            print(f"Detected Hailo architecture: {hailo_arch} → adding Hailo8L resources")
        else:
            print(f"Unknown architecture: {hailo_arch}, only default resources will be downloaded")

                

    # 4) Flatten + dedupe
    seen = set()
    items = []
    for grp in groups:
        for entry in config.get(grp, []):
            key = entry if isinstance(entry, str) else next(iter(entry.keys()))
            if key not in seen:
                seen.add(key)
                items.append(entry)

    resource_root = Path(RESOURCES_ROOT_PATH_DEFAULT)
    base_url = MODEL_ZOO_URL

    # 5) Process each entry
    for entry in items:
        # Determine URL + destination based on type
        if isinstance(entry, str):
            if entry.startswith(("http://", "https://")):
                url = entry
                ext = Path(url).suffix.lower()
                if ext == HAILO_FILE_EXTENSION:
                    # model URL
                    name = Path(url).stem
                    dest = resource_root / RESOURCES_MODELS_DIR_NAME / hailo_arch / f"{name}{HAILO_FILE_EXTENSION}"
                else:
                    # video URL
                    filename = Path(url).name
                    dest = resource_root / RESOURCES_VIDEOS_DIR_NAME / filename
            else:
                # bare model name → construct URL
                name = entry
                url = f"{base_url}/{model_zoo_version}/{hailo_arch}/{name}{HAILO_FILE_EXTENSION}"
                dest = resource_root / RESOURCES_MODELS_DIR_NAME / hailo_arch / f"{name}{HAILO_FILE_EXTENSION}"
        else:
            # mapping { name: url }
            name, url = next(iter(entry.items()))
            ext = Path(url).suffix.lower()
            if ext == HAILO_FILE_EXTENSION:
                dest = resource_root / RESOURCES_MODELS_DIR_NAME / hailo_arch / f"{name}{HAILO_FILE_EXTENSION}"
            else:
                filename = f"{name}{ext}"
                dest = resource_root / RESOURCES_VIDEOS_DIR_NAME / filename

        logger.info(f"Downloading {url} → {dest}")
        download_file(url, dest)
def main():
    parser = argparse.ArgumentParser(
        description="Install and download Hailo resources"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all resources"
    )
    parser.add_argument(
        "--group",
        type=str,
        default=RESOURCES_GROUP_DEFAULT,
        help="Which resource group to download"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_RESOURCES_CONFIG_PATH,
        help="Path to the resources config file"
    )
    args = parser.parse_args()

    if args.all:
        args.group = RESOURCES_GROUP_ALL

    # Populate env defaults
    load_environment()
    download_resources(group=args.group, resource_config_path=args.config)
    logger.info("✅ All resources downloaded successfully.")


if __name__ == "__main__":
    main()
