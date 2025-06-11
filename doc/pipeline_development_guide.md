# Pipeline Development Guide

This guide provides developers with everything needed to build AI-powered video processing applications using our GStreamer-based pipeline framework. The framework simplifies the complexity of GStreamer while providing powerful tools for real-time computer vision applications.

For comprehensive examples and additional resources, check out the [TAPPAS repository](https://github.com/hailo-ai/tappas/tree/master).

## Framework Overview

The pipeline framework is built around the `GStreamerApp` class, which manages GStreamer pipelines and provides a standardized approach to building AI applications. Instead of manually crafting complex GStreamer pipelines, developers can use our pre-built components that handle video input, AI inference, post-processing, and output display.

![Framework Architecture](../local_resources/framework_pipeline_blocks.png)

## Core Components

### GStreamerApp Class

The `GStreamerApp` class serves as the foundation for all pipeline applications. It handles:

- **Pipeline Management**: Creates and manages GStreamer pipelines with proper state transitions
- **Event Handling**: Manages GStreamer events like End-of-Stream, errors, and QoS messages
- **Callback Integration**: Connects user-defined functions for custom processing
- **Signal Handling**: Provides graceful shutdown on SIGINT (Ctrl-C)
- **Frame Processing**: Supports frame extraction using multiprocessing queues

#### Key Methods

- `create_pipeline()` - Initializes GStreamer and constructs the pipeline
- `get_pipeline_string()` - Override this method to define your custom pipeline
- `run()` - Starts the GLib event loop and manages execution
- `shutdown()` - Handles graceful cleanup and termination

### App Callback Class

The callback system allows you to inject custom processing logic at any point in the pipeline. Inherit from `app_callback_class` to implement your own data processing and state management.

## Pipeline Building Blocks

Our framework provides modular components that can be combined to create complete AI processing pipelines. Each component returns a GStreamer pipeline string that can be chained together.

![Pipeline Components](../local_resources/core_pipeline_components.png)

### Essential Components

#### SOURCE_PIPELINE()
Handles various video input types:
- USB cameras via `v4l2src`
- Video files with automatic decoding
- Raspberry Pi camera via `appsrc`
- Screen capture

Automatically configures format, resolution, and frame rate based on the source type.

#### INFERENCE_PIPELINE()
Manages AI inference using Hailo hardware:
- Loads HEF (Hailo Executable Format) models
- Integrates C++ post-processing libraries
- Configurable batch sizes and device groups
- Supports custom JSON configurations

```python
inference_pipeline = INFERENCE_PIPELINE(
    hef_path="model.hef",
    post_process_so="postprocess.so",
    batch_size=2,
    config_json="config.json"
)
```

#### INFERENCE_PIPELINE_WRAPPER()
Preserves original video resolution while enabling inference on different input sizes using `hailocropper` and `hailoaggregator` elements. This is essential when you need to maintain the original video quality while running inference at different resolutions.

#### DISPLAY_PIPELINE()
Handles video output with visualization:
- Renders bounding boxes and labels via `hailooverlay`
- Optional FPS overlay
- Configurable video sinks

### Advanced Components

#### CROPPER_PIPELINE()
Enables cascading detection by cropping detected objects and sending them to additional inference stages. Perfect for scenarios like face detection followed by face recognition.

#### TRACKER_PIPELINE()
Adds object tracking capabilities to maintain object identities across frames.

#### USER_CALLBACK_PIPELINE()
Integrates custom processing functions at any point in the pipeline for specialized operations.

#### FILE_SINK_PIPELINE()
Records processed video output to `.mkv` files for later analysis.

### Utility Functions

#### QUEUE()
Creates buffered connection points between pipeline elements. Queues are essential for:
- Managing data flow between elements
- Enabling multithreading (each queue creates a new thread)
- Controlling buffer sizes and leak behavior

## Pipeline Composition Patterns

![Pipeline Architecture](../local_resources/pipeline_component_arch.png)

### Basic AI Pipeline
```
SOURCE_PIPELINE → INFERENCE_PIPELINE → DISPLAY_PIPELINE
```

### Resolution Preservation Pattern
```
SOURCE_PIPELINE → INFERENCE_PIPELINE_WRAPPER(INFERENCE_PIPELINE) → DISPLAY_PIPELINE
```

### Multi-Stage Processing
```
SOURCE_PIPELINE → INFERENCE_PIPELINE → CROPPER_PIPELINE(INFERENCE_PIPELINE) → DISPLAY_PIPELINE
```

## Buffer Processing and Data Flow

The framework includes utilities for converting between GStreamer buffers and NumPy arrays, enabling custom processing of video frames.

![Buffer Utilities](../local_resources/buffer_utils_arch.png)

## Building Your First Pipeline

Here's a simple example of creating a custom pipeline:

```python
from hailo_apps_infra.gstreamer_app import GStreamerApp
from hailo_apps_infra.gstreamer_helper_pipelines import *

class MyCustomApp(GStreamerApp):
    def __init__(self, args):
        super().__init__(args)
        
    def get_pipeline_string(self):
        source = SOURCE_PIPELINE(video_source=self.video_source)
        inference = INFERENCE_PIPELINE(
            hef_path="my_model.hef",
            post_process_so="my_postprocess.so"
        )
        display = DISPLAY_PIPELINE()
        
        return f"{source} ! {inference} ! {display}"

# Usage
if __name__ == "__main__":
    from hailo_apps_infra.app_callback_class import app_callback_class
    
    app = MyCustomApp(get_default_parser().parse_args())
    app.run()
```

## Computer Vision Applications

The framework includes several ready-to-use computer vision applications:

### Object Detection
- Real-time YOLO-based object detection
- Configurable NMS thresholds
- Custom label support
- Optional tracking capabilities

### Pose Estimation
- Human pose detection with keypoint estimation
- Optimized for 1280x720 resolution
- Person-specific tracking

### Instance Segmentation
- Pixel-level object detection and segmentation
- Support for Hailo-8 and Hailo-8L models
- Automatic configuration based on model type

### Depth Estimation
- Monocular depth estimation
- 3D scene understanding capabilities
- Streamlined implementation

![Common Implementation](../local_resources/common_implementation_pattern.png)

## Development Best Practices

### Resource Management
- Use `get_resource_path()` for locating models and libraries
- Implement automatic architecture detection with `detect_hailo_arch()`
- Support both automatic and manual resource specification

### Error Handling
- Implement proper GStreamer event handling
- Use graceful shutdown procedures
- Provide meaningful error messages

### Performance Optimization
- Use queues strategically for multithreading
- Configure appropriate batch sizes
- Monitor QoS messages for performance tuning

## Getting Started

1. **Study the Examples**: Start with `pose_estimation_pipeline.py` as a reference implementation
2. **Use Helper Functions**: Leverage the pipeline helper functions instead of manual GStreamer syntax
3. **Test Incrementally**: Build your pipeline step by step, testing each component
4. **Monitor Performance**: Use the built-in FPS overlay and QoS monitoring

For more comprehensive examples and detailed documentation, visit the [TAPPAS repository](https://github.com/hailo-ai/tappas/tree/master).

## Command Line Usage

All pipeline applications support common command-line arguments:
- `--input`: Specify video source (camera, file, or screen)
- `--arch`: Manually specify Hailo architecture
- `--labels-json`: Custom label configuration
- `--help`: View all available options

Run any example with the `--help` flag to see all available options for that specific application.