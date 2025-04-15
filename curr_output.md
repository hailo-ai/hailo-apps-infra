# Directory Content: hailo_apps_infra/

## Directory Structure

```
hailo_apps_infra/
├── __pycache__
│   └── __init__.cpython-311.pyc
├── common
│   ├── __pycache__
│   │   ├── __init__.cpython-311.pyc
│   │   ├── get_usb_camera.cpython-311.pyc
│   │   ├── hailo_rpi_common.cpython-311.pyc
│   │   └── test_utils.cpython-311-pytest-8.3.5.pyc
│   ├── __init__.py
│   ├── get_usb_camera.py
│   ├── hailo_rpi_common.py
│   └── test_utils.py
├── config
│   ├── config.yaml
│   └── resources_config.yaml
├── core
│   ├── __pycache__
│   │   ├── __init__.cpython-311.pyc
│   │   ├── depth_pipeline.cpython-311.pyc
│   │   ├── detection_pipeline.cpython-311.pyc
│   │   ├── detection_pipeline_simple.cpython-311.pyc
│   │   ├── instance_segmentation_pipeline.cpython-311.pyc
│   │   └── pose_estimation_pipeline.cpython-311.pyc
│   ├── __init__.py
│   ├── depth_pipeline.py
│   ├── detection_pipeline.py
│   ├── detection_pipeline_simple.py
│   ├── instance_segmentation_pipeline.py
│   └── pose_estimation_pipeline.py
├── gstreamer
│   ├── __pycache__
│   │   ├── __init__.cpython-311.pyc
│   │   ├── gstreamer_app.cpython-311.pyc
│   │   └── gstreamer_helper_pipelines.cpython-311.pyc
│   ├── __init__.py
│   ├── gstreamer_app.py
│   └── gstreamer_helper_pipelines.py
├── installation
│   ├── __pycache__
│   │   ├── __init__.cpython-311.pyc
│   │   ├── compile_cpp.cpython-311.pyc
│   │   ├── download_resources.cpython-311.pyc
│   │   ├── install.cpython-311.pyc
│   │   ├── post_install.cpython-311.pyc
│   │   ├── set_env.cpython-311.pyc
│   │   └── validate_config.cpython-311.pyc
│   ├── __init__.py
│   ├── compile_cpp.py
│   ├── download_resources.py
│   ├── install.py
│   ├── post_install.py
│   ├── set_env.py
│   └── validate_config.py
├── .env
├── __init__.py
├── classes_MyProject.png
└── packages_MyProject.png
```

## File Contents

### .env

```
DEVICE_ARCH=rpi
HAILO_ARCH=hailo8
RESOURCE_PATH=/usr/local/hailo/resources
TAPPAS_POST_PROC_DIR=/usr/local/hailo/resources/postproc/tappas-core
```

### __init__.py

```

```

### core/__init__.py

```

```

### core/depth_pipeline.py

```
import gi
gi.require_version('Gst', '1.0')
import os
import setproctitle
from hailo_apps_infra.gstreamer.gstreamer_app import app_callback_class, dummy_callback, GStreamerApp
from hailo_apps_infra.gstreamer.gstreamer_helper_pipelines import DISPLAY_PIPELINE, INFERENCE_PIPELINE, INFERENCE_PIPELINE_WRAPPER, SOURCE_PIPELINE, USER_CALLBACK_PIPELINE
from hailo_apps_infra.common.hailo_rpi_common import detect_hailo_arch, get_default_parser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# User Gstreamer Application: This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDepthApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        
        if parser == None:
            parser = get_default_parser()

        super().__init__(parser, user_data)  # Call the parent class constructor

        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError('Could not auto-detect Hailo architecture. Please specify --arch manually.')
            self.arch = detected_arch
        else:
            self.arch = self.options_menu.arch

        self.app_callback = app_callback
        setproctitle.setproctitle("Hailo Depth App")  # Set the process title

        # Set the HEF file path (based on the arch), depth post processing method name & post-processing shared object file path
        if self.arch == "hailo8":
            self.depth_hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8" / "scdepthv3.hef")
        else:  # hailo8l
            self.depth_hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8l" /"scdepthv3_h8l.hef")

        self.depth_post_function_name = "filter_scdepth"
        self.depth_post_process_so = str(PROJECT_ROOT / "resources" / "so" / "libdepth_postprocess.so")

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
        depth_pipeline = INFERENCE_PIPELINE(
            hef_path=self.depth_hef_path,
            post_process_so=self.depth_post_process_so,
            post_function_name=self.depth_post_function_name,
            name='depth_inference')
        depth_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(depth_pipeline, name='inference_wrapper_depth')
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps)
    
        return (
            f'{source_pipeline} ! '
            f'{depth_pipeline_wrapper} ! '
            f'{user_callback_pipeline} ! '
            f'{display_pipeline}'
        )

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDepthApp(app_callback, user_data)
    app.run()
```

### core/detection_pipeline.py

```
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo
from pathlib import Path

from hailo_apps_infra.common.hailo_rpi_common import (
    get_default_parser,
    detect_hailo_arch,
)
from hailo_apps_infra.gstreamer.gstreamer_helper_pipelines import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
)
from hailo_apps_infra.gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]



# -----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------

# This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDetectionApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        if parser == None:
            parser = get_default_parser()
        parser.add_argument(
            "--labels-json",
            default=None,
            help="Path to costume labels JSON file",
        )
        # Call the parent class constructor
        super().__init__(parser, user_data)
        # Additional initialization code can be added here
        # Set Hailo parameters these parameters should be set based on the model used
        self.batch_size = 2
        nms_score_threshold = 0.3
        nms_iou_threshold = 0.45


        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch


        if self.options_menu.hef_path is not None:
            self.hef_path = self.options_menu.hef_path
        # Set the HEF file path based on the arch
        elif self.arch == "hailo8":
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8" / "yolov8m.hef")
        else:  # hailo8l
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8l" / "yolov8s_h8l.hef")

        # Set the post-processing shared object file
        self.post_process_so = str(PROJECT_ROOT / "resources" / "so" / "libyolo_hailortpp_postprocess.so")
        self.post_function_name = "filter_letterbox"
        # User-defined label JSON file
        self.labels_json = self.options_menu.labels_json

        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Set the process title
        setproctitle.setproctitle("Hailo Detection App")

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
        detection_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.labels_json,
            additional_params=self.thresholds_str)
        detection_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(detection_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps)

        pipeline_string = (
            f'{source_pipeline} ! '
            f'{detection_pipeline_wrapper} ! '
            f'{tracker_pipeline} ! '
            f'{user_callback_pipeline} ! '
            f'{display_pipeline}'
        )
        print(pipeline_string)
        return pipeline_string

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
```

### core/detection_pipeline_simple.py

```
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo
from pathlib import Path

from hailo_apps_infra.common.hailo_rpi_common import (
    get_default_parser,
    detect_hailo_arch,
)
from hailo_apps_infra.gstreamer.gstreamer_helper_pipelines import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
)
from hailo_apps_infra.gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# -----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------

# This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDetectionApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        if parser == None:
            parser = get_default_parser()
        parser.add_argument(
            "--labels-json",
            default=None,
            help="Path to costume labels JSON file",
        )

        # Call the parent class constructor
        super().__init__(parser, user_data)

        # Additional initialization code can be added here
        self.video_width = 640
        self.video_height = 640
        
        # Set Hailo parameters - these parameters should be set based on the model used
        self.batch_size = 2
        nms_score_threshold = 0.3
        nms_iou_threshold = 0.45
        if self.options_menu.input is None:  # Setting up a new application-specific default video (overrides the default video set in the GStreamerApp constructor)
            self.video_source = str(PROJECT_ROOT / "resources" / "example_640.mp4")
        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch

        if self.options_menu.hef_path is not None:
            self.hef_path = self.options_menu.hef_path
        # Set the HEF file path based on the arch
        elif self.arch == "hailo8":
            self.hef_path = str(PROJECT_ROOT / "resources"/ "models" / "hailo8" / "yolov6n.hef")
        else:  # hailo8l
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8l" / "yolov6n_h8l.hef")

        # Set the post-processing shared object file
        self.post_process_so = str(PROJECT_ROOT / "resources" / "so" / "libyolo_hailortpp_postprocess.so")
        self.post_function_name = "filter"

        # User-defined label JSON file
        self.labels_json = self.options_menu.labels_json

        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Set the process title
        setproctitle.setproctitle("Hailo Detection Simple App")

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height, no_webcam_compression=True)
        detection_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.labels_json,
            additional_params=self.thresholds_str)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps)

        pipeline_string = (
            f'{source_pipeline} ! '
            f'{detection_pipeline} ! '
            f'{user_callback_pipeline} ! '
            f'{display_pipeline}'
        )
        print(pipeline_string)
        return pipeline_string

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
```

