# Hailo-Gstreamer Framework
================

## What is Hailo-Tappas-Core?
Hailo-Tappas-Core is a GStreamer-based library of plugins that enables using Hailo devices within GStreamer pipelines to create intelligent video processing applications with Python.

## What is GStreamer?

GStreamer is a framework for creating streaming media applications. It provides a plugin-based architecture where plugins can be linked and arranged in a pipeline that defines the data flow. The GStreamer framework simplifies writing applications that handle audio, video, or any kind of data stream.

For additional details check [GStreamer overview](terminology.rst#gstreamer-framework)

## Hailo-Tappas-Core Python Integration

Our Python framework builds on top of Hailo-Tappas-Core GStreamer plugins, providing an easy-to-use interface for creating AI-powered video processing applications. The framework handles pipeline creation, management, and provides callback mechanisms for custom processing.

### Key Features

- **Simple Pipeline Construction**: Use pre-built pipeline components for common tasks
- **Flexible Video Sources**: Support for files, USB cameras, MIPI cameras, and Raspberry Pi cameras
- **AI Inference Integration**: Seamless integration with Hailo neural network inference
- **Custom Callbacks**: Easy integration of custom processing logic
- **Real-time Performance**: Optimized for low-latency video processing

## Core GStreamer Elements

The Hailo-Tappas-Core framework provides the following specialized GStreamer elements:

### AI/ML Processing Elements
* **[HailoNet](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_net.rst)** - Element for sending and receiving data from Hailo-8 chip
* **[HailoFilter](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_filter.rst)** - Element for applying postprocessing operations to frames and tensors
* **[HailoPython](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_python.rst)** - Element for applying postprocessing operations via Python

### Multi-Device & Routing Elements
* **[HailoMuxer](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_muxer.rst)** - Muxer element for Multi-Hailo-8 setups
* **[HailoRoundRobin](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_roundrobin.rst)** - Provides muxing functionality in round-robin method
* **[HailoStreamRouter](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_stream_router.rst)** - Provides de-muxing functionality

### Cascading Networks Elements
* **[HailoAggregator](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_aggregator.rst)** - Designed for cascading networks with 2 sink pads and 1 source
* **[HailoCropper](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_cropper.rst)** - Designed for cascading networks with 1 sink and 2 sources

### Tiling Elements
* **[HailoTileAggregator](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_tile_aggregator.rst)** - Designed for tiled applications with 2 sink pads and 1 source
* **[HailoTileCropper](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_tile_cropper.rst)** - Designed for tiled applications with 1 sink and 2 sources

### Tracking & Monitoring Elements
* **[HailoTracker](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_tracker.rst)** - Applies Joint Detection and Embedding (JDE) with Kalman filtering for object tracking
* **[HailoDeviceStats](https://github.com/hailo-ai/tappas/tree/master/docs/elements/hailo_device_stats.rst)** - Samples power and temperature from Hailo devices

## Python Framework Architecture

### Core Components

#### 1. GStreamerApp Base Class
The main application class that handles:
- Pipeline creation and management
- Signal handling and cleanup
- Frame rate control
- Error handling and recovery

#### 2. Pipeline Builder Functions
Pre-built pipeline components for common tasks:
- `SOURCE_PIPELINE()` - Video source handling (files, cameras, streams)
- `INFERENCE_PIPELINE()` - AI inference with Hailo devices
- `DISPLAY_PIPELINE()` - Video display with overlay support
- `USER_CALLBACK_PIPELINE()` - Custom processing integration

#### 3. Callback System
Easy integration of custom processing logic:
```python
class app_callback_class:
    def __init__(self):
        self.frame_count = 0
        self.frame_queue = multiprocessing.Queue(maxsize=3)
    
    def increment(self):
        self.frame_count += 1
```

### Example Usage

```python
from your_framework import GStreamerApp, app_callback_class

# Create callback handler
user_data = app_callback_class()

# Create application
app = GStreamerApp(args, user_data)

# Run the pipeline
app.run()
```

### Pipeline Construction

The framework provides helper functions to build complex pipelines easily:

```python
def get_pipeline_string(self):
    source_pipeline = SOURCE_PIPELINE(
        video_source=self.video_source,
        video_width=self.video_width,
        video_height=self.video_height,
        frame_rate=self.frame_rate
    )
    
    inference_pipeline = INFERENCE_PIPELINE(
        hef_path=self.hef_path,
        post_process_so=self.post_process_so
    )
    
    display_pipeline = DISPLAY_PIPELINE(
        sync=self.sync,
        show_fps=str(self.show_fps).lower()
    )
    
    return f"{source_pipeline} ! {inference_pipeline} ! {display_pipeline}"
```

## Supported Platforms

- Linux-based systems with GStreamer 1.0+
- Raspberry Pi with camera support
- x86/ARM platforms with USB camera support
- Integration with various video formats and codecs