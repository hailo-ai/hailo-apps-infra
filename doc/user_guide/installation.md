# Hailo Software Installation Guide

This guide provides comprehensive instructions for installing the Hailo Application Infrastructure on both x86_64 Ubuntu systems and Raspberry Pi devices.

## Table of Contents

- [Hailo Software Installation Guide](#hailo-software-installation-guide)
  - [Table of Contents](#table-of-contents)
  - [Quick Start (Automated Recommended)](#quick-start-automated-recommended)
  - [x86\_64 Ubuntu Installation](#x86_64-ubuntu-installation)
    - [Prerequisites for x86](#prerequisites-for-x86)
    - [Installation Steps for x86](#installation-steps-for-x86)
    - [Manual Installation for x86](#manual-installation-for-x86)
  - [Raspberry Pi Installation](#raspberry-pi-installation)
    - [Hardware Setup for RPi](#hardware-setup-for-rpi)
    - [Software Setup for RPi](#software-setup-for-rpi)
    - [Verification for RPi](#verification-for-rpi)
  - [Post-Installation Verification](#post-installation-verification)
  - [Uninstallation](#uninstallation)

---

## Quick Start (Automated Recommended)

This is the easiest and recommended way to get started on any supported platform. The script automatically detects your environment and installs the appropriate packages.

```bash
# 1. Clone the repository
git clone https://github.com/hailo-ai/hailo-apps-infra.git
cd hailo-apps-infra

# 2. Run the automated installation script
./install.sh
```

The installation script will:
1. Create a Python virtual environment (`venv_hailo_apps` by default).
2. Install all required system and Python dependencies.
3. Download necessary AI model files.
4. Configure the environment.

For more options, such as using a custom virtual environment name:
```bash
# Use a custom virtual environment name
./install.sh --venv-name my_custom_env

# Download all available models (not just the default ones)
./install.sh --all
```

For newer versions, please visit the [Hailo Developer Zone](https://hailo.ai/developer-zone/).

<details>
<summary><b>Manual Installation for x86 (Advanced)</b></summary>

If you need full control over the process:

1.  **Create & activate a virtual environment**
    ```bash
    python3 -m venv your_venv_name --system-site-packages
    source your_venv_name/bin/activate
    ```
2.  **Install Hailo Python packages**
    This script will install the HailoRT driver, runtime, and Tappas libraries.
    ```bash
    ./scripts/hailo_python_installation.sh
    ```
3.  **Install repository dependencies**
    ```bash
    pip install --upgrade pip
    pip install -e .
    ```
4.  **Run post-install setup**
    This downloads models and configures the environment.
    ```bash
    hailo-post-install
    ```
</details>

---

## x86_64 Ubuntu Installation

These instructions are for installing the Hailo software stack on a standard x86_64 machine running Ubuntu 22.04.

### Prerequisites for x86

* **Operating System**: Ubuntu 22.04
* **Hardware**: Hailo-8, Hailo-8L, or Hailo-10H accelerator.
* **Software**:
  * Python 3.10
  * `git`, `python3-venv`

### Installation Steps for x86

The `hailo_installer.sh` script handles the installation of the HailoRT and Tappas Core libraries. The main `install.sh` script in the root directory will run this for you, but you can also run it manually for custom installations.

**Default Installation:**
```bash
./scripts/hailo_installer.sh
```
This installs the default versions of HailoRT (4.20.0) and Tappas Core (3.31.0).

**Custom Version Installation:**
If you need specific versions, use the following flags:
```bash
./scripts/hailo_installer.sh \
  --hailort-version=4.20.0 \
  --tappas-core-version=3.31.0
```

For newer versions, please visit the [Hailo Developer Zone](https://hailo.ai/developer-zone/).

### Manual Installation for x86

If you need full control over the process:

1.  **Create & activate a virtual environment**
    ```bash
    python3 -m venv your_venv_name --system-site-packages
    source your_venv_name/bin/activate
    ```
2.  **Install Hailo Python packages**
    This script will install the HailoRT driver, runtime, and Tappas libraries.
    ```bash
    ./scripts/hailo_python_installation.sh
    ```
3.  **Install repository dependencies**
    ```bash
    pip install --upgrade pip
    pip install -e .
    ```
4.  **Run post-install setup**
    This downloads models and configures the environment.
    ```bash
    hailo-post-install
    ```

---

## Raspberry Pi Installation

These instructions are for setting up a Raspberry Pi 5 with a Hailo AI accelerator.

### Hardware Setup for RPi

1.  **Required Hardware**:
    *   Raspberry Pi 5 (8GB recommended) with Active Cooler.
    *   A Hailo accelerator:
        *   **Raspberry Pi AI Kit**: M.2 HAT + Hailo-8L/Hailo-8 Module.
        *   **Raspberry Pi AI HAT+**: A board with an integrated Hailo accelerator (13 or 26 TOPs).
    *   A 27W USB-C Power Supply.

2.  **Assembly**:
    *   **For AI Kit**: Follow the [Raspberry Pi's official AI Kit Guide](https://www.raspberrypi.com/documentation/accessories/ai-kit.html#ai-kit).
        *   Ensure a thermal pad is placed between the M.2 module and the HAT.
        *   Ensure the GPIO header is connected for stable operation.
    *   **For AI HAT+**: Follow the [Raspberry Pi's official AI HAT+ Guide](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html#ai-hat-plus).
        *   Ensure the GPIO header is connected for stable operation.

### Software Setup for RPi

1.  **Install Raspberry Pi OS**:
    *   Use the Raspberry Pi Imager to install the latest version of Raspberry Pi OS from [here](https://www.raspberrypi.com/software/).

2.  **Install Hailo Software**:
    *   The official Raspberry Pi AI stack includes the Hailo firmware and runtime. Follow the [Raspberry Pi's official AI Software Guide](https://www.raspberrypi.com/documentation/computers/ai.html#getting-started).

3.  **Enable PCIe Gen3 for Optimal Performance**:
    *   This is required for the M.2 HAT to achieve full performance. The AI HAT+ should configure this automatically if the GPIO is connected.
    *   Open the configuration tool: `sudo raspi-config`
    *   Go to `6 Advanced Options` -> `A8 PCIe Speed`.
    *   Choose `Yes` to enable PCIe Gen 3 mode.
    *   Reboot the Raspberry Pi: `sudo reboot`.

### Verification for RPi

1.  **Check if the Hailo chip is recognized**:
    ```bash
    hailortcli fw-control identify
    ```
    This should show your board details (e.g., Board Name: Hailo-8). If not, see the troubleshooting section.

2.  **Check GStreamer plugins**:
    *   Verify `hailotools`: `gst-inspect-1.0 hailotools`
    *   Verify `hailo` (inference element): `gst-inspect-1.0 hailo`
    *   If a plugin is not found, you may need to clear the GStreamer cache: `rm ~/.cache/gstreamer-1.0/registry.aarch64.bin` and reboot.

---

## Post-Installation Verification

After running any of the installation methods, you can verify that everything is working correctly.

1.  **Activate your environment**
    ```bash
    source hailo_infra_venv/bin/activate
    ```
2.  **Check installed Hailo packages**
    ```bash
    pip list | grep hailo
    # You should see packages like hailort, hailo-tappas-core, and hailo-apps-infra.

    apt list | grep hailo
    # This shows all installed Hailo-related system packages.
    ```
3.  **Verify the Hailo device connection**
    ```bash
    hailortcli fw-control identify
    ```
4.  **Run a demo application**
    ```bash
    hailo-detect-simple
    ```
    A video window with live detections should appear.

<details>
<summary><b>Troubleshooting Tips</b></summary>

*   **PCIe Issues (RPi)**: If `lspci | grep Hailo` shows no device, check your M.2 HAT or AI HAT+ connections, power supply, and ensure PCIe is enabled in `raspi-config`.
*   **Driver Issues (RPi)**: If you see driver errors, ensure your kernel is up to date (`sudo apt update && sudo apt full-upgrade`).
*   **`DEVICE_IN_USE()` Error**: This means the Hailo device is being used by another process. Run the cleanup script: `./scripts/kill_first_hailo.sh`.
*   **GStreamer `cannot allocate memory in static TLS block` (RPi)**: This is a known issue. Add `export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1` to your `~/.bashrc` file and reboot.

</details>

---

## Uninstallation

To remove the environment and downloaded resources:

```bash
# Deactivate the virtual environment if active
deactivate

# Delete project files and logs
sudo rm -rf hailo_infra_venv/ resources/ hailort.log .env hailo_apps_infra.egg-info
```
To uninstall system packages, use `apt remove`.