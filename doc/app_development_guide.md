# Hailo Apps - Advanced App Development Guide

Welcome to the advanced guide for developing applications with Hailo! This guide is designed for developers who have already set up their virtual environment with the `hailo-apps-infra` repository and have successfully tested a basic pipeline. If you've made it this far, you're ready to dive into the more sophisticated aspects of Hailo app development.

## Building User Interfaces with Gradio

When you want to create interactive applications similar to the face recognition demo, Gradio is your best friend. It's currently the most effective Python library for building real-time video interfaces that work seamlessly with Hailo's processing capabilities.

To get started with UI development, I recommend studying these key files as your reference:
- `hailo_apps_infra/hailo_apps/apps/face_recognition/face_ui_callbacks.py`
- `hailo_apps_infra/hailo_apps/apps/face_recognition/face_recognition.py`

These files demonstrate the best practices for wiring UI callbacks and visual components together. Think of them as your blueprint for creating engaging user experiences.

## Understanding Pipeline Architecture

The pipeline system is the backbone of Hailo applications. If you're just getting started, take a look at the default `read` pipeline in this repository. For more complex implementations, the [TAPPAS repository](https://github.com/hailo-ai/tappas/tree/master/apps/h8/gstreamer/general) contains extensive examples that showcase advanced pipeline configurations.

Let me walk you through the essential pipeline components you'll be working with:

**Source Management**: The `get_source_type(input_source)` function is your starting point. It intelligently identifies what type of input you're working with, supporting everything from files and USB cameras to Raspberry Pi cameras, libcamera, and even X11 image sources.

**Video Normalization**: The `SOURCE_PIPELINE(...)` component takes care of normalizing your video input, handling caps configuration and format standardization so you don't have to worry about compatibility issues.

**Queue Management**: `QUEUE(...)` adds GStreamer queues with proper memory and time constraints, ensuring smooth data flow through your pipeline.

**AI Inference**: This is where the magic happens. `INFERENCE_PIPELINE(...)` applies the `hailonet` inference along with optional `hailofilter` post-processing. For cases where you need to preserve the original video resolution, `INFERENCE_PIPELINE_WRAPPER(...)` wraps the inference process intelligently.

**Object Tracking**: When you need to track objects across frames, `TRACKER_PIPELINE(...)` initializes the `hailotracker` with Kalman filtering and IoU (Intersection over Union) parameters.

**Output and Visualization**: Finally, you have several options for output:
- `OVERLAY_PIPELINE(...)` for adding visual overlays
- `DISPLAY_PIPELINE(...)` for screen output
- `FILE_SINK_PIPELINE(...)` for saving results
- `USER_CALLBACK_PIPELINE(...)` for custom processing

## Integrating Custom Parsers

When you need to add custom parsing functionality, you have two straightforward options. You can either include your parser directly in your pipeline's configuration, or add it to the core system by modifying `hailo_core/hailo_common/core.py`. Choose the approach that best fits your application's architecture.

## Resource Management Made Simple

One of the most powerful features of the Hailo system is its centralized resource management. This system gives you seamless access to all the critical resources your application needs: models, video samples, and configuration files.

![Resources and Core Directory Structure](../local_resources/project_hierarchy.png)

![Resource Path Logic](../local_resources/resources_path.png)

![Resource Management Overview](../local_resources/resource_management_system.png)

The beauty of this system is that it handles all the complexity of resource location and management behind the scenes, so you can focus on building your application logic.

## Automatic Platform Detection

The system is smart enough to detect your platform and architecture automatically, configuring itself appropriately for optimal performance:

![Platform Support](../local_resources/platform_support_arch.png)

This means your applications will work seamlessly across different hardware configurations without requiring manual adjustments.

## System Architecture Deep Dive

![System Architecture](../local_resources/system_arch.png)

The foundation of the Hailo system rests on four major modules that work together to provide a robust development environment:

### System Constants and Definitions

The `defines.py` file serves as the central hub for all global constants and paths. Here's what you'll find organized there:

**Architecture Definitions**: Constants like `HAILO8_ARCH` and `HAILO8L_ARCH` define the different Hailo chip variants you might be working with.

**Platform Identification**: `X86_POSSIBLE_NAME` and `ARM_POSSIBLE_NAME` help the system identify what platform it's running on.

**Package Dependencies**: `HAILO_TAPPAS` and `HAILO_TAPPAS_CORE` define the system dependencies your application relies on.

**File Extensions**: `HAILO_FILE_EXTENSION` and `JSON_FILE_EXTENSION` standardize file type handling across the system.

### Dynamic Path Resolution

The system uses dynamic path root resolution through `Path(__file__).resolve().parents[3]`, which means it can figure out where it's running from and adjust accordingly.

### Pre-configured Pipeline Templates

The system comes with several pre-configured pipeline templates that cover the most common use cases:

**Object Detection**: Uses models like `yolov8m` and `yolov8s` with the `libyolo_hailortpp_postprocess.so` post-processing library.

**Pose Estimation**: Leverages `yolov8m_pose` and `yolov8s_pose` models with `libyolov8pose_postprocess.so` for human pose detection.

**Image Segmentation**: Employs `yolov5m_seg` and `yolov5n_seg` models with `libyolov5seg_postprocess.so` for pixel-level classification.

**Depth Estimation**: Uses the `scdepthv3` model with `libdepth_postprocess.so` for depth map generation.

**Face Recognition**: Combines `scrfd_10g` and `scrfd_2.5g` models with `libscrfd.so` for facial detection and recognition.

## Environment Detection and System Introspection

The `installation_utils.py` module provides comprehensive system introspection capabilities that make deployment across different environments seamless.

**Host Architecture Detection**: The system uses `platform.machine()` to determine whether it's running on x86, ARM, Raspberry Pi, or other architectures, returning appropriate identifiers for each.

![Host Architecture Detection Flow](../local_resources/host_arch_detection_flow.png)

**Hailo Device Detection**: The system can automatically detect which Hailo chip is connected by parsing command-line interface output to determine the chip version.

**Package Detection**: Using a combination of `pkg-config`, `dpkg`, and `pip` based checks, the system verifies that all necessary dependencies are properly installed.

**TAPPAS Detection**: The system intelligently determines whether `HAILO_TAPPAS` or `HAILO_TAPPAS_CORE` is installed and locates the associated post-processing directories.

![TAPPAS Variant Detection Flow](../local_resources/tappas_variant_detection_flow.png)

## Core Application Utilities

The `core.py` module provides essential utilities that every Hailo application needs.

### Environment Management

The `load_environment()` function handles all the complexity of environment setup. It loads your `.env` file using `python-dotenv`, validates that you have the necessary access permissions, and ensures all required variables are properly configured.

### Smart Resource Path Resolution

One of the most useful features is the `get_resource_path(pipeline_name, resource_type, model)` function. This intelligent function:
- Derives the base path from `RESOURCES_ROOT_PATH_DEFAULT`
- Detects the architecture automatically when needed
- Resolves paths for `.so` files, videos, photos, JSON configs, models, and face recognition data

![Resource Path Resolution Flow](../local_resources/resource_path_resolution_flow.png)

### Model Name Resolution

The system includes smart model name resolution through `get_model_name(pipeline_name, arch)`. This function uses a mapping system that automatically selects the appropriate model based on your pipeline type and hardware architecture:

```python
pipeline_map = {
    DETECTION_PIPELINE: DETECTION_MODEL_NAME_H8 if arch==HAILO8_ARCH else DETECTION_MODEL_NAME_H8L,
    # ... other mappings
}
```

### Command Line Argument Parsing

The system provides a standardized argument parser through `get_default_parser()` that handles common command-line options:

- `--input` or `-i`: Specifies the source input (defaults vary by application)
- `--arch`: Allows you to override the Hailo architecture detection
- `--hef-path`: Lets you specify a custom model path
- `--use-frame` or `-u`: Enables frame callback functionality
- `--show-fps` or `-f`: Shows FPS display for performance monitoring
- `--disable-sync`: Disables synchronization when needed