### core/instance_segmentation_pipeline.py

```
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo
from hailo_apps_infra.common.hailo_rpi_common import (
    get_default_parser,
    detect_hailo_arch,
)
from hailo_apps_infra.gstreamer.gstreamer_helper_pipelines import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    USER_CALLBACK_PIPELINE,
    TRACKER_PIPELINE,
    DISPLAY_PIPELINE,
)
from hailo_apps_infra.gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback
)

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

#-----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------

# This class inherits from the hailo_rpi_common.GStreamerApp class

class GStreamerInstanceSegmentationApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        if parser == None:
            parser = get_default_parser()
        # Call the parent class constructor
        super().__init__(parser, user_data)
        # Additional initialization code can be added here
        # Set Hailo parameters these parameters should be set based on the model used
        self.batch_size = 2
        self.video_width = 640
        self.video_height = 640

        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch

        # Set the HEF file path based on the architecture
        if self.options_menu.hef_path:
            self.hef_path = self.options_menu.hef_path
        elif self.arch == "hailo8":
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8" / "yolov5m_seg.hef")
        else:  # hailo8l
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8l" / "yolov5n_seg_h8l.hef")

        # Determine config file based on selected HEF
        if 'yolov5m_seg' in self.hef_path:
            self.config_file = str(PROJECT_ROOT / "resources" / "yolov5m_seg.json")
        elif 'yolov5n_seg' in self.hef_path:
            self.config_file = str(PROJECT_ROOT / "resources" / "yolov5n_seg.json")
        else:
            raise ValueError("HEF version not supported, you will need to provide a config file")

        # Set post-process .so path
        self.default_post_process_so = str(PROJECT_ROOT / "resources" / "so" / "libyolov5seg_postprocess.so")
        self.post_function_name = "filter_letterbox"
        self.app_callback = app_callback

        # Set the process title
        setproctitle.setproctitle("Hailo Instance Segmentation App")

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(video_source=self.video_source, video_width=self.video_width, video_height=self.video_height)
        infer_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.default_post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.config_file,
        )
        infer_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(infer_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps)
        pipeline_string = (
            f'{source_pipeline} ! '
            f'{infer_pipeline_wrapper} ! '
            f'{tracker_pipeline} ! '
            f'{user_callback_pipeline} ! '
            f'{display_pipeline}'
        )
        print(pipeline_string)
        return pipeline_string

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app = GStreamerInstanceSegmentationApp(dummy_callback, user_data)
    app.run()
```

### core/pose_estimation_pipeline.py

```
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo
from hailo_apps_infra.common.hailo_rpi_common import (
    get_default_parser,
    detect_hailo_arch,
)
from hailo_apps_infra.gstreamer.gstreamer_helper_pipelines import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
)
from hailo_apps_infra.gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback
)
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
#-----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------

# This class inherits from the hailo_rpi_common.GStreamerApp class

class GStreamerPoseEstimationApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        if parser == None:
            parser = get_default_parser()
        # Call the parent class constructor
        super().__init__(parser, user_data)
        # Additional initialization code can be added here
        # Set Hailo parameters these parameters should be set based on the model used
        self.batch_size = 2
        self.video_width = 1280
        self.video_height = 720


        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch



        # Set the HEF file path based on the architecture
        if self.options_menu.hef_path:
            self.hef_path = self.options_menu.hef_path
        elif self.arch == "hailo8":
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8" / "yolov8m_pose.hef")
        else:  # hailo8l
            self.hef_path = str(PROJECT_ROOT / "resources" / "models" / "hailo8l" / "yolov8s_pose_h8l.hef")

        self.app_callback = app_callback

        # Set the post-processing shared object file
        self.post_process_so = str(PROJECT_ROOT / "resources" / "so" / "libyolov8pose_postprocess.so")
        self.post_process_function = "filter_letterbox"

        # Set the process title
        setproctitle.setproctitle("Hailo Pose Estimation App")

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(video_source=self.video_source, video_width=self.video_width, video_height=self.video_height)
        infer_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_process_function,
            batch_size=self.batch_size
        )
        infer_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(infer_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=0)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()

        display_pipeline = DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps)
        pipeline_string = (
            f'{source_pipeline} !'
            f'{infer_pipeline_wrapper} ! '
            f'{tracker_pipeline} ! '
            f'{user_callback_pipeline} ! '
            f'{display_pipeline}'
        )
        print(pipeline_string)
        return pipeline_string

if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app = GStreamerPoseEstimationApp(dummy_callback, user_data)
    app.run()
```

### gstreamer/__init__.py

```

```

### gstreamer/gstreamer_app.py

