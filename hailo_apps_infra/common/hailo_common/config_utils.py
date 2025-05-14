"""
Configuration module: loads defaults, file config, CLI overrides, and merges them.
"""
import sys
from pathlib import Path
import yaml
import argparse

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
    STORAGE_DIR_KEY,
    # Default values
    HAILORT_VERSION_DEFAULT,
    TAPPAS_VERSION_DEFAULT,
    MODEL_ZOO_VERSION_DEFAULT,
    HOST_ARCH_DEFAULT,
    HAILO_ARCH_DEFAULT,
    SERVER_URL_DEFAULT,
    TAPPAS_VARIANT_DEFAULT,
    RESOURCES_PATH_DEFAULT,
    VIRTUAL_ENV_NAME_DEFAULT,
    STORAGE_DIR_DEFAULT,
    # Valid choices
    VALID_HAILORT_VERSION,
    VALID_TAPPAS_VERSION,
    VALID_MODEL_ZOO_VERSION,
    VALID_HOST_ARCH,
    VALID_HAILO_ARCH,
    VALID_SERVER_URL,
    VALID_TAPPAS_VARIANT,
    # File path
    DEFAULT_CONFIG_PATH
)


def load_yaml(path: Path) -> dict:
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
        RESOURCES_PATH_KEY: RESOURCES_PATH_DEFAULT,
        VIRTUAL_ENV_NAME_KEY: VIRTUAL_ENV_NAME_DEFAULT,
        STORAGE_DIR_KEY: STORAGE_DIR_DEFAULT,
    }


def merge_configs(base: dict, override: dict) -> dict:
    """Overlay `override` values onto `base`, skipping None entries."""
    merged = base.copy()
    for k, v in override.items():
        if v is not None:
            merged[k] = v
    return merged


def validate_config(config: dict) -> (bool, dict):
    """Validate each config value against its valid choices."""
    errors = {}
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
            errors[key] = f"Invalid value '{val}'. Valid options: {valid_choices}"
    return (False, errors) if errors else (True, {})


def parse_cli_args():
    """Parse CLI flags for config overrides."""
    parser = argparse.ArgumentParser(description="Hailo Infra Config")
    parser.add_argument(
        '-c', '--config', type=Path, default=None,
        help=f"Path to YAML config (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument('--hailort-version', choices=VALID_HAILORT_VERSION, help='HailoRT version')
    parser.add_argument('--tappas-version', choices=VALID_TAPPAS_VERSION, help='Tappas version')
    parser.add_argument('--model-zoo-version', choices=VALID_MODEL_ZOO_VERSION, help='Model zoo version')
    parser.add_argument('--host-arch', choices=VALID_HOST_ARCH, help='Host architecture')
    parser.add_argument('--hailo-arch', choices=VALID_HAILO_ARCH, help='Hailo architecture')
    parser.add_argument('--server-url', choices=VALID_SERVER_URL, help='Server URL')
    parser.add_argument('--tappas-variant', choices=VALID_TAPPAS_VARIANT, help='Tappas variant')
    parser.add_argument('--resources-path', help='Path to resources directory')
    parser.add_argument('--virtual-env-name', help='Virtual environment name')
    parser.add_argument('--storage-dir', help='Directory for deb/whl storage')
    return parser.parse_args()


def load_config_from_cli() -> dict:
    """Build the final config by merging defaults, file, and CLI overrides."""
    args = parse_cli_args()
    cfg = load_default_config()
    cfg_file = load_yaml(args.config) if args.config else load_yaml(Path(DEFAULT_CONFIG_PATH))
    cfg = merge_configs(cfg, cfg_file)
    cli_overrides = {
        HAILORT_VERSION_KEY: args.hailort_version,
        TAPPAS_VERSION_KEY: args.tappas_version,
        MODEL_ZOO_VERSION_KEY: args.model_zoo_version,
        HOST_ARCH_KEY: args.host_arch,
        HAILO_ARCH_KEY: args.hailo_arch,
        SERVER_URL_KEY: args.server_url,
        TAPPAS_VARIANT_KEY: args.tappas_variant,
        RESOURCES_PATH_KEY: args.resources_path,
        VIRTUAL_ENV_NAME_KEY: args.virtual_env_name,
        STORAGE_DIR_KEY: args.storage_dir,
    }
    cfg = merge_configs(cfg, cli_overrides)
    valid, errors = validate_config(cfg)
    if not valid:
        for k, err in errors.items():
            print(f"❌ {err}", file=sys.stderr)
        sys.exit(1)
    return cfg


if __name__ == '__main__':
    final_cfg = load_config_from_cli()
    for k, v in final_cfg.items():
        print(f"{k}={v}")