= Hailo Applications Infrastructure Documentation
:toc:
:sectnums:

== Overview

image::doc/images/github_applications_infrastructure.png[]

The Hailo Applications Infrastructure provides the core modular infrastructure for building AI pipelines on the Hailo platform. It supports platforms such as Raspberry Pi 4/5, x86_64, and aarch64 Ubuntu machines.

Key components:
- Modular GStreamer-based pipelines
- Post-processing modules in C++ with Meson build
- Python interface for creating apps and running pipelines
- Unified installer, config, and environment setup

== Getting Started

=== Requirements

You must install the Hailo SDK components before using this repository. Download them from the https://hailo.ai/developer-zone/software-downloads/[Hailo Developer Zone].

Required packages:
- HailoRT driver (deb)
- HailoRT libraries and Python API (deb + whl)
- TAPPAS (or tappas-core deb + Python API)

On Raspberry Pi, use the prebuilt Hailo image. See the https://github.com/hailo-ai/hailo-rpi5-examples/blob/main/doc/install-raspberry-pi5.md[RPi Installation Guide].

=== Installation

To install in a fresh environment:

[source,shell]
----
python3 install/install.py
----

This sets up the environment, compiles post-process C++, downloads resources, and sets environment variables.

If using from another repo like `hailo-rpi5-examples`, override `config.yaml` before calling the installer.

== Repository Structure

[source,text]
----
hailo-apps-infra/
├── config/                  # YAML configuration
├── cpp/                    # C++ post-processing code (Meson build)
├── doc/                    # Development and usage documentation
├── hailo_apps_infra/       # Main Python package
│   ├── common/             # Shared utils
│   ├── core/               # Pipelines (pose, detection, etc.)
│   ├── gstreamer/          # GStreamer helpers
├── install/                # Python-based installation logic
├── scripts/                # Shell build tools (compile, download)
├── resources/              # JSON, images, .so, model data
├── tests/                  # Unit tests and test assets
----

== Developer Guide

See link:doc/development_guide.md[Development Guide] for how to build with:
- `GStreamerApp`
- `AppCallback`
- `pipeline_helper_functions`

== Usage in Other Repos

=== As a Pip Package

[source,shell]
----
pip install git+https://github.com/hailo-ai/hailo-apps-infra.git
----

Or clone and install in editable mode:

[source,shell]
----
git clone https://github.com/hailo-ai/hailo-apps-infra.git
pip install -e ./hailo-apps-infra
----

=== With `hailo-rpi5-examples`

- Add `hailo-apps-infra` as a Git submodule or folder
- Call `install.py` during examples setup
- Use example-level `config.yaml` to override versions and paths

== Post-Processing C++ Modules

C++ `.cpp` files live under `cpp/` and are compiled via `scripts/compile_postprocess.sh` using Meson.

Shared libraries (`.so`) are installed to `resources/` by default. These are used by the GStreamer `hailofilter` plugin for inference post-processing.

== Configuration

Edit `config/config.yaml` to set:

[source,yaml]
----
hailort_version: "4.20.0"
tappas_version: "3.31.0"
apps_infra_version: "25.3.1"
model_zoo_version: "2.14.0"
device_arch: "auto"
hailo_arch: "auto"
resources_path: "auto"
python_version: "3.11"
auto_symlink: true
----

== Environment Variables

These are set during installation and persisted to `.env`:

- `DEVICE_ARCH`
- `HAILO_CHIP_ARCH`
- `TAPPAS_POST_PROC_DIR`
- `MODEL_ZOO_DIR`

Apps load `.env` automatically via `hailo_rpi_common.py`.

== GStreamer Pipeline Usage

See link:doc/development_guide.md[Development Guide] for:
- Pipeline creation using strings or helper functions
- Using `SOURCE_PIPELINE`, `INFERENCE_PIPELINE`, etc.
- Custom callbacks and output handlers
- Running with `--input`, `--use-frame`, `--dump-dot`, etc.

== Contribution

We currently do not accept PRs to this repo.

Contribute through:
- [Community Projects in RPi Examples](https://github.com/hailo-ai/hailo-rpi5-examples/tree/main/community_projects/community_projects.md)
- Reporting issues
- Suggestions in the https://community.hailo.ai/[Hailo Community Forum]

== License

MIT — see link:LICENSE[LICENSE]

== Disclaimer

This infrastructure is provided “AS IS” and tested only on specific versions/platforms. No guarantees are made for use outside those conditions.

