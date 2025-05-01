# Hailo Apps Infrastructure Installation Guide

This comprehensive guide describes how to install and configure the Hailo Apps Infrastructure repository. It covers installation methods, configuration, and post-installation steps.

## Table of Contents

- [Hailo Apps Infrastructure Installation Guide](#hailo-apps-infrastructure-installation-guide)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation Methods](#installation-methods)
    - [1. Automated Installation (`install.sh`)](#1-automated-installation-installsh)
  - [Core Installation Components](#core-installation-components)
    - [Post-Installation Setup](#post-installation-setup)
      - [Purpose](#purpose)
      - [Usage](#usage)
      - [Steps](#steps)
    - [Environment Variable Management](#environment-variable-management)
      - [Purpose](#purpose-1)
      - [Key Variables Written](#key-variables-written)
      - [Usage](#usage-1)
    - [Configuration Validation](#configuration-validation)
      - [Purpose](#purpose-2)
      - [Usage](#usage-2)
    - [Resource Downloading](#resource-downloading)
      - [Purpose](#purpose-3)
      - [Usage](#usage-3)
    - [C++ Post-Processing Compilation](#c-post-processing-compilation)
      - [Purpose](#purpose-4)
      - [Usage](#usage-4)
  - [Integration in Other Repositories](#integration-in-other-repositories)

## Prerequisites

- **Linux** with `bash` and Python 3.8-3.11 for x86 or 3.10 and 3.11 for rpi
- `sudo` privileges (for installing system directories and packages)
- `virtualenv` (bundled with Python 3 `venv` module)
- Internet access (to download wheels, models, videos)

## Installation Methods

---

### 1. Automated Installation (`install.sh`)

**Purpose**  
Automates environment setup for Hailo Infra: detects system architecture, checks/install required system and Python packages, sets up resource directories, configures a Python virtual environment, installs core and optional Hailo modules, handles shared dependencies, and runs final setup.

**Usage**  
```bash
sudo ./install.sh 
```

**What It Does**  
1. **Architecture Detection:**  
   Detects if the host is ARM (RPi) or x86 and chooses the correct system and Python packages.
2. **Resource Directory Creation:**  
   Creates `/usr/local/hailo/resources/{models/hailo8,models/hailo8l,videos,so}` with appropriate user permissions.
3. **System Package Check:**  
   Verifies system packages are installed (`hailo-all` for ARM, `hailort-pcie-driver` for x86, plus Hailo Tappas). Exits if not found.
4. **Python Package Check:**  
   Checks for required pip packages (`hailort` and tappas-core binding for your architecture). Flags missing ones for install inside the venv.
5. **Virtual Environment:**  
   Uses the `VENV_NAME` environment variable (defaults to `hailo_infra_venv`). Creates or activates the venv.  
   - Chooses to include or isolate system packages as needed.
6. **.env File Setup:**  
   Ensures a writable `.env` file exists at the repo root.
7. **Module Installation:**  
   Upgrades `pip`, `setuptools`, `wheel`. Installs core Hailo modules (`common`, `config`, `installation`). Installs optional modules (`gstreamer`, `pipelines`) based on flags.
8. **Requirements Install:**  
   Installs Python dependencies from `requirements.txt`.
9. **Post-Install:**  
   Runs the final post-install setup (`python3 -m hailo_installation.post_install`).


**Location in Repo**  
`install.sh` — found at the repository root.

---
## Core Installation Components

### Post-Installation Setup

**Location:** `hailo_installation` package (`post_install.py`)

#### Purpose

Finalizes installation by linking resources, validating config, setting environment vars, downloading models/videos, and compiling C++ post-processing code.

#### Usage

```bash
# Typically invoked by install.sh
python3 -m hailo_installation.post_install
```

#### Steps

1. **Validate config:** Loads `config.yaml` and runs `validate_config`
2. **Set environment:** Applies `set_environment_vars` to generate/update `.env`
3. **Symlink resources:** Points `./resources` to the configured `resources_path`
4. **Download resources:** Fetches default model/video assets via `download_resources(group="default")`
5. **Compile C++:** Runs `compile_postprocess()` to build post-processing binaries

### Environment Variable Management

**Location:** `hailo_installation` package (`set_env.py`)

#### Purpose

Reads the loaded config and persists environment variables into `.env`, making them available for scripts and runtime.

#### Key Variables Written

- `HOST_ARCH`, `HAILO_ARCH`
- `RESOURCES_PATH`, `TAPPAS_POST_PROC_DIR`, `MODEL_DIR`
- `MODEL_ZOO_VERSION`, `HAILORT_VERSION`, `TAPPAS_VERSION`, `APPS_INFRA_VERSION`
- `VIRTUAL_ENV_NAME`, `SERVER_URL`, `DEB_WHL_DIR`, `TAPPAS_VARIANT`

#### Usage

```bash
python3 hailo_installation/set_env.py
```

Or in your code:

```python
from hailo_installation.set_env import set_environment_vars
from hailo_common.get_config_values import load_config

config = load_config("path/to/config.yaml")
set_environment_vars(config)
```

### Configuration Validation

**Location:** `hailo_installation` package (`validate_config.py`)

#### Purpose

Checks that `config.yaml` contains all required keys and that optional keys are valid. Prints a summary and exits on errors.

#### Usage

```bash
python3 hailo_installation/validate_config.py
```

### Resource Downloading

**Location:** `hailo_installation` package (`download_resources.py`)

#### Purpose

Downloads model `.hef` files and example videos based on `resources_config.yaml` and the current `HAILO_ARCH`.

#### Usage

```bash
# Default (combined + arch-specific):
python3 hailo_installation/download_resources.py

# Specific group (e.g. all, hailo8, hailo8l):
python3 hailo_installation/download_resources.py --group all
```

Or in your code:

```python
from hailo_installation.download_resources import download_resources

download_resources(group="default")
```

### C++ Post-Processing Compilation

**Location:** `hailo_installation` package (`compile_cpp.py`)

#### Purpose

Invokes the shell script `scripts/compile_postprocess.sh` to build C++ post-processing libraries.

#### Usage

```bash
python3 hailo_installation/compile_cpp.py [release|debug|clean]
```

- Default: `release`
- `debug`: build debug binaries
- `clean`: remove build artifacts

Or in your code:

```python
from hailo_installation.compile_cpp import compile_postprocess

# Release build:
compile_postprocess()

# Debug build:
compile_postprocess(mode="debug")
```

## Integration in Other Repositories

To integrate Hailo's installation process into your own repository:

1. Add `hailo_installation` as a dependency
2. Import the required modules:
   - `set_environment_vars` (from `set_env`)
   - `compile_postprocess` (from `compile_cpp`)
   - `download_resources` (from `download_resources`)
   - `post_install` (to tie together the installation steps)
3. Create and configure your own YAML configuration file
4. Invoke the installation process in your setup script or CI/CD pipeline

Example Integration:

```python
from hailo_installation.post_install import post_install

if __name__ == "__main__":
    post_install()
```

For further customization and advanced options, refer to the docstrings at the top of each script file or inspect `config/config/hailo_config/config.yaml` in the `hailo_apps_infra` directory.