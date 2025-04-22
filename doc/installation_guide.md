# Hailo Apps Infrastructure Installation Guide

This comprehensive guide describes how to install and configure the Hailo Apps Infrastructure repository. It covers installation methods, configuration, and post-installation steps.

## Table of Contents

- [Hailo Apps Infrastructure Installation Guide](#hailo-apps-infrastructure-installation-guide)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation Methods](#installation-methods)
    - [1. Automated Installation (`install.sh`)](#1-automated-installation-installsh)
      - [Purpose](#purpose)
      - [Usage](#usage)
      - [What It Does](#what-it-does)
    - [2. Development Python Installation](#2-development-python-installation)
      - [Purpose](#purpose-1)
      - [Key Functions](#key-functions)
      - [Usage](#usage-1)
      - [Options](#options)
      - [Example Commands](#example-commands)
      - [Workflow](#workflow)
    - [3. Production Python Installation](#3-production-python-installation)
      - [Purpose](#purpose-2)
      - [Usage](#usage-2)
      - [Options](#options-1)
      - [Workflow](#workflow-1)
    - [4. Manual Installation Sequence](#4-manual-installation-sequence)
  - [Core Installation Components](#core-installation-components)
    - [Post-Installation Setup](#post-installation-setup)
      - [Purpose](#purpose-3)
      - [Usage](#usage-3)
      - [Steps](#steps)
    - [Environment Variable Management](#environment-variable-management)
      - [Purpose](#purpose-4)
      - [Key Variables Written](#key-variables-written)
      - [Usage](#usage-4)
    - [Configuration Validation](#configuration-validation)
      - [Purpose](#purpose-5)
      - [Usage](#usage-5)
    - [Resource Downloading](#resource-downloading)
      - [Purpose](#purpose-6)
      - [Usage](#usage-6)
    - [C++ Post-Processing Compilation](#c-post-processing-compilation)
      - [Purpose](#purpose-7)
      - [Usage](#usage-7)
  - [Integration in Other Repositories](#integration-in-other-repositories)

## Prerequisites

- **Linux/macOS** with `bash` and Python 3.7+
- `sudo` privileges (for installing system directories and packages)
- `virtualenv` (bundled with Python 3 `venv` module)
- Internet access (to download wheels, models, videos)

## Installation Methods

### 1. Automated Installation (`install.sh`)

**Location:** Repository root

#### Purpose

Creates resource directories, bootstraps a Python virtual environment, installs core and optional Hailo modules, installs shared runtime dependencies, and runs post-install setup.

#### Usage

```bash
# From repo root, give execute permission if needed:
chmod +x install.sh

# Install only GStreamer bindings:
sudo ./install.sh --gstreamer-only

# Install pipelines + GStreamer:
sudo ./install.sh --pipelines-only

# Install everything (GStreamer + pipelines):
sudo ./install.sh --all
```

#### What It Does

1. **Directory setup:** Creates `/usr/local/hailo/resources/{models/hailo8,models/hailo8l,videos,so}` with correct permissions.
2. **Virtual environment:** Reads `virtual_env_name` from config (defaults to `hailo_infra_venv`).
   - Creates venv if missing; installs x86-only deps (`pyhailort`, `tappas-core-bindings`) on x86 hosts.
   - Activates venv for subsequent installs.
3. **Environment file:** Ensures a writable `.env` in the repo root.
4. **Python packages:** Upgrades `pip setuptools wheel`, installs core modules (`common`, `config`, `installation`), and optional modules (`gstreamer`, `pipelines`) inside the venv.
5. **Runtime deps:** Installs `requirements.txt`.
6. **Post-install hook:** Runs `python3 -m hailo_installation.post_install` to finalize setup.

### 2. Development Python Installation

**Location:** `hailo_apps_infra/installation/python_installation_dev.py`

#### Purpose

Flexible installer targeting development workflows. Auto-detects or uses provided HailoRT/TAPPAS versions and wheel locations. Installs wheels into a named venv.

#### Key Functions

- **create_virtualenv(venv_dir)**  
  - Checks if the virtual environment exists  
  - Creates one if needed using `python3 -m venv venv_dir`
  - Logs success or failure

- **install_wheel(wheel_path)**  
  - Installs a wheel file using pip
  - Validates the existence of the wheel file

#### Usage

```bash
python3 python_installation_dev.py [OPTIONS]
```

#### Options

| Flag                   | Description                                                  |
|------------------------|--------------------------------------------------------------|
| `--venv-name NAME`     | Virtualenv directory (default: from config or `hailo_venv`) |
| `--hailort-version VER`| HailoRT version (auto-detected if `auto`)                   |
| `--tappas-version VER` | TAPPAS version (auto-detected if `auto`)                     |
| `--hailort-wheel PATH` | Path to existing HailoRT `.whl`                              |
| `--tappas-wheel PATH`  | Path to existing TAPPAS `.whl`                               |
| `--force-venv`         | Force venv install even if globally installed               |
| `-v`, `--verbose`      | Enable debug logging                                        |

#### Example Commands

```bash
# Basic installation using defaults
python3 python_installation_dev.py

# Custom virtual environment and version settings
python3 python_installation_dev.py --venv-name my_hailo_env --hailort-version 4.20.0 --tappas-version 3.31.0

# Force virtualenv with verbose logging
python3 python_installation_dev.py --force-venv --verbose

# Using pre-downloaded wheel files
python3 python_installation_dev.py --hailort-wheel /path/to/hailort.whl --tappas-wheel /path/to/tappas.whl
```

#### Workflow

1. Parses args; auto-detects missing values via config or system inspection
2. Creates/activates the Python venv
3. Installs specified wheels (`hailort-<ver>-<py_tag>-<platform>.whl`, `tappas_core_python_binding-<ver>.whl`)
4. Prints installed Hailo package versions

### 3. Production Python Installation

**Location:** Repository root (`python_installation.py`)

#### Purpose

Simplified installer for end users. Downloads official wheels from the Hailo server if not cached, sets up a venv, and installs Hailo Python bindings.

#### Usage

```bash
python3 python_installation.py [OPTIONS]
```

#### Options

| Flag                   | Description                                              |
|------------------------|----------------------------------------------------------|
| `--venv-name NAME`     | Virtualenv directory (default: `hailo_venv`)             |
| `--hailort-version VER`| HailoRT version (default: `4.20.0`)                      |
| `--tappas-version VER` | TAPPAS core version (default: `3.31.0`)                  |
| `--hailort-wheel PATH` | Path to existing HailoRT wheel                           |
| `--tappas-wheel PATH`  | Path to existing TAPPAS wheel                            |
| `--force-venv`         | Force install in venv even if globally present          |
| `-v`, `--verbose`      | Enable verbose logging                                   |

#### Workflow

1. Detects host and Hailo architectures
2. Skips installation if `hailort` and `hailo_tappas` are already importable (unless `--force-venv`)
3. Downloads wheels from `http://dev-public.hailo.ai/2025_01` into `hailo_temp_resources`
4. Creates/uses venv and installs wheels
5. Prints installed versions and activation instructions

### 4. Manual Installation Sequence

If you prefer to run each step individually:

1. **Clone & enter repo**
   ```bash
   git clone <repo_url> && cd hailo-apps-infra
   ```

2. **(Optional) Create venv & install Python bindings**
   ```bash
   python3 python_installation.py --venv-name my_env
   source my_env/bin/activate
   ```

3. **Validate configuration**
   ```bash
   python3 hailo_installation/validate_config.py
   ```

4. **Set environment variables**
   ```bash
   python3 hailo_installation/set_env.py
   ```

5. **Download resources**
   ```bash
   python3 hailo_installation/download_resources.py --group default
   ```

6. **Compile C++ post-processing**
   ```bash
   python3 hailo_installation/compile_cpp.py
   ```

7. **Run post-install hooks**
   ```bash
   python3 -m hailo_installation.post_install
   ```

8. **Activate environment for development**
   ```bash
   source $(grep VIRTUAL_ENV_NAME .env | cut -d '=' -f2)/bin/activate
   ```

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

Checks that `config.yaml` contains all required keys (`server_url`) and that optional keys are valid. Prints a summary and exits on errors.

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