## Environment Setup and Configuration

The `set_env.py` module handles the complex task of environment setup through the `set_environment_vars(config)` function.

### Detection and Configuration Flow

The system follows a comprehensive detection flow:

1. **System Detection**: Identifies `host_arch`, `hailo_arch`, `hailort_version`, and `tappas_variant`
2. **Environment Building**: Creates a comprehensive `env_vars` dictionary with all necessary settings
3. **Environment Application**: Updates `os.environ` with the new settings
4. **Persistence**: Saves the configuration using `_persist_env_vars(env_vars, env_path)`

![Environment Detection Flow](../local_resources/set_env_flow.png)

### Environment Persistence Strategy

The system takes care of environment persistence with a robust approach:
- Ensures the `.env` file is writable by setting appropriate permissions (`chmod 666`)
- Overwrites the file atomically to prevent corruption during updates
- Skips unset variables to maintain configuration integrity

### YAML Configuration Support

For more complex configurations, the system supports YAML files:
- Loads configuration from `config.yaml` through `load_and_validate_config()`
- Supports command-line override of configuration paths
- Provides comprehensive logging of the configuration process with fallback behavior for error recovery

## Integration with Your Applications

This foundation layer is designed to power all your application-level components by providing:

**Resource Resolution**: Through the `get_resource_path()` function, your applications can easily locate and access any resources they need.

**Runtime Adaptation**: Automatic architecture detection ensures your applications adapt to different hardware configurations seamlessly.

**Unified Environment**: The combination of `.env` files and `os.environ` management provides a consistent environment across all your applications.

**Installation Support**: Built-in support for automated setup and updates makes deployment and maintenance straightforward.

## Getting Started with Your Own Applications

Now that you understand the architecture and capabilities of the Hailo system, you're ready to start building your own advanced applications. Remember to leverage the existing pipeline templates as starting points, use the resource management system for easy access to models and data, and take advantage of the automatic platform detection to ensure your applications work across different environments.

The key to successful Hailo application development is understanding how these foundation components work together to provide a powerful, flexible platform for AI-powered video processing applications.

## Understanding the Applications Framework

Now that we've covered the foundation, let's dive into the applications framework itself. The framework follows a clean, layered architecture where your applications inherit from a base class and compose pipelines using predefined building blocks. This approach gives you the power of customization while maintaining consistency and reliability across all applications.

![App Framework Flow](../local_resources/app_framework_flow.png)

### The GStreamerApp Foundation

At the heart of the framework lies the `GStreamerApp` class, which serves as the foundation for all video processing applications. Think of it as your reliable partner that handles all the complex GStreamer initialization, pipeline lifecycle management, and provides a clean, standardized interface for building your applications.

#### Application Initialization Made Simple

When you create a new application, the constructor takes care of all the heavy lifting. It handles environment setup, parses command-line arguments, and configures pipeline parameters automatically. Here's what you get out of the box:

- **Video Source Management**: The system automatically detects and configures your input source, whether it's a file, camera, or other device
- **Resolution Configuration**: Default video dimensions of 1280x720, but fully customizable for your needs
- **Format Handling**: RGB format by default, with support for other formats as needed
- **AI Processing Setup**: Batch size configuration for inference (defaults to 1 for real-time processing)
- **Latency Control**: Pipeline latency set to 300 milliseconds for optimal real-time performance

#### Robust Pipeline Lifecycle Management

The framework provides comprehensive pipeline state management that you don't have to worry about. Methods like `create_pipeline()`, `run()`, and `shutdown()` handle all the complexity of GStreamer pipeline management. The `bus_call()` method automatically handles GStreamer messages including end-of-stream events, errors, and quality-of-service warnings.

#### Flexible Callback Integration

One of the most powerful features is the callback system. Your applications can register custom processing functions that get called at specific points in the pipeline. The framework automatically connects pad probes to elements named `identity_callback` in your pipeline string, making integration seamless.

You can find the complete implementation in `hailo_apps_infra/hailo_apps/hailo_gstreamer/gstreamer_app.py` (lines 109-384).

