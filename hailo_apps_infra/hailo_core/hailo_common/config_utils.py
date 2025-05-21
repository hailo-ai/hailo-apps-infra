"""
Configuration module: loads defaults, file config, CLI overrides, and merges them.
"""
import sys
from pathlib import Path
import yaml

from .defines import (
    # Config keys
    HAILORT_VERSION_KEY,
    TAPPAS_VERSION_KEY,
    MODEL_ZOO_VERSION_KEY,
    HOST_ARCH_KEY,
    HAILO_ARCH_KEY,
    SERVER_URL_KEY,
    TAPPAS_VARIANT_KEY,
    RESOURCES_PATH_KEY,
    VIRTUAL_ENV_NAME_KEY,
    # Default values
    HAILORT_VERSION_DEFAULT,
    TAPPAS_VERSION_DEFAULT,
    MODEL_ZOO_VERSION_DEFAULT,
    HOST_ARCH_DEFAULT,
    HAILO_ARCH_DEFAULT,
    SERVER_URL_DEFAULT,
    TAPPAS_VARIANT_DEFAULT,
    DEFAULT_RESOURCES_SYMLINK_PATH,
    VIRTUAL_ENV_NAME_DEFAULT,
    STORAGE_PATH_DEFAULT,
    # Valid choices
    VALID_HAILORT_VERSION,
    VALID_TAPPAS_VERSION,
    VALID_MODEL_ZOO_VERSION,
    VALID_HOST_ARCH,
    VALID_HAILO_ARCH,
    VALID_SERVER_URL,
    VALID_TAPPAS_VARIANT,
)

def load_config(path: Path) -> dict:
    """Load YAML file or exit if missing."""
    if not path.is_file():
        print(f"❌ Config file not found at {path}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(path.read_text()) or {}


def load_default_config() -> dict:
    """Return the built-in default config values."""
    return {
        HAILORT_VERSION_KEY: HAILORT_VERSION_DEFAULT,
        TAPPAS_VERSION_KEY: TAPPAS_VERSION_DEFAULT,
        MODEL_ZOO_VERSION_KEY: MODEL_ZOO_VERSION_DEFAULT,
        HOST_ARCH_KEY: HOST_ARCH_DEFAULT,
        HAILO_ARCH_KEY: HAILO_ARCH_DEFAULT,
        SERVER_URL_KEY: SERVER_URL_DEFAULT,
        TAPPAS_VARIANT_KEY: TAPPAS_VARIANT_DEFAULT,
        RESOURCES_PATH_KEY: DEFAULT_RESOURCES_SYMLINK_PATH,
        VIRTUAL_ENV_NAME_KEY: VIRTUAL_ENV_NAME_DEFAULT,
    }

def validate_config(config: dict) -> bool:
    """Validate each config value against its valid choices."""
    valid_config=True
    valid_map = {
        HAILORT_VERSION_KEY: VALID_HAILORT_VERSION,
        TAPPAS_VERSION_KEY: VALID_TAPPAS_VERSION,
        MODEL_ZOO_VERSION_KEY: VALID_MODEL_ZOO_VERSION,
        HOST_ARCH_KEY: VALID_HOST_ARCH,
        HAILO_ARCH_KEY: VALID_HAILO_ARCH,
        SERVER_URL_KEY: VALID_SERVER_URL,
        TAPPAS_VARIANT_KEY: VALID_TAPPAS_VARIANT,
    }
    for key, valid_choices in valid_map.items():
        val = config.get(key)
        if val not in valid_choices:
            valid_config = False
            print(f"Invalid value '{val}'. Valid options: {valid_choices}")
    return valid_config

def load_and_validate_config(config_path: str) -> dict:
    """
    Load and validate the configuration file.
    Returns the loaded configuration as a dictionary.
    """
    cfg_path = Path(config_path)
    config = load_config(cfg_path)
    if not validate_config(config):
        print("❌ Invalid configuration. Please check the config file.")
        sys.exit(1)
    return config