```
import multiprocessing
import setproctitle
import signal
import os
import gi
import threading
import sys
import cv2
import numpy as np
import time
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject
from hailo_apps_infra.gstreamer.gstreamer_helper_pipelines import get_source_type
from hailo_apps_infra.common.get_usb_camera import get_usb_video_devices
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
try:
    from picamera2 import Picamera2
except ImportError:
    pass # Available only on Pi OS

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# A sample class to be used in the callback function
# This example allows to:
# 1. Count the number of frames
# 2. Setup a multiprocessing queue to pass the frame to the main thread
# Additional variables and functions can be added to this class as needed
class app_callback_class:
    def __init__(self):
        self.frame_count = 0
        self.use_frame = False
        self.frame_queue = multiprocessing.Queue(maxsize=3)
        self.running = True

    def increment(self):
        self.frame_count += 1

    def get_count(self):
        return self.frame_count

    def set_frame(self, frame):
        if not self.frame_queue.full():
            self.frame_queue.put(frame)

    def get_frame(self):
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        else:
            return None

def dummy_callback(pad, info, user_data):
    """
    A minimal dummy callback function that returns immediately.

    Args:
        pad: The GStreamer pad
        info: The probe info
        user_data: User-defined data passed to the callback

    Returns:
        Gst.PadProbeReturn.OK
    """
    return Gst.PadProbeReturn.OK

# -----------------------------------------------------------------------------------------------
# GStreamerApp class
# -----------------------------------------------------------------------------------------------
class GStreamerApp:
    def __init__(self, args, user_data: app_callback_class):
        # Set the process title
        setproctitle.setproctitle("Hailo Python App")

        # Create options menu
        self.options_menu = args.parse_args()

        # Set up signal handler for SIGINT (Ctrl-C)
        signal.signal(signal.SIGINT, self.shutdown)

        # Initialize variables
        tappas_post_process_dir = os.environ.get('TAPPAS_POST_PROC_DIR', '')
        if tappas_post_process_dir == '':
            print("TAPPAS_POST_PROC_DIR environment variable is not set. Please set it to by sourcing setup_env.sh")
            exit(1)
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.postprocess_dir = tappas_post_process_dir
        self.video_source = self.options_menu.input
        if self.video_source is None:
            self.video_source = str(PROJECT_ROOT / "resources" / "videos" / "example.mp4")
        if self.video_source == 'usb':
            self.video_source = get_usb_video_devices()
            if not self.video_source:
                print('Provided argument "--input" is set to "usb", however no available USB cameras found. Please connect a camera or specifiy different input method.')
                exit(1)
            else:
                self.video_source = self.video_source[0]
        self.source_type = get_source_type(self.video_source)
        self.user_data = user_data
        self.video_sink = "autovideosink"
        self.pipeline = None
        self.loop = None
        self.threads = []
        self.error_occurred = False
        self.pipeline_latency = 300  # milliseconds

        # Set Hailo parameters; these parameters should be set based on the model used
        self.batch_size = 1
        self.video_width = 1280
        self.video_height = 720
        self.video_format = "RGB"
        self.hef_path = None
        self.app_callback = None

        # Set user data parameters
        user_data.use_frame = self.options_menu.use_frame

        self.sync = "false" if (self.options_menu.disable_sync or self.source_type != "file") else "true"
        self.show_fps = self.options_menu.show_fps

        if self.options_menu.dump_dot:
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = os.getcwd()

    def on_fps_measurement(self, sink, fps, droprate, avgfps):
        print(f"FPS: {fps:.2f}, Droprate: {droprate:.2f}, Avg FPS: {avgfps:.2f}")
        return True

    def create_pipeline(self):
        # Initialize GStreamer
        Gst.init(None)

        pipeline_string = self.get_pipeline_string()
        try:
            self.pipeline = Gst.parse_launch(pipeline_string)
        except Exception as e:
            print(f"Error creating pipeline: {e}", file=sys.stderr)
            sys.exit(1)

        # Connect to hailo_display fps-measurements
        if self.show_fps:
            print("Showing FPS")
            self.pipeline.get_by_name("hailo_display").connect("fps-measurements", self.on_fps_measurement)

        # Create a GLib Main Loop
        self.loop = GLib.MainLoop()

    def bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            self.on_eos()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}", file=sys.stderr)
            self.error_occurred = True
            self.shutdown()
        # QOS
        elif t == Gst.MessageType.QOS:
            # Handle QoS message here
            qos_element = message.src.get_name()
            print(f"QoS message received from {qos_element}")
        return True


    def on_eos(self):
        if self.source_type == "file":
             # Seek to the start (position 0) in nanoseconds
            success = self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, 0)
            if success:
                print("Video rewound successfully. Restarting playback...")
            else:
                print("Error rewinding the video.", file=sys.stderr)
        else:
            self.shutdown()


    def shutdown(self, signum=None, frame=None):
        print("Shutting down... Hit Ctrl-C again to force quit.")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.pipeline.set_state(Gst.State.PAUSED)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.READY)
        GLib.usleep(100000)  # 0.1 second delay

        self.pipeline.set_state(Gst.State.NULL)
        GLib.idle_add(self.loop.quit)


    def get_pipeline_string(self):
        # This is a placeholder function that should be overridden by the child class
        return ""

    def dump_dot_file(self):
        print("Dumping dot file...")
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
        return False

    def run(self):
        # Add a watch for messages on the pipeline's bus
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)


        # Connect pad probe to the identity element
        if not self.options_menu.disable_callback:
            identity = self.pipeline.get_by_name("identity_callback")
            if identity is None:
                print("Warning: identity_callback element not found, add <identity name=identity_callback> in your pipeline where you want the callback to be called.")
            else:
                identity_pad = identity.get_static_pad("src")
                identity_pad.add_probe(Gst.PadProbeType.BUFFER, self.app_callback, self.user_data)

        hailo_display = self.pipeline.get_by_name("hailo_display")
        if hailo_display is None:
            print("Warning: hailo_display element not found, add <fpsdisplaysink name=hailo_display> to your pipeline to support fps display.")

        # Disable QoS to prevent frame drops
        disable_qos(self.pipeline)

        # Start a subprocess to run the display_user_data_frame function
        if self.options_menu.use_frame:
            display_process = multiprocessing.Process(target=display_user_data_frame, args=(self.user_data,))
            display_process.start()

        if self.source_type == "rpi":
            picam_thread = threading.Thread(target=picamera_thread, args=(self.pipeline, self.video_width, self.video_height, self.video_format))
            self.threads.append(picam_thread)
            picam_thread.start()

        # Set the pipeline to PAUSED to ensure elements are initialized
        self.pipeline.set_state(Gst.State.PAUSED)

        # Set pipeline latency
        new_latency = self.pipeline_latency * Gst.MSECOND  # Convert milliseconds to nanoseconds
        self.pipeline.set_latency(new_latency)

        # Set pipeline to PLAYING state
        self.pipeline.set_state(Gst.State.PLAYING)

        # Dump dot file
        if self.options_menu.dump_dot:
            GLib.timeout_add_seconds(3, self.dump_dot_file)

        # Run the GLib event loop
        self.loop.run()

        # Clean up
        try:
            self.user_data.running = False
            self.pipeline.set_state(Gst.State.NULL)
            if self.options_menu.use_frame:
                display_process.terminate()
                display_process.join()
            for t in self.threads:
                t.join()
        except Exception as e:
            print(f"Error during cleanup: {e}", file=sys.stderr)
        finally:
            if self.error_occurred:
                print("Exiting with error...", file=sys.stderr)
                sys.exit(1)
            else:
                print("Exiting...")
                sys.exit(0)

def picamera_thread(pipeline, video_width, video_height, video_format, picamera_config=None):
    appsrc = pipeline.get_by_name("app_source")
    appsrc.set_property("is-live", True)
    appsrc.set_property("format", Gst.Format.TIME)
    print("appsrc properties: ", appsrc)
    # Initialize Picamera2
    with Picamera2() as picam2:
        if picamera_config is None:
            # Default configuration
            main = {'size': (1280, 720), 'format': 'RGB888'}
            lores = {'size': (video_width, video_height), 'format': 'RGB888'}
            controls = {'FrameRate': 30}
            config = picam2.create_preview_configuration(main=main, lores=lores, controls=controls)
        else:
            config = picamera_config
        # Configure the camera with the created configuration
        picam2.configure(config)
        # Update GStreamer caps based on 'lores' stream
        lores_stream = config['lores']
        format_str = 'RGB' if lores_stream['format'] == 'RGB888' else video_format
        width, height = lores_stream['size']
        print(f"Picamera2 configuration: width={width}, height={height}, format={format_str}")
        appsrc.set_property(
            "caps",
            Gst.Caps.from_string(
                f"video/x-raw, format={format_str}, width={width}, height={height}, "
                f"framerate=30/1, pixel-aspect-ratio=1/1"
            )
        )
        picam2.start()
        frame_count = 0
        start_time = time.time()
        print("picamera_process started")
        while True:
            frame_data = picam2.capture_array('lores')
            # frame_data = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            if frame_data is None:
                print("Failed to capture frame.")
                break
            # Convert framontigue data if necessary
            frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            frame = np.asarray(frame)
            # Create Gst.Buffer by wrapping the frame data
            buffer = Gst.Buffer.new_wrapped(frame.tobytes())
            # Set buffer PTS and duration
            buffer_duration = Gst.util_uint64_scale_int(1, Gst.SECOND, 30)
            buffer.pts = frame_count * buffer_duration
            buffer.duration = buffer_duration
            # Push the buffer to appsrc
            ret = appsrc.emit('push-buffer', buffer)
            if ret != Gst.FlowReturn.OK:
                print("Failed to push buffer:", ret)
                break
            frame_count += 1

def disable_qos(pipeline):
    """
    Iterate through all elements in the given GStreamer pipeline and set the qos property to False
    where applicable.
    When the 'qos' property is set to True, the element will measure the time it takes to process each buffer and will drop frames if latency is too high.
    We are running on long pipelines, so we want to disable this feature to avoid dropping frames.
    :param pipeline: A GStreamer pipeline object
    """
    # Ensure the pipeline is a Gst.Pipeline instance
    if not isinstance(pipeline, Gst.Pipeline):
        print("The provided object is not a GStreamer Pipeline")
        return

    # Iterate through all elements in the pipeline
    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result != Gst.IteratorResult.OK:
            break

        # Check if the element has the 'qos' property
        if 'qos' in GObject.list_properties(element):
            # Set the 'qos' property to False
            element.set_property('qos', False)
            print(f"Set qos to False for {element.get_name()}")

# This function is used to display the user data frame
def display_user_data_frame(user_data: app_callback_class):
    while user_data.running:
        frame = user_data.get_frame()
        if frame is not None:
            cv2.imshow("User Frame", frame)
        cv2.waitKey(1)
    cv2.destroyAllWindows()
```

### gstreamer/gstreamer_helper_pipelines.py

