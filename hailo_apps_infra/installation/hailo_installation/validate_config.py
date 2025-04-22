import sys
import logging
from pathlib import Path

# Import functions from get_config_values
from hailo_common.get_config_values import (
    load_config, validate_config
)

logger = logging.getLogger(__name__)

# Define required and optional keys
REQUIRED_KEYS = {"server_url"}

OPTIONAL_KEYS = {
    "hailort_version", "tappas_version", "model_zoo_version",
    "host_arch", "hailo_arch", "resources_path", "virtual_env_name", 
    "deb_whl_dir" , "apps_infra_version" , "tappas_variant"
}

# All valid configuration keys
ALL_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS



def print_config_summary(config):
    """Print a summary of required vs optional settings."""
    print("=== Configuration Summary ===")
    print("Required (explicit) settings:")
    for key in sorted(REQUIRED_KEYS):
        print(f"  {key}: {config.get(key, 'MISSING')}")
    print("Optional (auto) settings:")
    for key in sorted(OPTIONAL_KEYS):
        print(f"  {key}: {config.get(key, 'auto')}")
    print("============================")


def validate_config_file():
    """
    Load and validate the configuration file.
    Uses the valid config checks from get_config_values.py.
    """
    try:
        cfg = load_config()
        
        # Validate config values using the common function
        valid, errors = validate_config(cfg)
        if not valid:
            for key, err in errors.items():
                logger.error(err)
            raise ValueError("Invalid configuration values found.")

        # Check that required keys are not set to 'auto'
        for key in REQUIRED_KEYS:
            if cfg.get(key) == "auto" and key != "auto_symlink":  # Allow auto_symlink to be 'auto'
                raise KeyError(f"Required config key '{key}' cannot be 'auto'")

        # Warn on unknown keys
        for key in cfg:
            if key not in ALL_KEYS:
                logger.warning(f"Unknown config key: {key}")

        print_config_summary(cfg)
        logger.info("Config validation complete.")
        return cfg
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_config_file()