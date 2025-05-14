from pathlib import Path

# Base project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = str(
    PROJECT_ROOT / "hailo_apps_infra" / "config" / "hailo_config" / "config.yaml"
)
DEFAULT_RESOURCES_CONFIG_PATH = str(PROJECT_ROOT / "hailo_apps_infra" / "config" / "hailo_config" / "resources_config.yaml")

# Supported config options
VALID_HAILORT_VERSION = ["auto", "4.20.0", "4.21.0", "4.22.0"]
VALID_TAPPAS_VERSION = ["auto", "3.30.0", "3.31.0", "3.32.0"]
VALID_MODEL_ZOO_VERSION = ["v2.13.0", "v2.14.0", "v2.15.0"]
VALID_HOST_ARCH = ["auto", "x86", "rpi", "arm"]
VALID_HAILO_ARCH = ["auto", "hailo8", "hailo8l"]
VALID_SERVER_URL = ["http://dev-public.hailo.ai/2025_01"]
VALID_TAPPAS_VARIANT = ["auto", "hailo-tappas", "hailo-tappas-core"]

# Config key constants
HAILORT_VERSION_KEY = "hailort_version"
TAPPAS_VERSION_KEY = "tappas_version"
MODEL_ZOO_VERSION_KEY = "model_zoo_version"
HOST_ARCH_KEY = "host_arch"
HAILO_ARCH_KEY = "hailo_arch"
SERVER_URL_KEY = "server_url"
TAPPAS_VARIANT_KEY = "tappas_variant"
RESOURCES_PATH_KEY = "resources_path"
VIRTUAL_ENV_NAME_KEY = "virtual_env_name"
STORAGE_DIR_KEY = "deb_whl_dir"

# Default config values
HAILORT_VERSION_DEFAULT = "auto"
TAPPAS_VERSION_DEFAULT = "auto"
MODEL_ZOO_VERSION_DEFAULT = "v2.14.0"
HOST_ARCH_DEFAULT = "auto"
HAILO_ARCH_DEFAULT = "auto"
SERVER_URL_DEFAULT = "http://dev-public.hailo.ai/2025_01"
TAPPAS_VARIANT_DEFAULT = "auto"
RESOURCES_PATH_DEFAULT = "/usr/local/hailo/resources"
VIRTUAL_ENV_NAME_DEFAULT = "hailo_infra_venv"
STORAGE_DIR_DEFAULT = "deb_whl_dir"

# Resource groups for download_resources
RESOURCES_GROUP_DEFAULT = "default"
RESOURCES_GROUP_ALL = "all"
RESOURCES_GROUP_COMBINED = "combined"

# Resource group names
RESOURCES_GROUP_DEFAULT = "default"
RESOURCES_GROUP_ALL = "all"
RESOURCES_GROUP_COMBINED = "combined"
RESOURCES_GROUP_HAILO8 = "hailo8"
RESOURCES_GROUP_HAILO8L = "hailo8l"
RESOURCES_GROUP_RETRAIN = "retrain"

# YAML config file keys for download_resources
RESOURCES_CONFIG_DEFAULTS_KEY = "defaults"
RESOURCES_MODEL_ZOO_URL_KEY = "model_zoo_url"
RESOURCES_CONFIG_GROUPS_KEY = "groups"
RESOURCES_CONFIG_VIDEOS_KEY = "videos"

# Resources directory structure
RESOURCES_MODELS_DIR_NAME = "models"
RESOURCES_VIDEOS_DIR_NAME = "videos"
RESOURCES_SO_DIR_NAME = "so"

# Installation & subprocess defaults
PIP_CMD = "pip"
PIP_SHOW_TIMEOUT = 5  # seconds
INSTALL_LOG = "env_setup.log"

# Testing defaults
TEST_RUN_TIME = 10  # seconds
TERM_TIMEOUT = 5    # seconds

# USB device discovery
UDEV_CMD = "udevadm"

# Miscellaneous
EPSILON = 1e-6