```
import os

def get_source_type(input_source):
    # This function will return the source type based on the input source
    # return values can be "file", "mipi" or "usb"
    if input_source.startswith("/dev/video"):
        return 'usb'
    elif input_source.startswith("rpi"):
        return 'rpi'
    elif input_source.startswith("libcamera"): # Use libcamerasrc element, not suggested
        return 'libcamera'
    elif input_source.startswith('0x'):
        return 'ximage'
    else:
        return 'file'

def QUEUE(name, max_size_buffers=3, max_size_bytes=0, max_size_time=0, leaky='no'):
    """
    Creates a GStreamer queue element string with the specified parameters.

    Args:
        name (str): The name of the queue element.
        max_size_buffers (int, optional): The maximum number of buffers that the queue can hold. Defaults to 3.
        max_size_bytes (int, optional): The maximum size in bytes that the queue can hold. Defaults to 0 (unlimited).
        max_size_time (int, optional): The maximum size in time that the queue can hold. Defaults to 0 (unlimited).
        leaky (str, optional): The leaky type of the queue. Can be 'no', 'upstream', or 'downstream'. Defaults to 'no'.

    Returns:
        str: A string representing the GStreamer queue element with the specified parameters.
    """
    q_string = f'queue name={name} leaky={leaky} max-size-buffers={max_size_buffers} max-size-bytes={max_size_bytes} max-size-time={max_size_time} '
    return q_string

def get_camera_resulotion(video_width=640, video_height=640):
    # This function will return a standard camera resolution based on the video resolution required
    # Standard resolutions are 640x480, 1280x720, 1920x1080, 3840x2160
    # If the required resolution is not standard, it will return the closest standard resolution
    if video_width <= 640 and video_height <= 480:
        return 640, 480
    elif video_width <= 1280 and video_height <= 720:
        return 1280, 720
    elif video_width <= 1920 and video_height <= 1080:
        return 1920, 1080
    else:
        return 3840, 2160


def SOURCE_PIPELINE(video_source, video_width=640, video_height=640, video_format='RGB', name='source', no_webcam_compression=False):
    """
    Creates a GStreamer pipeline string for the video source.

    Args:
        video_source (str): The path or device name of the video source.
        video_width (int, optional): The width of the video. Defaults to 640.
        video_height (int, optional): The height of the video. Defaults to 640.
        video_format (str, optional): The video format. Defaults to 'RGB'.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'source'.

    Returns:
        str: A string representing the GStreamer pipeline for the video source.
    """
    source_type = get_source_type(video_source)

    if source_type == 'usb':
        if no_webcam_compression:
            # When using uncomressed format, only low resolution is supported
            source_element = (
                f'v4l2src device={video_source} name={name} ! '
                f'video/x-raw, width=640, height=480 ! '
                'videoflip name=videoflip video-direction=horiz ! '
            )
        else:
            # Use compressed format for webcam
            width, height = get_camera_resulotion(video_width, video_height)
            source_element = (
                f'v4l2src device={video_source} name={name} ! image/jpeg, framerate=30/1, width={width}, height={height} ! '
                f'{QUEUE(name=f"{name}_queue_decode")} ! '
                f'decodebin name={name}_decodebin ! '
                f'videoflip name=videoflip video-direction=horiz ! '
            )
    elif source_type == 'rpi':
        source_element = (
            f'appsrc name=app_source is-live=true leaky-type=downstream max-buffers=3 ! '
            'videoflip name=videoflip video-direction=horiz ! '
            f'video/x-raw, format={video_format}, width={video_width}, height={video_height} ! '
        )
    elif source_type == 'libcamera':
        source_element = (
            f'libcamerasrc name={name} ! '
            f'video/x-raw, format={video_format}, width=1536, height=864 ! '
        )
    elif source_type == 'ximage':
        source_element = (
            f'ximagesrc xid={video_source} ! '
            f'{QUEUE(name=f"{name}queue_scale_")} ! '
            f'videoscale ! '
        )
    else:
        source_element = (
            f'filesrc location="{video_source}" name={name} ! '
            f'{QUEUE(name=f"{name}_queue_decode")} ! '
            f'decodebin name={name}_decodebin ! '
        )
    source_pipeline = (
        f'{source_element} '
        f'{QUEUE(name=f"{name}_scale_q")} ! '
        f'videoscale name={name}_videoscale n-threads=2 ! '
        f'{QUEUE(name=f"{name}_convert_q")} ! '
        f'videoconvert n-threads=3 name={name}_convert qos=false ! '
        f'video/x-raw, pixel-aspect-ratio=1/1, format={video_format}, width={video_width}, height={video_height} '
    )

    return source_pipeline

def INFERENCE_PIPELINE(
    hef_path,
    post_process_so=None,
    batch_size=1,
    config_json=None,
    post_function_name=None,
    additional_params='',
    name='inference',
    # Extra hailonet parameters
    scheduler_timeout_ms=None,
    scheduler_priority=None,
    vdevice_group_id=1,
    multi_process_service=None
):
    """
    Creates a GStreamer pipeline string for inference and post-processing using a user-provided shared object file.
    This pipeline includes videoscale and videoconvert elements to convert the video frame to the required format.
    The format and resolution are automatically negotiated based on the HEF file requirements.

    Args:
        hef_path (str): Path to the HEF file.
        post_process_so (str or None): Path to the post-processing .so file. If None, post-processing is skipped.
        batch_size (int): Batch size for hailonet (default=1).
        config_json (str or None): Config JSON for post-processing (e.g., label mapping).
        post_function_name (str or None): Function name in the .so postprocess.
        additional_params (str): Additional parameters appended to hailonet.
        name (str): Prefix name for pipeline elements (default='inference').

        # Extra hailonet parameters
        Run `gst-inspect-1.0 hailonet` for more information.
        vdevice_group_id (int): hailonet vdevice-group-id. Default=1.
        scheduler_timeout_ms (int or None): hailonet scheduler-timeout-ms. Default=None.
        scheduler_priority (int or None): hailonet scheduler-priority. Default=None.
        multi_process_service (bool or None): hailonet multi-process-service. Default=None.

    Returns:
        str: A string representing the GStreamer pipeline for inference.
    """
    # config & function strings
    config_str = f' config-path={config_json} ' if config_json else ''
    function_name_str = f' function-name={post_function_name} ' if post_function_name else ''
    vdevice_group_id_str = f' vdevice-group-id={vdevice_group_id} '
    multi_process_service_str = f' multi-process-service={str(multi_process_service).lower()} ' if multi_process_service is not None else ''
    scheduler_timeout_ms_str = f' scheduler-timeout-ms={scheduler_timeout_ms} ' if scheduler_timeout_ms is not None else ''
    scheduler_priority_str = f' scheduler-priority={scheduler_priority} ' if scheduler_priority is not None else ''

    hailonet_str = (
        f'hailonet name={name}_hailonet '
        f'hef-path={hef_path} '
        f'batch-size={batch_size} '
        f'{vdevice_group_id_str}'
        f'{multi_process_service_str}'
        f'{scheduler_timeout_ms_str}'
        f'{scheduler_priority_str}'
        f'{additional_params} '
        f'force-writable=true '
    )

    inference_pipeline = (
        f'{QUEUE(name=f"{name}_scale_q")} ! '
        f'videoscale name={name}_videoscale n-threads=2 qos=false ! '
        f'{QUEUE(name=f"{name}_convert_q")} ! '
        f'video/x-raw, pixel-aspect-ratio=1/1 ! '
        f'videoconvert name={name}_videoconvert n-threads=2 ! '
        f'{QUEUE(name=f"{name}_hailonet_q")} ! '
        f'{hailonet_str} ! '
    )

    if post_process_so:
        inference_pipeline += (
            f'{QUEUE(name=f"{name}_hailofilter_q")} ! '
            f'hailofilter name={name}_hailofilter so-path={post_process_so} {config_str} {function_name_str} qos=false ! '
        )

    inference_pipeline += f'{QUEUE(name=f"{name}_output_q")} '

    return inference_pipeline

def INFERENCE_PIPELINE_WRAPPER(inner_pipeline, bypass_max_size_buffers=20, name='inference_wrapper'):
    """
    Creates a GStreamer pipeline string that wraps an inner pipeline with a hailocropper and hailoaggregator.
    This allows to keep the original video resolution and color-space (format) of the input frame.
    The inner pipeline should be able to do the required conversions and rescale the detection to the original frame size.

    Args:
        inner_pipeline (str): The inner pipeline string to be wrapped.
        bypass_max_size_buffers (int, optional): The maximum number of buffers for the bypass queue. Defaults to 20.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'inference_wrapper'.

    Returns:
        str: A string representing the GStreamer pipeline for the inference wrapper.
    """
    # Get the directory for post-processing shared objects
    tappas_post_process_dir = os.environ.get('TAPPAS_POST_PROC_DIR', '')
    whole_buffer_crop_so = os.path.join(tappas_post_process_dir, 'cropping_algorithms/libwhole_buffer.so')

    # Construct the inference wrapper pipeline string
    inference_wrapper_pipeline = (
        f'{QUEUE(name=f"{name}_input_q")} ! '
        f'hailocropper name={name}_crop so-path={whole_buffer_crop_so} function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true '
        f'hailoaggregator name={name}_agg '
        f'{name}_crop. ! {QUEUE(max_size_buffers=bypass_max_size_buffers, name=f"{name}_bypass_q")} ! {name}_agg.sink_0 '
        f'{name}_crop. ! {inner_pipeline} ! {name}_agg.sink_1 '
        f'{name}_agg. ! {QUEUE(name=f"{name}_output_q")} '
    )

    return inference_wrapper_pipeline

def OVERLAY_PIPELINE(name='hailo_overlay'):
    """
    Creates a GStreamer pipeline string for the hailooverlay element.
    This pipeline is used to draw bounding boxes and labels on the video.

    Args:
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_overlay'.

    Returns:
        str: A string representing the GStreamer pipeline for the hailooverlay element.
    """
    # Construct the overlay pipeline string
    overlay_pipeline = (
        f'{QUEUE(name=f"{name}_q")} ! '
        f'hailooverlay name={name} '
    )

    return overlay_pipeline

def DISPLAY_PIPELINE(video_sink='autovideosink', sync='true', show_fps='false', name='hailo_display'):
    """
    Creates a GStreamer pipeline string for displaying the video.
    It includes the hailooverlay plugin to draw bounding boxes and labels on the video.

    Args:
        video_sink (str, optional): The video sink element to use. Defaults to 'autovideosink'.
        sync (str, optional): The sync property for the video sink. Defaults to 'true'.
        show_fps (str, optional): Whether to show the FPS on the video sink. Should be 'true' or 'false'. Defaults to 'false'.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_display'.

    Returns:
        str: A string representing the GStreamer pipeline for displaying the video.
    """
    # Construct the display pipeline string
    display_pipeline = (
        f'{OVERLAY_PIPELINE(name=f"{name}_overlay")} ! '
        f'{QUEUE(name=f"{name}_videoconvert_q")} ! '
        f'videoconvert name={name}_videoconvert n-threads=2 qos=false ! '
        f'{QUEUE(name=f"{name}_q")} ! '
        f'fpsdisplaysink name={name} video-sink={video_sink} sync={sync} text-overlay={show_fps} signal-fps-measurements=true '
    )

    return display_pipeline

def FILE_SINK_PIPELINE(output_file='output.mkv', name='file_sink', bitrate=5000):
    """
    Creates a GStreamer pipeline string for saving the video to a file in .mkv format.
    It it recommended run ffmpeg to fix the file header after recording.
    example: ffmpeg -i output.mkv -c copy fixed_output.mkv
    Note: If your source is a file, looping will not work with this pipeline.
    Args:
        output_file (str): The path to the output file.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'file_sink'.
        bitrate (int, optional): The bitrate for the encoder. Defaults to 5000.

    Returns:
        str: A string representing the GStreamer pipeline for saving the video to a file.
    """
    # Construct the file sink pipeline string
    file_sink_pipeline = (
        f'{QUEUE(name=f"{name}_videoconvert_q")} ! '
        f'videoconvert name={name}_videoconvert n-threads=2 qos=false ! '
        f'{QUEUE(name=f"{name}_encoder_q")} ! '
        f'x264enc tune=zerolatency bitrate={bitrate} ! '
        f'matroskamux ! '
        f'filesink location={output_file} '
    )

    return file_sink_pipeline

def USER_CALLBACK_PIPELINE(name='identity_callback'):
    """
    Creates a GStreamer pipeline string for the user callback element.

    Args:
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'identity_callback'.

    Returns:
        str: A string representing the GStreamer pipeline for the user callback element.
    """
    # Construct the user callback pipeline string
    user_callback_pipeline = (
        f'{QUEUE(name=f"{name}_q")} ! '
        f'identity name={name} '
    )

    return user_callback_pipeline

def TRACKER_PIPELINE(class_id, kalman_dist_thr=0.8, iou_thr=0.9, init_iou_thr=0.7, keep_new_frames=2, keep_tracked_frames=15, keep_lost_frames=2, keep_past_metadata=False, qos=False, name='hailo_tracker'):
    """
    Creates a GStreamer pipeline string for the HailoTracker element.
    Args:
        class_id (int): The class ID to track. Default is -1, which tracks across all classes.
        kalman_dist_thr (float, optional): Threshold used in Kalman filter to compare Mahalanobis cost matrix. Closer to 1.0 is looser. Defaults to 0.8.
        iou_thr (float, optional): Threshold used in Kalman filter to compare IOU cost matrix. Closer to 1.0 is looser. Defaults to 0.9.
        init_iou_thr (float, optional): Threshold used in Kalman filter to compare IOU cost matrix of newly found instances. Closer to 1.0 is looser. Defaults to 0.7.
        keep_new_frames (int, optional): Number of frames to keep without a successful match before a 'new' instance is removed from the tracking record. Defaults to 2.
        keep_tracked_frames (int, optional): Number of frames to keep without a successful match before a 'tracked' instance is considered 'lost'. Defaults to 15.
        keep_lost_frames (int, optional): Number of frames to keep without a successful match before a 'lost' instance is removed from the tracking record. Defaults to 2.
        keep_past_metadata (bool, optional): Whether to keep past metadata on tracked objects. Defaults to False.
        qos (bool, optional): Whether to enable QoS. Defaults to False.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_tracker'.
    Note:
        For a full list of options and their descriptions, run `gst-inspect-1.0 hailotracker`.
    Returns:
        str: A string representing the GStreamer pipeline for the HailoTracker element.
    """
    # Construct the tracker pipeline string
    tracker_pipeline = (
        f'hailotracker name={name} class-id={class_id} kalman-dist-thr={kalman_dist_thr} iou-thr={iou_thr} init-iou-thr={init_iou_thr} '
        f'keep-new-frames={keep_new_frames} keep-tracked-frames={keep_tracked_frames} keep-lost-frames={keep_lost_frames} keep-past-metadata={keep_past_metadata} qos={qos} ! '
        f'{QUEUE(name=f"{name}_q")} '
    )
    return tracker_pipeline

def CROPPER_PIPELINE(
    inner_pipeline,
    so_path,
    function_name,
    use_letterbox=True,
    no_scaling_bbox=True,
    internal_offset=True,
    resize_method='bilinear',
    bypass_max_size_buffers=20,
    name='cropper_wrapper'
):
    """
    Wraps an inner pipeline with hailocropper and hailoaggregator.
    The cropper will crop detections made by earlier stages in the pipeline.
    Each detection is cropped and sent to the inner pipeline for further processing.
    The aggregator will combine the cropped detections with the original frame.
    Example use case: After face detection pipeline stage, crop the faces and send them to a face recognition pipeline.

    Args:
        inner_pipeline (str): The pipeline string to be wrapped.
        so_path (str): The path to the cropper .so library.
        function_name (str): The function name in the .so library.
        use_letterbox (bool): Whether to preserve aspect ratio. Defaults True.
        no_scaling_bbox (bool): If True, bounding boxes are not scaled. Defaults True.
        internal_offset (bool): If True, uses internal offsets. Defaults True.
        resize_method (str): The resize method. Defaults to 'inter-area'.
        bypass_max_size_buffers (int): For the bypass queue. Defaults to 20.
        name (str): A prefix name for pipeline elements. Defaults 'cropper_wrapper'.

    Returns:
        str: A pipeline string representing hailocropper + aggregator around the inner_pipeline.
    """
    return (
        f'{QUEUE(name=f"{name}_input_q")} ! '
        f'hailocropper name={name}_cropper '
        f'so-path={so_path} '
        f'function-name={function_name} '
        f'use-letterbox={str(use_letterbox).lower()} '
        f'no-scaling-bbox={str(no_scaling_bbox).lower()} '
        f'internal-offset={str(internal_offset).lower()} '
        f'resize-method={resize_method} '
        f'hailoaggregator name={name}_agg '
        # bypass
        f'{name}_cropper. ! '
        f'{QUEUE(name=f"{name}_bypass_q", max_size_buffers=bypass_max_size_buffers)} ! {name}_agg.sink_0 '
        # pipeline for the actual inference
        f'{name}_cropper. ! {inner_pipeline} ! {name}_agg.sink_1 '
        # aggregator output
        f'{name}_agg. ! {QUEUE(name=f"{name}_output_q")} '
    )
```

