# Hailo GStreamer Pipelines: Usage & Development Guide

This guide focuses on **running**, **extending**, and **debugging** the pre‑built Hailo GStreamer pipelines, plus reference for the common helper functions.

---

## 1. Running Pipelines

### 1.1 CLI Commands
After installing the package in editable mode (`pip install -e .`), these commands become available:

| Command               | Description                                  |
|-----------------------|----------------------------------------------|
| `hailo-detect`        | Full-featured detection + tracking           |
| `hailo-simple-detect` | Simple YOLO detection                        |
| `hailo-depth`         | Depth estimation pipeline                    |
| `hailo-pose`          | Pose estimation pipeline                     |
| `hailo-seg`           | Instance segmentation pipeline               |

**Example:**
```bash
hailo-simple-detect --input usb
```
Get pipeline‑specific options:
```bash
hailo-detect --help
```

### 1.2 Direct Python Invocation
Run any pipeline script directly:
```bash
python3 hailo_apps_infra/pipelines/instance_segmentation_pipeline.py \
  --input example.mp4 --show-fps
```
Or using module syntax:
```bash
python3 -m hailo_pipelines.instance_segmentation_pipeline --input /dev/video0
```

---

## 2. Command‑Line Flags

### 2.1 Common Flags
Inherited from `get_default_parser()`:

| Flag                | Description                                                              |
|---------------------|--------------------------------------------------------------------------|
| `--input, -i`       | File path, `usb`, `rpi`, or X11 window ID                                 |
| `--arch`            | `hailo8` or `hailo8l`; auto‑detected if omitted                           |
| `--hef-path`        | Override the HEF model file                                               |
| `--show-fps, -f`    | Overlay FPS & drop‑rate on video                                          |
| `--disable-sync`    | `sync=false` on video sink (minimize latency)                             |
| `--disable-callback`| Skip the `identity` pad probe callback                                     |
| `--use-frame, -u`   | Enable frame queue callback (for OpenCV or custom consumption)            |
| `--dump-dot`        | Dump GStreamer graph to `pipeline.dot` after initialization               |
| `--frame-rate, -r`  | Frame rate of the video source. Default is 30.                            |


### 2.2 Detection‑Specific Flag
- **`--labels-json <PATH>`**: custom JSON mapping of class IDs to labels (only for `hailo-detect`).

**Example:**
```bash
hailo-detect --labels-json /path/to/labels.json
```

---

## 3. Pipeline Building Blocks
Utilities in **[`gstreamer_helper_pipelines.py`](../hailo_apps_infra/gstreamer/hailo_gstreamer/gstreamer_helper_pipelines.py)** for composing custom pipelines:

- **`get_source_type(input_source)`**
  Classifies source as `file`, `usb`, `rpi`, `libcamera`, or `ximage` based on prefix. citeturn1file0

- **`SOURCE_PIPELINE(video_source, video_width, video_height, video_format, name, no_webcam_compression)`**
  Standardizes video input and ensures correct caps and format. citeturn1file0

- **`QUEUE(name, max_size_buffers, max_size_bytes, max_size_time, leaky)`**
  Inserts a GStreamer queue with specified buffering properties. citeturn1file0

- **`INFERENCE_PIPELINE(hef_path, post_process_so, batch_size, config_json, post_function_name, scheduler_timeout_ms, scheduler_priority, vdevice_group_id, multi_process_service, additional_params, name)`**
  Configures `hailonet` inference plus optional `hailofilter` post‑processing. citeturn1file0

- **`INFERENCE_PIPELINE_WRAPPER(inner_pipeline, bypass_max_size_buffers, name)`**
  Wraps detection in `hailocropper` and `hailoaggregator` to preserve original resolution. citeturn1file0

- **`TRACKER_PIPELINE(class_id, kalman_dist_thr, iou_thr, init_iou_thr, keep_new_frames, keep_tracked_frames, keep_lost_frames, keep_past_metadata, qos, name)`**
  Sets up `hailotracker` with Kalman/IoU thresholds. citeturn1file0

- **`OVERLAY_PIPELINE(name)`**, **`DISPLAY_PIPELINE(video_sink, sync, show_fps, name)`**, **`FILE_SINK_PIPELINE(output_file, name, bitrate)`**, **`USER_CALLBACK_PIPELINE(name)`**
  Helpers for overlay, display, file recording, and user callbacks. citeturn1file0

---

---

## 4. Function Reference

### 4.1 [utils.py](../hailo_apps_infra/common/hailo_common/utils.py)
- `run_command(command, error_msg)`: shell exec with exit on error.
- `run_command_with_output(command)`: returns stdout or `None`.
- `create_symlink(source_path, link_path)`: safely makes a directory symlink.
- `load_config(config_path)`: loads YAML config into `dict`.
- `load_environment(env_file, required_vars)`: loads `.env` and warns missing.
- Model/resource helpers:
  - `get_model_name(pipeline_name, hailo_arch)`
  - `get_resource_path(pipeline_name, resource_type, model=None)`
- `detect_hailo_package_version(package_name)`: queries `dpkg`.

### 4.2 [hailo_rpi_common.py](../hailo_apps_infra/common/hailo_common/hailo_rpi_common.py)
- `get_default_parser()`: builds the shared `argparse` with flags.
- `detect_host_arch()`, `detect_hailo_arch()`, `detect_pkg_installed()`
- Resource directory helpers.
- Buffer→NumPy handlers: `handle_rgb`, `handle_nv12`, `handle_yuyv`, `get_numpy_from_buffer`, `get_caps_from_pad`

### 4.3 [get_config_values.py](../hailo_apps_infra/common/hailo_common/get_config_values.py)
- `load_config()`, `get_config_value(key)`, `get_default_config_value(key)`, `validate_config(config)`

### 4.4 [get_usb_camera.py](../hailo_apps_infra/common/hailo_common/get_usb_camera.py)
- `get_usb_video_devices()`: lists USB `/dev/video*` devices via `udevadm`.

---
---

## 5. Developing & Extending
1. **Subclass** `GStreamerApp` (in `gstreamer_app.py`), override `get_pipeline_string()`.
2. **Add parser args** before `super().__init__()` in `__init__`.
3. **Compose** your pipeline with helper functions.
4. **Expose** as CLI in `pyproject.toml` under `[project.scripts]`.
5. **Reinstall**: `pip install -e .`
6. **Run**: your new `hailo-<name>` command.

---

## 6. Debugging & Visualization
- **Graphviz**: use `--dump-dot`, then `dot -Tpng pipeline.dot -o pipeline.png`.  
  *Installation*: On Ubuntu, run `sudo apt install graphviz`. For more details, see the [Graphviz Installation Guide](https://graphviz.org/download/).
- **GST_DEBUG logs**: set `GST_DEBUG=*:<LEVEL>`.
- **FPS**: use `--show-fps`; QoS is auto‑disabled to avoid dropping.
- **Community Help**: For further support, visit the [Hailo Community Forum](https://community.hailo.ai/).