## Pipeline Building Blocks - Your Construction Kit

The framework provides a comprehensive set of functions for constructing GStreamer pipelines. These building blocks are like LEGO pieces that you can compose together to create complete video processing applications.

![Pipeline Building Block Functions](../local_resources/pipeline_building_blocks.png)

### Core Pipeline Functions

Let me walk you through the essential building blocks you'll be working with:

#### SOURCE_PIPELINE() - Your Input Gateway

This function creates video input pipelines that support multiple source types seamlessly:

- **File Sources**: Works with MP4, AVI, and other video file formats
- **USB Cameras**: Integrates with V4L2 devices and automatically detects the best format
- **Raspberry Pi Camera**: Direct integration with picamera2 for Pi-based applications
- **Screen Capture**: X11 window capture for desktop applications

The function is smart enough to automatically detect your source type using `get_source_type()` and configures the appropriate GStreamer elements with proper scaling, format conversion, and frame rate control.

#### INFERENCE_PIPELINE() - Where AI Happens

This is where the magic of AI inference occurs. The function constructs inference pipelines that integrate seamlessly with Hailo hardware acceleration. Key parameters you'll work with include:

- **HEF Path**: Points to your compiled Hailo Executable Format file
- **Post-processing Library**: Path to your C++ post-processing shared library
- **Batch Size**: Controls inference batch size for performance optimization
- **Configuration**: JSON configuration file for post-processing parameters
- **Device Group**: Hailo device group identifier for multi-device setups

#### INFERENCE_PIPELINE_WRAPPER() - Resolution Intelligence

This clever function provides resolution preservation by wrapping inference pipelines with `hailocropper` and `hailoaggregator` elements. This means your AI inference can run at different resolutions while maintaining the original frame dimensions for downstream processing - perfect for applications that need both performance and visual quality.

### Pipeline Composition Pattern

Building your application pipeline is as simple as calling these functions and connecting them together:

```python
def get_pipeline_string(self):
    source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
    inference_pipeline = INFERENCE_PIPELINE(self.hef_path, self.post_process_so)
    display_pipeline = DISPLAY_PIPELINE()
    
    return f"{source_pipeline} ! {inference_pipeline} ! {display_pipeline}"
```

The complete implementation can be found in `hailo_apps_infra/hailo_apps/hailo_gstreamer/gstreamer_helper_pipelines.py` (lines 6-476).

## The Callback System - Your Custom Processing Gateway

The framework provides a flexible callback system that lets you access video frames, AI inference results, and metadata at specific points in your pipeline. This is where you can implement your custom logic and data extraction.

![Callback System Components](../local_resources/callback_system.png)

### Understanding the app_callback_class

The `app_callback_class` provides a standard interface for callback functionality with several powerful features:

- **Frame Counting**: Tracks processed frames through `increment()` and `get_count()` methods
- **Frame Buffering**: Thread-safe frame queue with `set_frame()` and `get_frame()` methods
- **Multiprocessing Support**: Queue implementation that works across process boundaries
- **Lifecycle Management**: A `running` flag for clean shutdown procedures

### Seamless Pipeline Integration

Callbacks integrate with GStreamer pipelines through pad probes on identity elements. Here's how it works: you simply include an identity element named `identity_callback` in your pipeline string, and the framework automatically:

1. Locates the `identity_callback` element in your pipeline
2. Attaches a pad probe to the source pad
3. Calls your registered callback function for each buffer that passes through
4. Provides easy access to buffer data via `get_numpy_from_buffer()`

### Buffer Utilities Integration

The callback system works seamlessly with buffer conversion utilities to give you easy access to video data in numpy format. The `get_numpy_from_buffer()` function supports multiple video formats:

- **RGB**: Converts to (height, width, 3) numpy array through `handle_rgb()`
- **NV12**: Provides Y plane and UV plane arrays through `handle_nv12()`
- **YUYV**: Creates (height, width, 2) numpy array through `handle_yuyv()`