### common/__init__.py

```

```

### common/get_usb_camera.py

```
import os
import subprocess

# if udevadm is not installed, install it using the following command:
# sudo apt-get install udev


def get_usb_video_devices():
    """
    Get a list of video devices that are connected via USB and have video capture capability.
    """
    video_devices = [f'/dev/{device}' for device in os.listdir('/dev') if device.startswith('video')]
    usb_video_devices = []

    for device in video_devices:
        try:
            # Use udevadm to get detailed information about the device
            udevadm_cmd = ["udevadm", "info", "--query=all", "--name=" + device]
            result = subprocess.run(udevadm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8')

            # Check if the device is connected via USB and has video capture capabilities
            if "ID_BUS=usb" in output and ":capture:" in output:
                usb_video_devices.append(device)
        except Exception as e:
            print(f"Error checking device {device}: {e}")

    return usb_video_devices

def main():
    usb_video_devices = get_usb_video_devices()

    if usb_video_devices:
        print(f"USB cameras found on: {', '.join(usb_video_devices)}")
    else:
        print("No available USB cameras found.")

if __name__ == "__main__":
    main()
```

### common/hailo_rpi_common.py

```
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import signal
import threading
import subprocess
import platform

# Try to import hailo python module
try:
    import hailo
except ImportError:
    sys.exit("Failed to import hailo python module. Make sure you are in hailo virtual environment.")

from dotenv import load_dotenv
from pathlib import Path

# Load .env from repo root if it exists
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


# -----------------------------------------------------------------------------------------------
# Common functions
# -----------------------------------------------------------------------------------------------
def run_command(command):
    """Run a shell command and return the output as a string."""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return ""
    
def pkg_config_get(option, package):
    """Get package information from pkg-config."""
    return run_command(f"pkg-config {option} {package}")

def create_standard_resource_dirs(base_path: Path):
    """
    Create the default folder layout under a given resource path.
    - /models/hailo8
    - /models/hailo8l
    - /models/hailo10
    - /videos
    - /photos
    - /gifs
    """
    for sub in ["models/hailo8", "models/hailo8l", "models/hailo10", "videos", "photos", "gifs"]:
        (base_path / sub).mkdir(parents=True, exist_ok=True)

def detect_pkg_installed(pkg_name: str) -> bool:
    """
    Check if a package is installed on the system.
    Args:
        pkg_name (str): The name of the package to check.
    Returns:
        bool: True if the package is installed, False otherwise.
    """
    try:
        subprocess.check_output(["dpkg", "-s", pkg_name])
        return True
    except subprocess.CalledProcessError:
        return False
    
def detect_device_arch():
    """
    Detect the host architecture: rpi, arm, or x86.
    Returns:
        str: One of "rpi", "arm", "x86", or "unknown"
    """
    machine = platform.machine().lower()
    system = platform.system().lower()

    if "arm" in machine or "aarch64" in machine:
        # Detect Raspberry Pi based on OS and CPU
        if system == "linux" and (
            "raspberrypi" in platform.uname().node or
            "pi" in platform.uname().node
        ):
            return "rpi"
        else:
            return "arm"
    elif "x86" in machine or "amd64" in machine:
        return "x86"
    else:
        return "unknown"

def detect_hailo_arch():
    try:
        # Run the hailortcli command to get device information
        result = subprocess.run(['hailortcli', 'fw-control', 'identify'], capture_output=True, text=True)

        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error running hailortcli: {result.stderr}")
            return None

        # Search for the "Device Architecture" line in the output
        for line in result.stdout.split('\n'):
            if "Device Architecture" in line:
                if "HAILO8L" in line:
                    return "hailo8l"
                elif "HAILO8" in line:
                    return "hailo8"

        print("Could not determine Hailo architecture from device information.")
        return None
    except Exception as e:
        print(f"An error occurred while detecting Hailo architecture: {e}")
        return None

def get_caps_from_pad(pad: Gst.Pad):
    caps = pad.get_current_caps()
    if caps:
        # We can now extract information from the caps
        structure = caps.get_structure(0)
        if structure:
            # Extracting some common properties
            format = structure.get_value('format')
            width = structure.get_value('width')
            height = structure.get_value('height')
            return format, width, height
    else:
        return None, None, None


def get_default_parser():
    parser = argparse.ArgumentParser(description="Hailo App Help")
    parser.add_argument(
        "--input", "-i", type=str, default=None,
        help="Input source. Can be a file, USB (webcam), RPi camera (CSI camera module) or ximage. \
        For RPi camera use '-i rpi' \
        For automatically detect a connected usb camera, use '-i usb' \
        For manually specifying a connected usb camera, use '-i /dev/video<X>' \
        Defaults to application specific video."
    )
    parser.add_argument("--use-frame", "-u", action="store_true", help="Use frame from the callback function")
    parser.add_argument("--show-fps", "-f", action="store_true", help="Print FPS on sink")
    parser.add_argument(
            "--arch",
            default=None,
            choices=['hailo8', 'hailo8l'],
            help="Specify the Hailo architecture (hailo8 or hailo8l). Default is None , app will run check.",
        )
    parser.add_argument(
            "--hef-path",
            default=None,
            help="Path to HEF file",
        )
    parser.add_argument(
        "--disable-sync", action="store_true",
        help="Disables display sink sync, will run as fast as possible. Relevant when using file source."
    )
    parser.add_argument(
        "--disable-callback", action="store_true",
        help="Disables the user's custom callback function in the pipeline. Use this option to run the pipeline without invoking the callback logic."
    )
    parser.add_argument("--dump-dot", action="store_true", help="Dump the pipeline graph to a dot file pipeline.dot")
    return parser


# ---------------------------------------------------------
# Functions used to get numpy arrays from GStreamer buffers
# ---------------------------------------------------------

def handle_rgb(map_info, width, height):
    # The copy() method is used to create a copy of the numpy array. This is necessary because the original numpy array is created from buffer data, and it does not own the data it represents. Instead, it's just a view of the buffer's data.
    return np.ndarray(shape=(height, width, 3), dtype=np.uint8, buffer=map_info.data).copy()

def handle_nv12(map_info, width, height):
    y_plane_size = width * height
    uv_plane_size = width * height // 2
    y_plane = np.ndarray(shape=(height, width), dtype=np.uint8, buffer=map_info.data[:y_plane_size]).copy()
    uv_plane = np.ndarray(shape=(height//2, width//2, 2), dtype=np.uint8, buffer=map_info.data[y_plane_size:]).copy()
    return y_plane, uv_plane

def handle_yuyv(map_info, width, height):
    return np.ndarray(shape=(height, width, 2), dtype=np.uint8, buffer=map_info.data).copy()

FORMAT_HANDLERS = {
    'RGB': handle_rgb,
    'NV12': handle_nv12,
    'YUYV': handle_yuyv,
}

def get_numpy_from_buffer(buffer, format, width, height):
    """
    Converts a GstBuffer to a numpy array based on provided format, width, and height.

    Args:
        buffer (GstBuffer): The GStreamer Buffer to convert.
        format (str): The video format ('RGB', 'NV12', 'YUYV', etc.).
        width (int): The width of the video frame.
        height (int): The height of the video frame.

    Returns:
        np.ndarray: A numpy array representing the buffer's data, or a tuple of arrays for certain formats.
    """
    # Map the buffer to access data
    success, map_info = buffer.map(Gst.MapFlags.READ)
    if not success:
        raise ValueError("Buffer mapping failed")

    try:
        # Handle different formats based on the provided format parameter
        handler = FORMAT_HANDLERS.get(format)
        if handler is None:
            raise ValueError(f"Unsupported format: {format}")
        return handler(map_info, width, height)
    finally:
        buffer.unmap(map_info)
```

