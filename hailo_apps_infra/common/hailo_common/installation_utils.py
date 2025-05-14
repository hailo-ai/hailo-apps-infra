"""
Installation-related utilities.
"""
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from .utils import run_command_with_output
from .defines import  PIP_CMD, PROJECT_ROOT

logger = __import__('logging').getLogger("hailo_install")

def load_environment(env_path: Path = None) -> None:
    """
    Load a .env file into process environment variables.
    """
    # Default to PROJECT_ROOT/.env if no path given
    env_path = env_path or PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment from {env_path}")
    
def detect_pip_package_installed(pkg: str) -> bool:
    """Check if a pip package is installed."""
    try:
        result = subprocess.run(
            [PIP_CMD, 'show', pkg], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=None
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_pip_package_version(pkg: str) -> str | None:
    """Get pip package version if installed."""
    try:
        output = run_command_with_output([PIP_CMD, 'show', pkg])
        for line in output.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def set_environment_vars(config: dict, env_path: Path = None):
    """Persist environment variables to a .env file."""
    load_dotenv()
    env_path = env_path or PROJECT_ROOT / ".env"
    lines = []
    for key, val in config.items():
        if val is not None:
            lines.append(f"{key.upper()}={val}\n")
    with open(env_path, 'w') as f:
        f.writelines(lines)
    logger.info(f"Environment written to {env_path}")