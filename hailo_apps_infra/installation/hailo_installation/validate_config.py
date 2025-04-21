import yaml
import logging
import re

logger = logging.getLogger("config-validator")

REQUIRED_KEYS = [
    "hailort_version",
    "tappas_version",
    "apps_infra_version",
    "model_zoo_version",
    "device_arch",
    "hailo_arch"
]

# Additional optional keys that should be validated if present
OPTIONAL_KEYS = [
    "resources_path",
    "auto_symlink",
    "virtual_env_name",
    "server_url",
    "deb_whl_dir"
]

# Valid options for certain fields
VALID_DEVICE_ARCH = ["auto", "rpi", "x86", "arm"]
VALID_HAILO_ARCH = ["auto", "hailo8", "hailo8l"]

def validate_config(config):
    """
    Validate configuration file contents.
    Checks for required keys and validates format of values.
    """
    logger.info("Validating config keys...")
    
    # Check for required keys
    for key in REQUIRED_KEYS:
        if key not in config:
            raise KeyError(f"Missing required config key: {key}")
    
    # Validate version formats
    if "hailort_version" in config and config["hailort_version"] != "auto":
        if not is_valid_version_format(config["hailort_version"]):
            logger.warning(f"hailort_version should be in format X.Y.Z (got: {config['hailort_version']})")
    
    if "tappas_version" in config and config["tappas_version"] != "auto":
        if not is_valid_version_format(config["tappas_version"]):
            logger.warning(f"tappas_version should be in format X.Y.Z (got: {config['tappas_version']})")
    
    if "apps_infra_version" in config and config["apps_infra_version"] != "auto":
        if not is_valid_version_format(config["apps_infra_version"]):
            logger.warning(f"apps_infra_version should be in format X.Y.Z (got: {config['apps_infra_version']})")
    
    if "model_zoo_version" in config and config["model_zoo_version"] != "auto":
        if not config["model_zoo_version"].startswith("v") or not is_valid_version_format(config["model_zoo_version"][1:]):
            logger.warning(f"model_zoo_version should be in format vX.Y.Z (got: {config['model_zoo_version']})")
    
    # Validate device architecture
    if "device_arch" in config and config["device_arch"] != "auto":
        if config["device_arch"] not in VALID_DEVICE_ARCH:
            logger.warning(f"device_arch should be one of {VALID_DEVICE_ARCH} (got: {config['device_arch']})")
    
    # Validate Hailo architecture
    if "hailo_arch" in config and config["hailo_arch"] != "auto":
        if config["hailo_arch"] not in VALID_HAILO_ARCH:
            logger.warning(f"hailo_arch should be one of {VALID_HAILO_ARCH} (got: {config['hailo_arch']})")
    
    # Validate server URL format
    if "server_url" in config and config["server_url"] != "auto":
        if not config["server_url"].startswith(("http://", "https://")):
            logger.warning(f"server_url should start with http:// or https:// (got: {config['server_url']})")
    
    # Validate resources_path is a string
    if "resources_path" in config and config["resources_path"] != "auto":
        if not isinstance(config["resources_path"], str):
            logger.warning(f"resources_path should be a string (got: {type(config['resources_path']).__name__})")
    
    # Validate auto_symlink is boolean
    if "auto_symlink" in config and config["auto_symlink"] != "auto":
        if not isinstance(config["auto_symlink"], bool):
            logger.warning(f"auto_symlink should be a boolean (got: {type(config['auto_symlink']).__name__})")
    
    # Validate virtual_env_name is a string
    if "virtual_env_name" in config and config["virtual_env_name"] != "auto":
        if not isinstance(config["virtual_env_name"], str):
            logger.warning(f"virtual_env_name should be a string (got: {type(config['virtual_env_name']).__name__})")
    
    # Validate deb_whl_dir is a string
    if "deb_whl_dir" in config and config["deb_whl_dir"] != "auto":
        if not isinstance(config["deb_whl_dir"], str):
            logger.warning(f"deb_whl_dir should be a string (got: {type(config['deb_whl_dir']).__name__})")
    
    logger.info("Config validation complete.")
    return config


def is_valid_version_format(version_str):
    """Check if a string is in the format X.Y.Z where X, Y, Z are integers."""
    try:
        parts = version_str.split('.')
        if len(parts) != 3:
            return False
        return all(part.isdigit() for part in parts)
    except:
        return False


def print_config_summary(config):
    """Print a summary of the validated configuration."""
    print("\n=== Hailo Configuration Summary ===")
    
    # Print required keys first
    print("Required Configuration:")
    for key in sorted(REQUIRED_KEYS):
        if key in config:
            print(f"  {key}: {config[key]}")
        else:
            print(f"  {key}: MISSING")
    
    # Print optional keys
    print("\nOptional Configuration:")
    for key in sorted(set(config.keys()) - set(REQUIRED_KEYS)):
        print(f"  {key}: {config[key]}")
    
    print("==================================\n")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        validated_config = validate_config(config)
        print_config_summary(validated_config)
    except FileNotFoundError:
        logger.error("Config file not found. Please create a config.yaml file.")
    except KeyError as e:
        logger.error(f"Invalid configuration: {e}")