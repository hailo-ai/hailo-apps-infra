# Hailo Runtime x86 Installation Guide

This guide walks you through installing the Hailo Runtime environment on x86-64 systems. If you need versions above 4.20, visit the [Developer Zone](https://hailo.ai/developer-zone/) and search for HailoRT.

## What Gets Installed

When you run the installer, you'll get these components:

- **HailoRT Driver & Runtime** - Core runtime for Hailo AI processors
- **Tappas Core Libraries** - Application framework and utilities  
- **Python Bindings** - Python interfaces for both HailoRT and Tappas Core
- **System Dependencies** - Essential tools like build utilities, FFmpeg, GStreamer, and OpenCV

## System Requirements

### Supported Hardware
- **x86_64 / AMD64** processors (Intel or AMD 64-bit systems)
- **aarch64 / ARM64** architecture (modern ARM servers)

### Raspberry Pi Note
While technically supported, we don't recommend using this installer on Raspberry Pi OS. Instead, use the official Hailo package provided by Raspberry Pi:
[Raspberry Pi AI Documentation](https://www.raspberrypi.com/documentation/computers/ai.html)

### Software Requirements
- **Python**: Versions 3.10 through 3.11
- **Operating System**: Ubuntu or other Debian-based Linux distributions

## Basic Installation

The simplest way to get started is running the installer with default settings:

```bash
./scripts/hailo_installer.sh
```

This installs HailoRT 4.20.0 and Tappas Core 3.31.0 by default.

## Custom Installation Options

### Specify Component Versions

If you need specific versions of the components:

```bash
./scripts/hailo_installer.sh \
  --hailort-version=4.20.0 \
  --tappas-core-version=3.31.0
```

### Choose Virtual Environment Name

To use a custom name for your Python virtual environment:

```bash
./scripts/hailo_installer.sh --venv-name=my_hailo_env
```

### Combine Multiple Options

You can mix and match installation options:

```bash
./scripts/hailo_installer.sh \
  --hailort-version=4.20.0 \
  --tappas-core-version=3.31.0 \
  --venv-name=hailo_dev
```

## Installation Process

The installer performs these steps automatically:

### System Checks
- Detects your CPU architecture to ensure compatibility
- Verifies Python version is between 3.8 and 3.11
- Checks for Raspberry Pi-specific requirements if applicable
- Warns about potentially unsupported kernel versions

### Installation Steps
- Installs system packages including `build-essential` and development tools
- Sets up the HailoRT PCIe driver for hardware communication
- Installs HailoRT and Tappas Core libraries
- Creates a Python virtual environment with all necessary bindings

## Raspberry Pi Considerations

If you're on a Raspberry Pi system, the installer looks for the `hailo-all` package. If it's not found, you should follow the official Raspberry Pi AI documentation instead of using this installer:
[Raspberry Pi AI Setup Guide](https://www.raspberrypi.com/documentation/computers/ai.html)

## Post-Installation Setup

### Activate Your Environment

After installation completes, activate your Python virtual environment:

```bash
# Using the default environment name
source hailo_venv/bin/activate
```

If you used a custom environment name, replace `hailo_venv` with your chosen name.

### Verify Installation

Check that Hailo packages were installed correctly:

```bash
apt list | grep hailo
```

This shows all installed Hailo-related packages on your system.

## Troubleshooting Common Issues

### Download Problems
The installer includes automatic retry logic for download failures. If downloads keep failing, check your internet connection and firewall settings.

### Permission Errors
If system package installation fails, you may need to run with elevated privileges:

```bash
sudo ./scripts/hailo_installer.sh
```

### Architecture Not Supported
Double-check that you're running on a supported x86-64 or ARM64 system. The installer will detect and report unsupported architectures.

### Python Version Issues
Make sure you have Python 3.10 or 3.11 installed before running the installer. You can check your version with:

```bash
python3 --version
```

## Getting Newer Versions

For versions above 4.20 or access to beta releases and advanced features, visit the Hailo Developer Zone:

- **Main Developer Portal**: [Hailo Developer Zone](https://hailo.ai/developer-zone/)
- **Software Downloads**: [Download Section](https://hailo.ai/developer-zone/software-downloads/)