### common/test_utils.py

```
import os
import time
import signal
import subprocess
import logging
from pathlib import Path
from hailo_apps_infra.common.hailo_rpi_common import detect_device_arch, detect_hailo_arch
from hailo_apps_infra.common.get_usb_camera import get_usb_video_devices


logger = logging.getLogger("pipeline-tests-utils")

TEST_RUN_TIME = 10
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

def is_rpi_camera_available():
    try:
        from picamera2 import Picamera2
    except ImportError:
        return False

    try:
        result = subprocess.run(['rpicam-hello', '-t', '1'], capture_output=True, timeout=5)
        if "no cameras available" in result.stderr.decode().lower():
            return False
        return True
    except Exception:
        return False


def get_device_architecture():
    platform_arch = detect_device_arch()
    hailo_arch = detect_hailo_arch()
    logger.info(f"Using platform: {platform_arch}, Hailo architecture: {hailo_arch}")
    return platform_arch, hailo_arch


def get_compatible_hefs(hailo_arch, model_type):
    if hailo_arch is None:
        return [f"resources/models/placeholder_{model_type}.hef"]

    base_dir = Path("resources/models") / hailo_arch
    if not base_dir.exists():
        logger.warning(f"Model directory not found: {base_dir}")
        return []

    model_keywords = {
        'detection': ["yolo", "detect"],
        'pose': ["pose"],
        'segmentation': ["seg"],
        'depth': ["depth"]
    }

    keywords = model_keywords.get(model_type, [])
    hefs = [str(p) for p in base_dir.glob("*.hef") if any(k in p.name.lower() for k in keywords)]

    if not hefs:
        logger.warning(f"No HEFs found for model_type={model_type} in {base_dir}")

    return hefs


def get_available_video_inputs():
    inputs = {}
    video_dir = Path("resources/video")
    video_files = list(video_dir.glob("*.mp4"))
    inputs['file'] = [str(f) for f in video_files] or ["resources/video/example.mp4"]

    try:
        devices = get_usb_video_devices()
        inputs['usb'] = [dev.device_path for dev in devices] + ['usb'] if devices else []
    except Exception as e:
        logger.warning(f"USB camera detection failed: {e}")

    platform_arch, _ = get_device_architecture()
    if platform_arch == 'rpi':
        try:
            from picamera2 import Picamera2
            inputs['rpi'] = ['rpi']
        except ImportError:
            pass

    return inputs


def run_pipeline_test(pipeline_module, hef_path, input_source, input_type, extra_args=None):
    hef_name = os.path.basename(hef_path)
    test_name = f"{pipeline_module.split('.')[-1]}_{hef_name}_{input_type}"
    log_file_path = log_dir / f"{test_name}.log"

    cmd = [
        'python', '-m', pipeline_module,
        '--input', input_source,
        '--hef-path', hef_path
    ] + (extra_args or [])

    logger.info(f"Running test: {' '.join(cmd)}")

    with open(log_file_path, "w") as log_file:
        log_file.write(f"Running command: {' '.join(cmd)}\n")
        process = subprocess.Popen(cmd)
        try:
            time.sleep(TEST_RUN_TIME)
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        except Exception as e:
            process.kill()
            logger.error(f"Test failed: {e}")
            return False

    return process.returncode in [0, -15]
```