You can find the implementation details in `hailo_apps_infra/hailo_apps/hailo_gstreamer/gstreamer_app.py` (lines 69-91, 324-332, 469-476) and `hailo_apps_infra/hailo_core/hailo_common/buffer_utils.py` (lines 45-101).

## C++ Post-Processing Integration - Performance Optimization

The framework seamlessly integrates with optimized C++ post-processing libraries through GStreamer's `hailofilter` element. These libraries provide hardware-accelerated post-processing for various AI tasks, giving you maximum performance where it matters most.

![C++ Post-processing Library Integration](../local_resources/cpp_pp_library.png)

### Library Integration Pattern

C++ post-processing libraries integrate through the `INFERENCE_PIPELINE()` function's parameters in a clean, straightforward way:

```python
INFERENCE_PIPELINE(
    hef_path="model.hef",
    post_process_so="/usr/local/hailo/resources/so/yolo_hailortpp_postprocess.so",
    config_json="labels.json", 
    post_function_name="yolo_hailortpp_postprocess"
)
```

The framework automatically constructs the appropriate `hailofilter` element configuration and integrates it into your GStreamer pipeline.

### Available Post-processing Libraries

The framework comes with several pre-built post-processing libraries ready for use:

- **Object Detection**: `yolo_hailortpp_postprocess.so` with `yolo_hailortpp_postprocess` function
- **Pose Estimation**: `yolov8pose_postprocess.so` with `yolov8pose_postprocess` function for keypoint processing
- **Instance Segmentation**: `yolov5seg_postprocess.so` with `yolov5seg_postprocess` function for mask processing
- **Depth Estimation**: `depth_postprocess.so` with `depth_postprocess` function
- **Face Detection**: `scrfd.so` with `scrfd` function
- **Face Recognition**: `face_recognition_post.so` with `face_recognition_post` function for feature extraction

All libraries install automatically to `/usr/local/hailo/resources/so/` and integrate seamlessly with the framework's pipeline building functions.

The implementation details are available in `hailo_apps_infra/hailo_cpp_postprocess/cpp/meson.build` (lines 6-135) and `hailo_apps_infra/hailo_apps/hailo_gstreamer/gstreamer_helper_pipelines.py` (lines 134-210).

## Application Development Pattern - Building Your Apps

Applications built on this framework follow a consistent inheritance and composition pattern that makes development both powerful and straightforward. The framework provides all the infrastructure, so you can focus on your domain-specific pipeline construction and processing logic.

![Application Development Structure](../local_resources/app_dev_structure.png)

### The Development Pattern

Here's how you'll typically structure your applications:

1. **Inheritance**: Your applications inherit from `GStreamerApp` to gain all the pipeline management capabilities
2. **Pipeline Definition**: Override `get_pipeline_string()` to define your application-specific GStreamer pipeline
3. **Callback Registration**: Implement custom callback functions and register them with the framework
4. **Resource Configuration**: Configure model paths, post-processing libraries, and other resources
5. **Execution**: Use the inherited `run()` method to execute your complete application

### Example Application Structure

Here's what a typical application looks like in practice:

```python
class DetectionApp(GStreamerApp):
    def __init__(self, args, user_data):
        super().__init__(args, user_data)
        self.hef_path = "yolov8m.hef"
        self.post_process_so = "yolo_hailortpp_postprocess.so"
        self.app_callback = detection_callback
    
    def get_pipeline_string(self):
        source = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
        inference = INFERENCE_PIPELINE(self.hef_path, self.post_process_so)
        display = DISPLAY_PIPELINE()
        callback = USER_CALLBACK_PIPELINE()
        
        return f"{source} ! {inference} ! {callback} ! {display}"
```

This pattern enables rapid development of specialized AI applications while maintaining consistency and reliability across the entire framework. You get all the power and flexibility you need, with the confidence that comes from a well-tested, robust foundation.

## Putting It All Together

The Hailo applications framework is designed to make advanced AI video processing accessible and efficient. By understanding how the foundation layer provides resource management and system detection, how the application framework handles pipeline management and callbacks, and how the building blocks compose together, you have everything you need to build sophisticated AI applications.