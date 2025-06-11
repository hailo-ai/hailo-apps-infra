# Pipeline Usage Guide

This guide covers how to run  AI pipelines in the Hailo Apps Infrastructure repository. The repo contains 6 main computer vision applications that can be executed through various methods.

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

### Method 1: CLI Commands (Recommended for End Users)

After installing with `pip install -e .` from the repository root, all pipelines are available as CLI commands:

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
hailo-face-recon
```

**Best for:** Production deployment and end-user applications

### Method 2: Python Module Execution (Recommended for Development)

```bash
# Object Detection
python -m hailo_apps_infra.hailo_apps.hailo_pipelines.detection_pipeline

# Simple Detection
python -m hailo_apps_infra.hailo_apps.hailo_pipelines.detection_pipeline_simple

# Pose Estimation
python -m hailo_apps_infra.hailo_apps.hailo_pipelines.pose_estimation_pipeline

# Instance Segmentation
python -m hailo_apps_infra.hailo_apps.hailo_pipelines.instance_segmentation_pipeline

# Depth Estimation
python -m hailo_apps_infra.hailo_apps.hailo_pipelines.depth_pipeline

# Face Recognition
python -m hailo_apps_infra.hailo_apps.apps.face_recognition.face_recognition
```

**Best for:** Development, testing, and CI/CD pipelines

### Method 3: Direct Script Execution with PYTHONPATH (Quick Debugging)

```bash
# Object Detection
PYTHONPATH=. python hailo_apps_infra/hailo_apps/hailo_pipelines/detection_pipeline.py

# Simple Detection
PYTHONPATH=. python hailo_apps_infra/hailo_apps/hailo_pipelines/detection_pipeline_simple.py

# Pose Estimation
PYTHONPATH=. python hailo_apps_infra/hailo_apps/hailo_pipelines/pose_estimation_pipeline.py

# Instance Segmentation
PYTHONPATH=. python hailo_apps_infra/hailo_apps/hailo_pipelines/instance_segmentation_pipeline.py

# Depth Estimation
PYTHONPATH=. python hailo_apps_infra/hailo_apps/hailo_pipelines/depth_pipeline.py
```

**Best for:** Local debugging and quick script execution

### Method 4: Custom Script Wrapper

Create a wrapper script (e.g., `run_detection.py`):

```python
from hailo_apps_infra.hailo_apps.hailo_pipelines import detection_pipeline

detection_pipeline.main()
```

Then run:
```bash
python run_detection.py
```

**Best for:** Jupyter notebooks, simplified testing, and custom integrations

## What Doesn't Work

These approaches will fail with `ModuleNotFoundError` or broken imports:

```bash
# ❌ Wrong - missing PYTHONPATH
python hailo_apps_infra/hailo_apps/hailo_pipelines/detection_pipeline.py

# ❌ Wrong - old package structure
python -m hailo_apps_infra.pipelines.hailo_pipelines.detection_pipeline
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

## Quick Reference

| Use Case | Best Method | Example |
|----------|-------------|---------|
| **Production/End Users** | CLI Commands | `hailo-detect` |
| **Development/Testing** | Python Module | `python -m hailo_apps_infra.hailo_apps.hailo_pipelines.detection_pipeline` |
| **Quick Debugging** | PYTHONPATH + Direct | `PYTHONPATH=. python hailo_apps_infra/hailo_apps/hailo_pipelines/detection_pipeline.py` |
| **Custom Integration** | Import + Call main() | Custom wrapper scripts |

## Notes

All pipelines follow consistent patterns with proper `main()` function entry points and support common arguments like `--input`, `--arch`, `--hef-path`, plus pipeline-specific options. The framework provides flexibility for different deployment scenarios while maintaining ease of use.