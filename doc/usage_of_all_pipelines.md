# Pipeline Usage Guide

This guide covers how to run  AI pipelines in the Hailo Apps Infrastructure repository.

These pipelines are meant to be used as a building block for youre final project, For more info [development guide](app_development.md)


## Available Pipelines

The repository provides the following AI applications:

| CLI Command | Pipeline Type | Purpose |
|-------------|---------------|---------|
| `hailo-detect` | Object Detection | Standard object detection with tracking |
| `hailo-simple-detect` | Simple Detection | Simplified detection without tracking |
| `hailo-pose` | Pose Estimation | Human pose keypoint detection |
| `hailo-seg` | Instance Segmentation | Pixel-level object segmentation |
| `hailo-depth` | Depth Estimation | Monocular depth estimation |
| `hailo-face-recon` | Face Recognition | Face detection and recognition |

## Running Pipelines

### Method 1: CLI Commands 


```bash
# Object Detection
hailo-detect

# Simple Detection (no tracking)
hailo-simple-detect

# Pose Estimation
hailo-pose

# Instance Segmentation
hailo-seg

# Depth Estimation
hailo-depth

# Face Recognition
hailo-face-recon # beta version
```

### Method 2: Direct Script Execution 
```bash
# Object Detection
python hailo_apps_infra/hailo_apps/hailo_pipelines/detection_pipeline.py

# Simple Detection
python hailo_apps_infra/hailo_apps/hailo_pipelines/detection_pipeline_simple.py

# Pose Estimation
python hailo_apps_infra/hailo_apps/hailo_pipelines/pose_estimation_pipeline.py

# Instance Segmentation
python hailo_apps_infra/hailo_apps/hailo_pipelines/instance_segmentation_pipeline.py

# Depth Estimation
python hailo_apps_infra/hailo_apps/hailo_pipelines/depth_pipeline.py
```

## Pipeline Features

### Object Detection Pipeline
- **Features:** Tracking, configurable NMS thresholds, custom labels
- **Models:** YOLOv8m (Hailo-8), YOLOv8s (Hailo-8L)

### Simple Detection Pipeline
- **Features:** No tracking, simplified pipeline, custom labels
- **Models:** YOLOv6n

### Pose Estimation Pipeline
- **Features:** Human pose keypoints, higher resolution (1280x720), person tracking
- **Models:** YOLOv8m_pose (Hailo-8), YOLOv8s_pose (Hailo-8L)

### Instance Segmentation Pipeline
- **Features:** Pixel-level segmentation, automatic config selection
- **Models:** YOLOv5m_seg (Hailo-8), YOLOv5n_seg (Hailo-8L)

### Depth Estimation Pipeline
- **Features:** Monocular depth estimation, simplified pipeline
- **Models:** SCDepthv3


## Configuration Options



| Flag(s)              | Description                                                                                                                                                                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--input`, `-i`      | Input source. Can be a file, USB (webcam), RPi camera (CSI module), or XImage. For RPi camera use `-i rpi`. For automatic USB detection use `-i usb`. For specific USB device use `-i /dev/video<X>`. Defaults to application-specific source. |
| `--use-frame`, `-u`  | Use the video frame directly from the callback function instead of the default sink behavior.                                                                                                                                                  |
| `--show-fps`, `-f`   | Print the current FPS on the display sink.                                                                                                                                                                                                     |
| `--arch`             | Hailo architecture to target. Choices: `hailo8`, `hailo8l`, `hailo10h`. If unset, the app will auto-detect.                                                                                                                                    |
| `--hef-path`         | Path to a compiled HEF file to load for inference.                                                                                                                                                                                             |
| `--disable-sync`     | Disable display sink synchronization; runs as fast as possible (useful for file sources).                                                                                                                                                      |
| `--disable-callback` | Disable the user-defined callback in the pipeline; runs without custom post-processing logic.                                                                                                                                                  |
| `--dump-dot`         | Dump the pipeline graph to `pipeline.dot` for visualization.                                                                                                                                                                                   |
| `--frame-rate`, `-r` | Frame rate of the video source in frames per second (default: 30).                                                                                                                                                                             |

## Pipeline-Specific CLI Options & General Flow

### 1. Detection (`detection_pipeline.py`)

| Flag            | Description                                                            |
| --------------- | ---------------------------------------------------------------------- |
| `--so-path`     | Path to the shared object file (`.so`) used for post-processing.       |
| `--pp-function` | Name of the function inside the post-processing shared object to call. |
| `--labels-json` | Path to a custom labels JSON file for detection/classification.        |

### 2. Simple Detection (`detection_pipeline_simple.py`)

| Flag            | Description                                                     |
| --------------- | --------------------------------------------------------------- |
| `--so-path`     | Path to the shared object file for detection post-processing.   |
| `--pp-function` | Name of the function inside the `.so` to invoke.                |
| `--labels-json` | Path to a custom labels JSON file for detection/classification. |


## Basic Pipeline Flow

Below is a high-level overview of how frames move through a Hailo GStreamer pipeline:

```mermaid
flowchart LR
    Source  --> Inference
    Inference --> Tracker
    Tracker --> Callback
    Callback --> Display
```

1. **Source**: Captures or reads video frames (file, USB, RPi camera, etc.).
2. **Inference**: Runs the Hailo HEF model and applies post-processing logic.
3. **Tracker** *(optional)*: Associates detections across consecutive frames.
4. **Callback**: Executes any user-defined Python callback for custom per-frame processing.
5. **Display**: Renders the final output, including overlays, FPS, and other visuals.

---


