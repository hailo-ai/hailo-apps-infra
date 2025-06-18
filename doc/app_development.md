# Hailo AI Pipeline Development Guide

A comprehensive guide for building and configuring GStreamer-based AI pipelines with Hailo hardware acceleration.

## Overview

This guide walks you through creating AI inference pipelines using Hailo's Accelerator. You'll learn how to set up models, configure GStreamer pipelines, and build applications that can process video streams with real-time AI inference.

## Prerequisites

- Hailo hardware (Hailo-8 or Hailo-8L or Hailo-10H)
- Python 3.10 or 3.11 with GStreamer bindings
- Access to Hailo Model Zoo or compiled `.hef` models or use defaults

## Step 1: Prepare Your Model and Post-Processing

### Get Your Model Ready

You have two options for obtaining a model:

**Option A: Use Hailo Model Zoo**
- Browse the [Hailo Model Zoo](https://github.com/hailo-ai/hailo_model_zoo) for pre-compiled models
- Download the `.hef` file for your chosen model

**Option B: Compile Your Own Model**
- Use Hailo's Dataflow Compiler (DFC) to convert your ONNX/TensorFlow model


### Set Up Post-Processing

Most applications use standard post-processing methods:

- **NMS (Non-Maximum Suppression)**: For object detection models
- **HailoRT post-processing**: Built-in processing functions

If you need custom post-processing:
1. Write your C/C++ post-processing function
2. Compile it into a shared object (`.so`) library
3. Ensure the exported function name matches your pipeline configuration

## Step 2: Configure Pipeline Parameters

Set up your application parameters by defining these key attributes:

```python
class MyPipelineApp(GStreamerApp):
    def __init__(self, parser=None):
        # Model configuration
        self.hef_path = "/path/to/your_model.hef"           # Path to your HEF model
        self.post_process_so = "/path/to/postproc.so"       # Post-processing library
        self.post_function_name = "postproc_func"           # Function name in library
        
        # Pipeline settings  
        self.batch_size = 1                                 # Inference batch size
        self.video_width = 640                              # Input/output width
        self.video_height = 640                             # Input/output height
        self.frame_rate = 30                                # Target FPS
        
        # Performance tuning
        self.sync = False                                   # Disable for low latency
        self.show_fps = True                                # Show FPS overlay
```

## Step 3: Build Your GStreamer Pipeline

Use the helper functions from `gstreamer_helper_pipelines.py` to construct your pipeline:

### 3.1 Source Stage
Captures video input from camera or file:

```python
source = SOURCE_PIPELINE(
    video_source=self.video_source,
    video_width=self.video_width,
    video_height=self.video_height,
    frame_rate=self.frame_rate,
    sync=self.sync
)
```

### 3.2 Inference Stage
Runs AI inference on the Hailo NPU:

```python
infer = INFERENCE_PIPELINE(
    hef_path=self.hef_path,
    post_process_so=self.post_process_so,
    post_function_name=self.post_function_name,
    batch_size=self.batch_size
)
```

### 3.3 Optional: Resolution Preservation
Maintains original video resolution through inference:

```python
infer_wrapped = INFERENCE_PIPELINE_WRAPPER(infer)
```

### 3.4 Optional: Object Tracking
Adds tracking capabilities for detected objects:

```python
tracker = TRACKER_PIPELINE(class_id=0)  # Track objects of class 0
```

### 3.5 User Callback
Allows custom processing of inference results:

```python
callback = USER_CALLBACK_PIPELINE()
```

### 3.6 Display Stage
Outputs processed video with overlays:

```python
display = DISPLAY_PIPELINE(
    video_sink=self.video_sink,
    sync=self.sync,
    show_fps=self.show_fps
)
```

### 3.7 Combine Pipeline Stages

```python
def get_pipeline_string(self):
    # Build individual stages
    source = SOURCE_PIPELINE(...)
    infer = INFERENCE_PIPELINE(...)
    infer_wrapped = INFERENCE_PIPELINE_WRAPPER(infer)
    tracker = TRACKER_PIPELINE(class_id=0)
    callback = USER_CALLBACK_PIPELINE()
    display = DISPLAY_PIPELINE(...)
    
    # Connect stages with GStreamer linking
    pipeline_str = (
        f"{source} ! "
        f"{infer_wrapped} ! "
        f"{tracker} ! "
        f"{callback} ! "
        f"{display}"
    )
    
    return pipeline_str
```

## Step 4: Complete Application Implementation

Here's a complete example application:

```python
from gstreamer_app import GStreamerApp
from gstreamer_helper_pipelines import *
from hailo_common import get_default_parser

class MyHailoApp(GStreamerApp):
    def __init__(self, parser=None):
        # Initialize with command line parser
        parser = parser or get_default_parser()
        super().__init__(parser, user_data=None)
        
        # Configure your model and pipeline
        self.setup_model_config()
        self.setup_pipeline_config()
        
        # Build and start the pipeline
        self.create_pipeline()
    
    def setup_model_config(self):
        """Configure model-specific parameters"""
        self.hef_path = "/path/to/yolov5s.hef"
        self.post_process_so = "/path/to/libyolo_post.so"
        self.post_function_name = "yolov5_postprocess"
        self.batch_size = 1
    
    def setup_pipeline_config(self):
        """Configure pipeline parameters"""
        self.video_width = 640
        self.video_height = 640
        self.frame_rate = 30
        self.sync = False          # Better performance
        self.show_fps = True       # Monitor performance
    
    def get_pipeline_string(self):
        """Build the complete GStreamer pipeline"""
        source = SOURCE_PIPELINE(
            video_source=self.video_source,
            video_width=self.video_width,
            video_height=self.video_height,
            frame_rate=self.frame_rate,
            sync=self.sync
        )
        
        infer = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size
        )
        
        # Wrap inference to preserve resolution
        infer_wrapped = INFERENCE_PIPELINE_WRAPPER(infer)
        
        # Add object tracking
        tracker = TRACKER_PIPELINE(class_id=0)
        
        # Add user callback for custom processing
        callback = USER_CALLBACK_PIPELINE()
        
        # Set up display output
        display = DISPLAY_PIPELINE(
            video_sink=self.video_sink,
            sync=self.sync,
            show_fps=self.show_fps
        )
        
        return f"{source} ! {infer_wrapped} ! {tracker} ! {callback} ! {display}"

if __name__ == "__main__":
    app = MyHailoApp()
    app.run()
```

## Step 5: Running and Debugging

### Basic Usage

Run your application with various input sources:

```bash
# Use webcam
python my_hailo_app.py --video-source /dev/video0 --show-fps

# Use video file  
python my_hailo_app.py --video-source /path/to/video.mp4 --show-fps

# Use RTSP stream
python my_hailo_app.py --video-source rtsp://camera-ip/stream --show-fps
```

### Debugging Options

Enable debugging features to troubleshoot issues:

```bash
# Export pipeline graph for visualization
python my_hailo_app.py --dump-dot

# Disable synchronization for lower latency
python my_hailo_app.py --disable-sync

# Test with different frame rates
python my_hailo_app.py --frame-rate 15

# Combine multiple debug options
python my_hailo_app.py --video-source /dev/video0 --dump-dot --show-fps --disable-sync
```

### Performance Tuning

If you encounter performance issues:

1. **Frame Drops**: Adjust queue sizes in `gstreamer_helper_pipelines.py`
   ```python
   QUEUE(name="inference_queue", max_size_buffers=3, max_size_bytes=0, max_size_time=0)
   ```

2. **High Latency**: 
   - Set `sync=False`
   - Reduce queue buffer sizes
   - Lower frame rate temporarily

3. **Memory Issues**:
   - Reduce batch size
   - Check for memory leaks in custom post-processing

## Common Issues and Solutions

### Post-Processing Issues
- Verify shared object library path and permissions
- Ensure function name matches exactly (case-sensitive)
- Check that the post-processing function signature is correct

### Pipeline Errors
- Use `--dump-dot` to visualize the pipeline structure
- Check GStreamer logs for detailed error messages

## Next Steps

- Explore the [Hailo Model Zoo](https://github.com/hailo-ai/hailo_model_zoo) for more models
- Learn about custom post-processing development
- Optimize your pipeline for specific use cases
- Integrate with your application's business logic

## Resources

- [Hailo Developer Zone](https://hailo.ai/developer-zone/)
- [GStreamer Documentation](https://gstreamer.freedesktop.org/documentation/)
- [Hailo Community Forum](https://community.hailo.ai/)

---

#### Happy building! 🚀