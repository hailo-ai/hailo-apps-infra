#!/usr/bin/env python3
from pathlib import Path
import sys

# ─── other imports ────────────────────────────────────────────────────────────

import argparse
import logging
import os
import urllib.request

import yaml




# ─── load_config, load_environment ────────────────────────────────────────────────
from hailo_apps.hailo_app_python.core.common.config_utils import load_config

from hailo_apps.hailo_app_python.core.common.core import load_environment

from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch

# ─── all the defines ──────────────────────────────────────────────────────────────
from hailo_apps.hailo_app_python.core.common.defines import (
        DEFAULT_RESOURCES_CONFIG_PATH,
        HAILO_ARCH_KEY,
        MODEL_ZOO_URL,
        MODEL_ZOO_VERSION_KEY,
        MODEL_ZOO_VERSION_DEFAULT,
        RESOURCES_GROUPS_MAP,
        RESOURCES_GROUP_DEFAULT,
        HAILO8_ARCH,
        HAILO8L_ARCH,
        HAILO10H_ARCH,
        RESOURCES_GROUP_HAILO8,
        RESOURCES_GROUP_HAILO8L,
        RESOURCES_ROOT_PATH_DEFAULT,
        RESOURCES_MODELS_DIR_NAME,
        RESOURCES_VIDEOS_DIR_NAME,
        HAILO_FILE_EXTENSION,
        RESOURCES_GROUP_ALL,
        RESOURCES_GROUP_RETRAIN,
        JSON_FILE_EXTENSION,
        RESOURCES_JSON_DIR_NAME,
    )


logger = logging.getLogger("resource-downloader")
logging.basicConfig(level=logging.INFO)

# ─── create_default_config, download_file, download_resources ──────────────────────
def create_default_config():
    """Create the default resources configuration."""
    default_config = {
        'default': [
            'yolov6n',
            'scdepthv3',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/example.mp4',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/example_640.mp4',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/face_recognition.mp4',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/configs/scrfd.json',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/configs/barcode_labels.json',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/configs/face_recon_algo_params.json',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/configs/yolov5m_seg.json',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/configs/yolov5n_seg.json'
        ],
        'hailo8': [
            'yolov8m',
            'yolov5m_seg',
            'yolov8m_pose',
            'scrfd_10g',
            'arcface_mobilefacenet'
        ],
        'hailo8l': [
            'yolov8s',
            'yolov5n_seg',
            'yolov8s_pose',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/scrfd_2.5g.hef',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/arcface_mobilefacenet_h8l.hef'
        ],
        'all': [
            'yolov8s_pose',
            'yolov8s',
            'yolov8m_pose',
            'yolov8m',
            'yolov6n',
            'yolov5n_seg',
            'yolov5m_wo_spp',
            'yolov5m_seg',
            'yolov11s',
            'yolov11n',
            'scdepthv3'
        ],
        'retrain': [
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov8s-hailo8l-barcode.hef',
            'https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/barcode.mp4'
        ]
    }
    return default_config

def create_config_at_path(config_path: str = None):
    """Create default config at specified path."""
    cfg_path = None
    if config_path is None:
        cfg_path = Path("/usr/local/hailo/resources/resources_config.yaml")
    else:
        cfg_path = Path(config_path)

    cfg_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = create_default_config()
    with open(cfg_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)

    print(f"Default configuration created at {cfg_path}")
    return cfg_path  # Return Path object


def download_file(url: str, dest_path: Path):
    if dest_path.exists():
        logger.info(f"✅ {dest_path.name} already exists, skipping.")
        return
    logger.info(f"⬇ Downloading {url} → {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest_path)
    logger.info(f"✅ Downloaded to {dest_path}")

def download_resources(group: str = None,
                       resource_config_path: str = None, arch: str = None):
    # 1) Load your YAML config (expects a mapping: group -> [entries])
    cfg_path = Path(resource_config_path or DEFAULT_RESOURCES_CONFIG_PATH)
    if not cfg_path.is_file():
        print(f"❌ Config file not found at {cfg_path}", file=sys.stderr)
        print("Creating a default config file...")
        cfg_path = create_config_at_path()
    print(f"Loading resources config from {cfg_path}")
    config = load_config(cfg_path)

    # 2) Detect architecture & version
    if not arch:
        hailo_arch = os.getenv(HAILO_ARCH_KEY) or detect_hailo_arch()
    else:
        print(f"Using architecture from command line: {arch}")
        hailo_arch = arch


    if not hailo_arch:
        print("❌ Hailo architecture could not be detected.")
        hailo_arch = HAILO8_ARCH
        print(f"➡️ Defaulting to architecture: {hailo_arch}")

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
            if group == RESOURCES_GROUP_ALL:
                groups.append(RESOURCES_GROUP_RETRAIN)
        else:
            logger.warning(f"Unknown group '{group}', skipping.")

    if hailo_arch == HAILO8_ARCH:
        groups.append(RESOURCES_GROUP_HAILO8)
        print(f"Detected Hailo architecture: {hailo_arch} → adding Hailo8 resources")
    elif hailo_arch == HAILO8L_ARCH:
        groups.append(RESOURCES_GROUP_HAILO8L)
        print(f"Detected Hailo architecture: {hailo_arch} → adding Hailo8L resources")
    elif hailo_arch == HAILO10H_ARCH:
        print(f"Detected Hailo architecture: {hailo_arch} → adding Hailo10H resources")
        groups.append(RESOURCES_GROUP_HAILO8)
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
                    if entry.find("hailo8l") != -1:
                        dest = resource_root / RESOURCES_MODELS_DIR_NAME / "hailo8l" / f"{name}{HAILO_FILE_EXTENSION}"
                else:
                    if ext == JSON_FILE_EXTENSION:  # JSON file URL
                        filename = Path(url).name
                        dest = resource_root / RESOURCES_JSON_DIR_NAME / filename
                    else:  # video URL
                        filename = Path(url).name
                        dest = resource_root / RESOURCES_VIDEOS_DIR_NAME / filename
            else:
                # bare model name → construct URL
                name = entry
                if hailo_arch == HAILO10H_ARCH:
                    url = f"{base_url}/{model_zoo_version}/{'hailo15h'}/{name}{HAILO_FILE_EXTENSION}"
                else:
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
    parser.add_argument(
        "--arch",
        type=str,
        default=None,
        help="Hailo architecture to use (e.g. hailo8, hailo8l, hailo10h). If not specified, it will be auto-detected."
    )
    args = parser.parse_args()

    if args.all:
        args.group = RESOURCES_GROUP_ALL

    # Populate env defaults
    load_environment()
    download_resources(group=args.group, resource_config_path=args.config, arch=args.arch)
    logger.info("✅ All resources downloaded successfully.")


if __name__ == "__main__":
    main()
