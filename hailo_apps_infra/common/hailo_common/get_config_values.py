#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml
import argparse


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_PATH = PROJECT_ROOT / "resources"

# Supported config Options
VALID_HAILORT_VERSION = ["auto", "4.20.0" ,"4.21.0" ,"4.22.0"]
VALID_TAPPAS_VERSION = ["auto","3.30.0", "3.31.0", "3.32.0"]
VALID_MODEL_ZOO_VERSION = ["v2.13.0","v2.14.0", "v2.15.0"]
VALID_HOST_ARCH = ["auto" , "x86" , "rpi" , "arm"]
VALID_HAILO_ARCH = ["auto", "hailo8", "hailo8l"]
VALID_SERVER_URL = ["http://dev-public.hailo.ai/2025_01"]
VALID_TAPPAS_VARIANT = ["auto", "hailo-tappas", "hailo-tappas-core"]

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

def get_default_config_value(key: str) -> str:
    """
    Return the default value for `key` from the default config values.
    """
    default_config = {
        "hailort_version": "auto",
        "tappas_version": "auto",
        "apps_infra_version": "25.3.1",
        "model_zoo_version": "v2.14.0",
        "host_arch": "auto",
        "hailo_arch": "auto",
        "server_url": "http://dev-public.hailo.ai/2025_01",
        "resources_path": "/usr/local/hailo/resources",
        "virtual_env_name": str(PROJECT_ROOT / "hailo_infra_venv"),
        "deb_whl_dir": str(RESOURCE_PATH / "deb_whl"),
        "tappas_variant": "auto",
    }
    return default_config.get(key, None)


def is_valid_config_value(key: str, value: str) -> bool:
    """
    Validate the value for `key` against the list of valid values.
    Returns True only if the value is in the predefined list of valid values for the key.
    """
    if key == "hailort_version":
        return value in VALID_HAILORT_VERSION
    elif key == "tappas_version":
        return value in VALID_TAPPAS_VERSION
    elif key == "model_zoo_version":
        return value in VALID_MODEL_ZOO_VERSION
    elif key == "host_arch":
        return value in VALID_HOST_ARCH
    elif key == "hailo_arch":
        return value in VALID_HAILO_ARCH
    elif key == "server_url":
        return value in VALID_SERVER_URL
    elif key == "deb_whl_dir":
        # For string-type config values without predefined lists,
        # we validate that they're non-empty strings
        return isinstance(value, str) and bool(value)
    elif key == "resources_path":
        return isinstance(value, str) and bool(value)
    elif key == "virtual_env_name":
        return isinstance(value, str) and bool(value)
    elif key == "apps_infra_version":
        # For version format values without predefined lists,
        # validate format (e.g., x.y.z)
        return isinstance(value, str) and value.count(".") == 2
    elif key == "tappas_variant":
        return value in VALID_TAPPAS_VARIANT
    else:
        return False
    
def validate_config(config: dict) -> (bool):
    """
    Validate the complete config dict.
    
    """
    errors = {}
    for key, value in config.items():
        if not is_valid_config_value(key, value):
            errors[key] = f"Invalid value '{value}' for key '{key}'."
    return (False, errors) if errors else (True, {})


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
