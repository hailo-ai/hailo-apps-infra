# System Configuration

The Hailo Applications infrastructure uses a YAML configuration file to manage global settings for installation, model management, and hardware detection. While the default settings are suitable for most users, this file provides fine-grained control.

The configuration is typically managed by the installation scripts, but can be manually edited if needed.

## Configuration Options

Here is a breakdown of what each option in the configuration file controls.

```yaml
# HailoRT version configuration
hailort_version: "auto"  # Options: "auto", "latest", or a specific version like "4.15.0"

# TAPPAS framework version
tappas_version: "auto"   # TAPPAS model version. "auto" is recommended for automatic detection.

# Model zoo version for downloading models
model_zoo_version: "v2.14.0"  # The specific version of the Hailo Model Zoo to use.

# Hardware architecture detection
host_arch: "auto"        # The host system architecture. Options: "rpi", "x86", "arm", or "auto".
hailo_arch: "auto"       # The Hailo device architecture. Options: "hailo8", "hailo8l", "hailo10h", or "auto".

# File paths and directories
resources_path: "resources"              # The directory where downloaded models and resources are stored.
virtual_env_name: "hailo_infra_venv"     # The default name for the Python virtual environment.
storage_dir: "hailo_temp_resources"      # A temporary directory for downloads.

# Server configuration
server_url: "http://dev-public.hailo.ai/2025_01"  # The server from which to download models.

# TAPPAS configuration
tappas_variant: "auto"           # The TAPPAS variant to use. Options: "tappas", "tappas-core", or "auto".
tappas_postproc_path: "auto"     # The path to the post-processing libraries. "auto" will use the default path.
```

## Configuration Tips

*   **Use "auto" where possible**: For `hailort_version`, `tappas_version`, `host_arch`, and `hailo_arch`, the `"auto"` setting allows the system to detect the correct configuration for your hardware and software setup. This is the safest and most reliable option.
*   **Modifying `resources_path`**: Only change this if you have a specific need to store the AI models and other resources in a non-default location.
*   **Do Not Change `server_url`**: This URL points to the official Hailo model server. Do not change it unless explicitly instructed to by Hailo support.