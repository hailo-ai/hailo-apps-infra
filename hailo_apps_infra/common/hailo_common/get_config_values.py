#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml
import argparse


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_PATH = PROJECT_ROOT / "resources"

def load_config() -> dict:
    """
    Load hailo_config/config.yaml and return it as a dict.
    """
    cfg_path   = PROJECT_ROOT / "hailo_apps_infra" / "config" / "hailo_config" / "config.yaml"

    if not cfg_path.is_file():
        print(f"❌ Config file not found at {cfg_path}", file=sys.stderr)
        sys.exit(1)

    return yaml.safe_load(cfg_path.read_text())

def get_config_value(key: str) -> str:
    """
    Return the value for `key` from the loaded config.
    """
    config = load_config()
    if key not in config:
        raise KeyError(f"Key '{key}' not found in config.yaml")
    return config[key]

def main():
    # Load once to get available keys
    config = load_config()
    keys = sorted(config.keys())

    parser = argparse.ArgumentParser(
        description="Retrieve a value from hailo_config/config.yaml"
    )
    parser.add_argument(
        "key",
        choices=keys,
        help="Which config key to retrieve (choose from: " + ", ".join(keys) + ")"
    )
    args = parser.parse_args()

    try:
        value = config[args.key]
    except KeyError:
        # argparse should prevent this, but just in case
        print(f"❌ Key '{args.key}' not found.", file=sys.stderr)
        sys.exit(1)

    print(value)

if __name__ == "__main__":
    main()
