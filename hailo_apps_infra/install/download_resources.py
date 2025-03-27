
import argparse
import logging
import os
from pathlib import Path
import yaml
import urllib.request
from hailo_apps_infra.common.hailo_rpi_common import detect_hailo_arch
from importlib.resources import files

logger = logging.getLogger("resource-downloader")
logging.basicConfig(level=logging.INFO)

def load_config():
    config_path = files("hailo_apps_infra").joinpath("config/resources_config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def download_file(url, dest_path):
    if dest_path.exists():
        logger.info(f"✅ {dest_path.name} already exists, skipping.")
        return
    logger.info(f"⬇ Downloading {url} → {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest_path)
    logger.info(f"✅ Downloaded to {dest_path}")

def download_resources(group=None, names=None):
    config = load_config()
    arch = detect_hailo_arch()
    logger.info(f"Detected Hailo architecture: {arch}")

    resources_dir = Path("/usr/local/hailo/resources")
    selected_names = set()

    # Always include resources from the default group
    selected_names.update(config["groups"]["default"])

    # If another group is provided (and it's not "default"), add its resources too
    if group and group != "default":
        selected_names.update(config["groups"].get(group, []))

    # If specific resource names are provided, add them as well
    if names:
        selected_names.update(names)

    for name in selected_names:
        if name in config["models"]:
            model = config["models"][name]
            if model["arch"] == arch:
                subdir = resources_dir / "models" / arch
                dest = subdir / f"{name}.hef"
                download_file(model["url"], dest)
            else:
                logger.info(f"⏩ Skipping {name}, not for arch {arch}")
        elif name in config["videos"]:
            dest = resources_dir / "videos" / f"{name}.mp4"
            download_file(config["videos"][name]["url"], dest)
        else:
            logger.warning(f"⚠ Unknown resource: {name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", type=str, help="Download a named group like default, all, test")
    parser.add_argument("--name", nargs="*", help="Download specific resources by name")
    args = parser.parse_args()

    if not args.group and not args.name:
        print("❌ Please specify either --group or --name , will download the default only!")

    download_resources(group=args.group, names=args.name)