# Hailo Software Installation Guide

This guide provides comprehensive instructions for installing the Hailo Application Infrastructure on both x86_64 Ubuntu systems and Raspberry Pi devices.

## Table of Contents

- [Hailo Software Installation Guide](#hailo-software-installation-guide)
  - [Table of Contents](#table-of-contents)
  - [Automated Installation (Recommended)](#automated-installation-recommended)
  - [Download Resources](#download-resources)
    - [Usage](#usage)
    - [Available Options](#available-options)
    - [Resource Groups](#resource-groups)
    - [Examples](#examples)
  - [Raspberry Pi Installation](#raspberry-pi-installation)
    - [Hardware Setup for RPi](#hardware-setup-for-rpi)
    - [Software Setup for RPi](#software-setup-for-rpi)
    - [Verification for RPi](#verification-for-rpi)
  - [Post-Installation Verification](#post-installation-verification)
  - [Uninstallation](#uninstallation)

---

## Automated Installation (Recommended)

This is the easiest and recommended way to get started on any supported platform. The script automatically detects your environment and installs the appropriate packages.
This script supports both x86_64 Ubuntu and Raspberry Pi.
On the Raspberry Pi, make sure you first install the HW and SW as described in the [Raspberry Pi Installation](#raspberry-pi-installation) section.


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


<details>
<summary><b>Manual Installation (Advanced)</b></summary>

If you need full control over the process use the following instructions.

The `hailo_installer.sh` script handles the installation of the HailoRT and Tappas Core libraries. The main `install.sh` script in the root directory will run this for you, but you can also run it manually for custom installations.

1. **HailoRT and TAPPAS-CORE Installation:**
```bash
./scripts/hailo_installer.sh
```
This installs the default versions of HailoRT and TAPPAS-CORE.
On the Raspberry Pi, use their apt server.
For additional versions, please visit the [Hailo Developer Zone](https://hailo.ai/developer-zone/).

2.  **Create & activate a virtual environment**
    ```bash
    python3 -m venv your_venv_name --system-site-packages
    source your_venv_name/bin/activate
    ```
We use system-site-packages to inherit python packages from the system.
On the Raspberry Pi, the hailoRT and TAPPAS-CORE python bindings are installed on the system. As part of hailo-all installation.
On the x86_64 Ubuntu, the hailoRT and TAPPAS-CORE python bindings can be installed inside the virtual environment.
Note that also on the x86_64 Ubuntu, the gi library is installed on the system (apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0). You can try installing using pip but it is not recommended.

3.  **Install Hailo Python packages**
    This script will install the HailoRT and TAPPAS-CORE python bindings.
    ```bash
    ./scripts/hailo_python_installation.sh
    ```
4.  **Install repository**
    ```bash
    pip install --upgrade pip
    pip install -e .
    ```
5.  **Run post-install setup**
    This downloads models and configures the environment.
    ```bash
    hailo-post-install
    ```

</details>

---
## Download Resources

The Hailo Apps Infrastructure includes a resource downloader utility that automatically fetches AI models, configuration files, and test videos optimized for your Hailo hardware. You can access this tool through the Python script `hailo_apps/hailo_app_python/core/installation/download_resources.py` or via the command-line tool `hailo-download-resources`.

### Usage

```bash
hailo-download-resources [OPTIONS]
```

### Available Options

- `--all`: Download all available resources across all architectures
- `--group <GROUP>`: Specify which resource group to download (see groups below)
- `--config <PATH>`: Use a custom resources configuration file (defaults to system config)
- `--arch <ARCHITECTURE>`: Force a specific Hailo architecture (hailo8, hailo8l, hailo10h). If not specified, the architecture will be auto-detected

### Resource Groups

- **default**: Core models and videos needed for basic functionality (yolov6n, scdepthv3, sample videos)
- **hailo8**: Models optimized for Hailo-8 (yolov8m, scrfd_10g, arcface_mobilefacenet)
- **hailo8l**: Models optimized for Hailo-8L (yolov8s, scrfd_2.5g, arcface_mobilefacenet_h8l)
- **all**: Complete model collection including all architectures and specialized models
- **retrain**: Additional resources for model retraining examples (custom barcode detection model and test video)

By default, we download models that support real-time frame rates for your device. Note that larger models can also be used, but the frame rate might be lower. If you need more accuracy, you can download a larger model. Additional models can be downloaded from the [Hailo Model Zoo](https://github.com/hailo-ai/hailo_model_zoo).


### Examples

```bash
# Download default resources for your detected hardware
hailo-download-resources

# Download all available resources
hailo-download-resources --all

# Download only Hailo-8L specific resources
hailo-download-resources --group hailo8l

# Force download for specific architecture
hailo-download-resources --arch hailo8 --group hailo8
```

The downloader automatically organizes resources into appropriate directories under the `resources/` folder, with models separated by architecture and videos/configs in dedicated subdirectories.

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
sudo rm -rf venv_hailo_apps/ resources/ hailort.log .env hailo_apps.egg-info
```
To uninstall system packages, use `apt remove`.