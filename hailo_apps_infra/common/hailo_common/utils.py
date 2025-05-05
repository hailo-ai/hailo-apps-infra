import os
import subprocess
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv
from hailo_common.common import detect_pkg_installed

logger = logging.getLogger("hailo-utils")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_PATH = PROJECT_ROOT / "resources"

def run_command(command, error_msg):
    logger.info(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        logger.error(f"{error_msg} (exit code {result.returncode})")
        exit(result.returncode)

def run_command_with_output(command):
    logger.info(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}")
        logger.error(result.stderr)
        return None
    return result.stdout.strip()

def create_symlink(source_path, link_path):
    source = Path(source_path)
    link = Path(link_path)
    if link.exists():
        if link.is_symlink():
            logger.info("Symlink already exists.")
            return
        else:
            logger.warning(f"Path {link} exists and is not a symlink.")
            return
    logger.info(f"Creating symlink: {link} -> {source}")
    link.symlink_to(source, target_is_directory=True)

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
    

def load_environment(env_file=PROJECT_ROOT / ".env", required_vars=None):
    """
    Loads environment variables from a .env file and verifies required ones.

    Args:
        env_file (str): Path to the .env file.
        required_vars (list): List of required variable names to validate.
    """
    load_dotenv(dotenv_path=env_file)

    # check if the virtual env is activated and has all dependencies installed
    print(f"Loading environment variables from {env_file}...")
    if not os.path.exists(env_file):
        logger.error(f"⚠️ .env file not found: {env_file}")
        return
    if not os.access(env_file, os.R_OK):
        logger.error(f"⚠️ .env file not readable: {env_file}")
        return
    if not os.access(env_file, os.W_OK):
        logger.error(f"⚠️ .env file not writable: {env_file}")
        return
    if not os.access(env_file, os.F_OK):
        logger.error(f"⚠️ .env file not found: {env_file}")
        return

    required_vars = required_vars or [
        "TAPPAS_POST_PROC_DIR",
        "RESOURCES_PATH",
        "HOST_ARCH",
        "HAILO_ARCH"
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)

    if missing:
        logger.warning("⚠️ Missing environment variables: %s", ", ".join(missing))
    else:
        logger.info("✅ All required environment variables loaded.")


MODEL_MAP = {
    ("detection", "hailo8"): "yolov8m",
    ("detection", "hailo8l"): "yolov8s",

    ("seg", "hailo8"): "yolov5m_seg",
    ("seg", "hailo8l"): "yolov5n_seg",

    ("pose", "hailo8"): "yolov8m_pose",
    ("pose", "hailo8l"): "yolov8s_pose",

    ("depth", "hailo8"): "scdepthv3",
    ("depth", "hailo8l"): "scdepthv3",

    ("simple_detection", "hailo8"): "yolov6n",
    ("simple_detection", "hailo8l"): "yolov6n",
}

def get_model_name(pipeline_name, hailo_arch=None):
    key = (pipeline_name, hailo_arch)
    default_key = (pipeline_name, None)
    
    if key in MODEL_MAP:
        return MODEL_MAP[key]
    elif default_key in MODEL_MAP:
        return MODEL_MAP[default_key]
    else:
        logger.error(f"Unknown pipeline name or arch: {pipeline_name}, {hailo_arch}")
        return None
        

def get_resource_path(pipeline_name, resource_type, model = None):
    """
    Returns the resource path based on the environment variable or default.
    """
    hailo_arch = os.getenv("HAILO_ARCH")
    if (resource_type == "so" or resource_type == "videos") and model is not None:
        return RESOURCE_PATH / resource_type / model
    if (resource_type == "models") and model is not None:
        return (RESOURCE_PATH / resource_type / hailo_arch / model).with_suffix(".hef") 
    elif (resource_type == "models") and pipeline_name is not None and model is None:
        return (RESOURCE_PATH / resource_type / hailo_arch / get_model_name(pipeline_name, hailo_arch)).with_suffix(".hef")    
    else:
        logger.error(f"Unknown pipeline name or arch: {pipeline_name}, {hailo_arch}")
        return None
    

def detect_hailo_package_version(package_name):
    """
    Detects the installed Hailo package version using dpkg-query.
    Args:
        package_name (str): The name of the package to check.
    Returns:
        str: The version of the package, or None if not found.

    Example packages: hailo-tappas-core, hailort-pcie-driver, hailort , hailo-tappas
    """
    try:
        # -W: show package, -f='${Version}' prints just the version
        version = subprocess.check_output(
            ["dpkg-query", "-W", "-f=${Version}", package_name],
            stderr=subprocess.STDOUT,
            text=True
        ).strip()
        return version
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to detect version for {package_name}: {e.output.strip()}")
        return None