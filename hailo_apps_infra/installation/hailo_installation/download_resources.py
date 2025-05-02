
import argparse
import logging
import os
from pathlib import Path
import yaml
import urllib.request
from hailo_common.common import detect_hailo_arch
from hailo_common.utils import load_config, load_environment
from importlib.resources import files

logger = logging.getLogger("resource-downloader")
logging.basicConfig(level=logging.INFO)


def download_file(url, dest_path):
    if dest_path.exists():
        logger.info(f"✅ {dest_path.name} already exists, skipping.")
        return
    logger.info(f"⬇ Downloading {url} → {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest_path)
    logger.info(f"✅ Downloaded to {dest_path}")

def download_resources(group=None, names=None):
    """
    Downloads resources from the specified group or names.

    Args:
        group (str): The resource group to download.
        names (list): Specific resource names to download.
    """

    cfg_path = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "hailo_config"
        / "resources_config.yaml"
    )
    config = load_config(cfg_path)
    hailo_arch = os.getenv("HAILO_ARCH", detect_hailo_arch())
    logger.info(f"Detected Hailo architecture: {hailo_arch}")
    resource_path = Path(os.getenv("RESOURCE_PATH", "/usr/local/hailo/resources"))
    models_base_url = config["defaults"]["model_zoo_url"]
    model_zoo_version = os.getenv("MODEL_ZOO_VERSION")
    print(f"================Model Zoo version: {model_zoo_version}===================")

    if group is None or group == "default":
        # default = combined + arch‐specific
        selected_groups = ["combined", hailo_arch]
    else:
        selected_groups = list(config["groups"].get("all", []))

        # 4) Figure out which groups to pull
    if group is None or group == "default":
        # default = combined + arch‑specific
        selected_groups = ["combined", hailo_arch]
    elif group == "all":
        selected_groups = ["all"]
    elif group in config["groups"]:
        selected_groups = [group]
    else:
        logger.error(f"Unknown group '{group}'")
        return

    # 5) Flatten into one list
    selected = []
    for grp in selected_groups:
        selected.extend(config["groups"].get(grp, []))

    # 6) Dedupe (preserve first‑seen order)
    seen = set()
    deduped = []
    for item in selected:
        if isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = next(iter(item.keys()))
        else:
            continue

        if name not in seen:
            seen.add(name)
            deduped.append(item)

    # 7) Download models
    for item in deduped:
        if isinstance(item, str):
            # standard model‑zoo entry
            name = item
            url = f"{models_base_url}/{model_zoo_version}/{hailo_arch}/{name}.hef"
        else:
            # full‑URL override (e.g. retrain)
            name, url = next(iter(item.items()))

        dest = resource_path / "models" / hailo_arch / f"{name}.hef"
        print(f"Downloading {name} from {url} to {dest}")
        download_file(url, dest)

    # 8) Download all videos
    for vid_name, vid_cfg in config.get("videos", {}).items():
        url = vid_cfg["url"]
        # Get extension from URL or config, defaulting to .mp4 if not specified
        extension = os.path.splitext(url)[1] if os.path.splitext(url)[1] else vid_cfg.get("extension", ".mp4")
        # Use original filename if provided
        filename = vid_cfg.get("filename", f"{vid_name}{extension}")
        dest = resource_path / "videos" / filename
        download_file(url, dest)

def main():
    p = argparse.ArgumentParser(
        description="Install and download Hailo resources"
    )
    p.add_argument(
        "--group",
        type=str,
        default="default",
        help="Which resource group to download (default, all, combined, hailo8, hailo8l, retrain)",
    )
    args = p.parse_args()
    load_environment()
    # call into your downloader
    download_resources(group=args.group)


if __name__ == "__main__":
    main()