### config/config.yaml

```
hailort_version: "4.20.0"
tappas_version: "3.31.0"
apps_infra_version: "25.3.1"
model_zoo_version: "2.14.0"
device_arch: "rpi" # Options: "rpi" (Raspberry Pi), "x86" (desktop/server), "arm" (generic ARM board) or "auto" (detect from device)
hailo_arch: "auto" # Options: "hailo8", "hailo8l", or "auto" (detect from device)
resources_path: "/usr/local/hailo/resources" # If set to "auto" or empty, defaults to /usr/local/hailo/resources
python_version: "3.11"
auto_symlink: true
```

### config/resources_config.yaml

```
groups:
  default:
    - yolov8m_pose
    - yolov5m_seg
    - yolov8m
    - yolov6n_h8
    - scdepthv3_h8
    - yolov8s_h8l
    - yolov8s_pose_h8l
    - yolov5n_seg_h8l
    - yolov6n_h8l
    - scdepthv3_h8l
    - example
    - example_640
  all:
    - yolov8m
    - #yolov5m_wo_spp_h8
    - yolov8s_h8
    - yolov8m_pose
    - yolov8s_pose
    - yolov5m_seg
    - yolov5n_seg_h8
    - yolov6n_h8
    - yolov11n_h8
    - yolov11s_h8
    - scdepthv3_h8
    - #yolov5m_wo_spp_h8l
    - yolov8m_h8l
    - yolov11n_h8l
    - yolov11s_h8l
    - yolov8s_h8l
    - yolov6n_h8l
    - scdepthv3_h8l
    - yolov8s_pose_h8l
    - yolov5n_seg_h8l
    - yolov8s_barcode_h8l
    - example
    - barcode
    - example_640
  test: []
  custom: []

models:
  # Hailo8 models
  yolov8m:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov8m.hef
    arch: hailo8
  yolov8m_pose:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov8m_pose.hef
    arch: hailo8
  yolov8s_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov8s.hef
    arch: hailo8
  yolov8s_pose:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov8s_pose.hef
    arch: hailo8
  yolov5m_seg:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov5m_seg.hef
    arch: hailo8
  yolov5n_seg_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov5n_seg.hef
    arch: hailo8
  yolov6n_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov6n.hef
    arch: hailo8
  yolov11n_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov11n.hef
    arch: hailo8
  yolov11s_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov11s.hef
    arch: hailo8
  scdepthv3_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/scdepthv3.hef
    arch: hailo8
  yolov5m_wo_spp_h8:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8/yolov5m_wo_spp.hef
    arch: hailo8
    
  # Hailo8L models
  yolov5m_wo_spp_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov5m_wo_spp.hef
    arch: hailo8l
  yolov8m_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov8m.hef
    arch: hailo8l
  yolov8s_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov8s.hef
    arch: hailo8l
  yolov11n_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov11n.hef
    arch: hailo8l
  yolov11s_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov11s.hef
    arch: hailo8l
  yolov6n_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov6n.hef
    arch: hailo8l
  scdepthv3_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/scdepthv3.hef
    arch: hailo8l
  yolov8s_pose_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov8s_pose.hef
    arch: hailo8l
  yolov5n_seg_h8l:
    url: https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.14.0/hailo8l/yolov5n_seg.hef
    arch: hailo8l
  yolov8s_barcode_h8l:
    url: https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/hefs/h8l_rpi/yolov8s-hailo8l-barcode.hef
    arch: hailo8l

videos:
  example:
    url: https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/example.mp4
  barcode:
    url: https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/barcode.mp4
  example_640:
    url: https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/video/example_640.mp4

photos: {}
gifs: {}
```

### installation/__init__.py

```

```

### installation/compile_cpp.py

```
import subprocess
import logging
import pathlib

logger = logging.getLogger("cpp-compiler")

def compile_postprocess(mode="release"):
    script_path = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "compile_postprocess.sh"
    cmd = [str(script_path)]
    if mode in ("debug", "clean"):
        cmd.append(mode)

    logger.info(f"Running C++ build: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
```

### installation/download_resources.py

```

import argparse
import logging
import os
from pathlib import Path
import yaml
import urllib.request
from hailo_apps_infra.common.hailo_rpi_common import detect_hailo_arch
from importlib.resources import files

logger = logging.getLogger("resource-downloader")
logging.basicConfig(level=logging.INFO)

def load_config():
    config_path = files("hailo_apps_infra").joinpath("config/resources_config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def download_file(url, dest_path):
    if dest_path.exists():
        logger.info(f"✅ {dest_path.name} already exists, skipping.")
        return
    logger.info(f"⬇ Downloading {url} → {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest_path)
    logger.info(f"✅ Downloaded to {dest_path}")

def download_resources(group=None, names=None):
    config = load_config()
    arch = detect_hailo_arch()
    logger.info(f"Detected Hailo architecture: {arch}")

    resources_dir = Path("/usr/local/hailo/resources")
    selected_names = set()

    # Always include resources from the default group
    selected_names.update(config["groups"]["default"])

    # If another group is provided (and it's not "default"), add its resources too
    if group and group != "default":
        selected_names.update(config["groups"].get(group, []))

    # If specific resource names are provided, add them as well
    if names:
        selected_names.update(names)

    for name in selected_names:
        if name in config["models"]:
            model = config["models"][name]
            if model["arch"] == arch:
                subdir = resources_dir / "models" / arch
                dest = subdir / f"{name}.hef"
                download_file(model["url"], dest)
            else:
                logger.info(f"⏩ Skipping {name}, not for arch {arch}")
        elif name in config["videos"]:
            dest = resources_dir / "videos" / f"{name}.mp4"
            download_file(config["videos"][name]["url"], dest)
        else:
            logger.warning(f"⚠ Unknown resource: {name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", type=str, help="Download a named group like default, all, test")
    parser.add_argument("--name", nargs="*", help="Download specific resources by name")
    args = parser.parse_args()

    if not args.group and not args.name:
        print("❌ Please specify either --group or --name , will download the default only!")

    download_resources(group=args.group, names=args.name)
```

