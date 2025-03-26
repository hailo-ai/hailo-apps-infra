import yaml
import logging

logger = logging.getLogger("config-validator")

REQUIRED_KEYS = [
    "hailort_version",
    "tappas_version",
    "apps_infra_version",
    "model_zoo_version",
    "device_arch",
    "hailo_arch"
    ]

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_config(config):
    logger.info("Validating config keys...")
    for key in REQUIRED_KEYS:
        if key not in config:
            raise KeyError(f"Missing required config key: {key}")
    logger.info("Config is valid.")
