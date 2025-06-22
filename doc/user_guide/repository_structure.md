# Repository Structure Guide

This document provides an overview of the directory structure for the Hailo Applications repository, explaining the purpose of each key folder.

```
hailo-apps/
├── doc/                            # Comprehensive documentation
├── hailo_apps_infra/
│   ├── hailo_core/                 # Core infrastructure and utilities
│   └── hailo_apps/                 # Reusable GStreamer components and applications
├── scripts/                        # Installation and utility scripts
├── tests/                          # Test suite for the project
├── install.sh                      # Main installation script
└── pyproject.toml                  # Package configuration for installation
```

## Key Directories

### `doc/`
This directory contains all the project documentation, including user guides, developer guides, and architectural overviews. It's the best place to start if you have questions about how to use or extend the repository.

### `hailo_apps_infra/`
This is the heart of the repository, containing all the core Python source code. It is structured as a Python package.

*   **`hailo_core/`**: Contains the foundational utilities that support the entire ecosystem. This includes installation scripts, configuration management, and common helper functions that are used across all applications.
*   **`hailo_apps/`**: Contains the AI applications themselves. This directory is further subdivided into reusable GStreamer components and the final, runnable application scripts.

### `scripts/`
This directory holds various shell scripts used for installation, environment setup, and other utility tasks. The main `install.sh` script orchestrates many of the scripts found here.

### `tests/`
This directory contains the test suite for the project, primarily using the `pytest` framework. These tests ensure the reliability and correctness of the infrastructure and applications.

---

## The `resources` Directory

After running the installation script, you will see a `resources` directory in the root of the project. This is not a regular directory, but rather a **symbolic link** (or symlink).

*   **What it is**: It's a shortcut that points to a system-wide directory, `/usr/share/hailo_resources`.
*   **What it contains**: This central location stores all the large files needed by the applications, such as the compiled AI models (`.hef` files), videos for demonstration, and other assets.
*   **Why it's a symlink**: By using a symlink, we avoid duplicating large files across multiple projects. All your Hailo applications can share a single, central pool of models and videos, saving disk space and making resource management easier. You can add your own models to this directory, and they will be accessible to all applications.