### installation/install.py

```
import os
import subprocess
import pathlib
import logging
from hailo_apps_infra.installation.validate_config import load_config, validate_config
from hailo_apps_infra.installation.post_install import run_post_install
from hailo_apps_infra.installation.compile_cpp import compile_postprocess


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hailo-installer")

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def run_command(command, error_msg):
    logger.info(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        logger.error(f"{error_msg} (exit code {result.returncode})")
        exit(result.returncode)


def install():
    logger.info("Loading and validating configuration...")
    config = load_config(PROJECT_ROOT / "hailo_apps_infra" / "config" / "config.yaml")
    validate_config(config)

    logger.info("Running post-install setup...")
    run_post_install(config)

    logger.info("Compiling post-process code...")
    compile_postprocess()

    #logger.info("Downloading resources...")
    #run_command("./scripts/download_resources.sh --all", "Failed to download models/resources")

    logger.info("Hailo Infra installation completed successfully!")


if __name__ == "__main__":
    install()
```

### installation/post_install.py

```
import os
import pathlib
import logging
import shutil
from hailo_apps_infra.installation.set_env import set_environment_vars
from hailo_apps_infra.installation.download_resources import download_resources


logger = logging.getLogger("post-install")
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

def create_resources_symlink(resource_path):
    """Creates (or refreshes) a symlink for the resources directory."""
    resources_link = PROJECT_ROOT / "resources"
    resources_target = pathlib.Path(resource_path)
    if resources_link.exists():
        if resources_link.is_symlink():
            logger.info("Removing existing symlink to resources.")
            resources_link.unlink()
        else:
            logger.info(f"Removing existing directory {resources_link}.")
            shutil.rmtree(resources_link)
    logger.info(f"Creating symlink: {resources_link} -> {resources_target}")
    resources_link.symlink_to(resources_target, target_is_directory=True)

def create_postproc_symlink(resource_path, tappas_post_proc_dir):
    resource_path = pathlib.Path(resource_path)
    tappas_target = pathlib.Path(tappas_post_proc_dir)
    
    # Check if tappas_target is already under resource_path using a string comparison.
    if str(tappas_target).startswith(str(resource_path)):
        logger.info("TAPPAS postproc directory is already within the resource path. Skipping symlink creation.")
        return

    postproc_link = resource_path / "postproc"
    if postproc_link.exists():
        if postproc_link.is_symlink():
            logger.info("Removing existing symlink for tappas post-processing directory.")
            postproc_link.unlink()
        else:
            logger.info(f"Removing existing directory {postproc_link}.")
            shutil.rmtree(postproc_link)
    logger.info(f"Creating symlink: {postproc_link} -> {tappas_target}")
    postproc_link.symlink_to(tappas_target, target_is_directory=True)




def run_post_install(config, resource_group="default"):
    # Set or default the resource path
    resource_path = config.get("resource_path")
    if not resource_path or resource_path == "auto":
        resource_path = "/usr/local/hailo/resources"
    config["resource_path"] = resource_path

    # Set environment variables (including TAPPAS_POST_PROC_DIR)
    set_environment_vars(config)
    
    # Create the primary symlink for the resources folder
    create_resources_symlink(resource_path)
    
    # Create a symlink inside the resources folder that points to the tappas postproc directory
    tappas_post_proc_dir = os.environ.get("TAPPAS_POST_PROC_DIR")
    if tappas_post_proc_dir:
        create_postproc_symlink(resource_path, tappas_post_proc_dir)
    else:
        logger.error("TAPPAS_POST_PROC_DIR is not set. Cannot create postproc symlink.")

    logger.info("📦 Ensuring default resources are downloaded...")
    download_resources(group=resource_group)
    logger.info("Post-install setup completed.")
```

### installation/set_env.py

```
import os
import logging
import subprocess
from pathlib import Path
from hailo_apps_infra.common.hailo_rpi_common import detect_device_arch, detect_hailo_arch , detect_pkg_installed, pkg_config_get

logger = logging.getLogger("env-setup")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

def get_tappas_post_proc_dir(tappas_variant=None):
    """Get the TAPPAS_POST_PROC_DIR based on the installed TAPPAS variant."""
    if tappas_variant == "hailo-tappas-core":
        tappas_post_proc_dir = pkg_config_get("--variable=tappas_postproc_lib_dir", "hailo-tappas-core")
    elif tappas_variant == "hailo_tappas":
        tappas_workspace = pkg_config_get("--variable=tappas_workspace", "hailo_tappas")
        tappas_post_proc_dir = os.path.join(tappas_workspace, "apps/h8/gstreamer/libs/post_processes/")
    else:
        print("Error: Neither hailo-tappas-core nor hailo_tappas is installed")
        return None
    
    # Verify the discovered path exists
    if not os.path.exists(tappas_post_proc_dir):
        print(f"Warning: TAPPAS_POST_PROC_DIR '{tappas_post_proc_dir}' does not exist")
    else:
        print(f"Found TAPPAS_POST_PROC_DIR: {tappas_post_proc_dir}")
    
    return tappas_post_proc_dir

def set_environment_vars(config, refresh=False):
    if not refresh and ENV_PATH.exists():
        logger.info("Using existing .env (set refresh=True to regenerate)")
        return

    device_arch = config.get("device_arch") or "auto"
    hailo_arch = config.get("hailo_arch") or "auto"
    resource_path = config.get("resource_path") or "auto"

    if device_arch == "auto":
        device_arch = detect_device_arch()
    if hailo_arch == "auto":
        hailo_arch = detect_hailo_arch()
    if resource_path == "auto":
        resource_path = "/usr/local/hailo/resources"

    # TAPPAS dir detection
    if detect_pkg_installed("hailo-tappas"):
        tappas_variant = "tappas"
    elif detect_pkg_installed("hailo-tappas-core"):
        tappas_variant = "tappas-core"
    else:
        tappas_variant = "none"
        logger.warning("⚠ Could not detect TAPPAS variant.")

    # tappas_postproc_dir = os.path.join(resource_path, "postproc", tappas_variant) if tappas_variant != "none" else ""
    tappas_postproc_dir = get_tappas_post_proc_dir(tappas_variant)
    model_dir = os.path.join(resource_path, "models")

    os.environ["DEVICE_ARCH"] = device_arch
    os.environ["HAILO_ARCH"] = hailo_arch
    os.environ["RESOURCE_PATH"] = resource_path
    os.environ["TAPPAS_POST_PROC_DIR"] = tappas_postproc_dir

    logger.info(f"Set DEVICE_ARCH={device_arch}")
    logger.info(f"Set HAILO_ARCH={hailo_arch}")
    logger.info(f"Set TAPPAS_POST_PROC_DIR={tappas_postproc_dir}")
    logger.info(f"Set RESOURCE_PATH={resource_path}")

    persist_env_vars(device_arch, hailo_arch, resource_path, tappas_postproc_dir, model_dir)


def persist_env_vars(device_arch, hailo_arch, resource_path, tappas_postproc_dir, model_dir):
    with open(ENV_PATH, "w") as f:
        f.write(f"DEVICE_ARCH={device_arch}\n")
        f.write(f"HAILO_ARCH={hailo_arch}\n")
        f.write(f"RESOURCE_PATH={resource_path}\n")
        f.write(f"TAPPAS_POST_PROC_DIR={tappas_postproc_dir}\n")
    logger.info(f"✅ Persisted environment variables to {ENV_PATH}")
```

### installation/validate_config.py

```
import yaml
import logging

logger = logging.getLogger("config-validator")

REQUIRED_KEYS = [
    "hailort_version",
    "tappas_version",
    "apps_infra_version",
    "model_zoo_version",
    "device_arch",
    "hailo_arch"
    ]

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_config(config):
    logger.info("Validating config keys...")
    for key in REQUIRED_KEYS:
        if key not in config:
            raise KeyError(f"Missing required config key: {key}")
    logger.info("Config is valid.")
```

