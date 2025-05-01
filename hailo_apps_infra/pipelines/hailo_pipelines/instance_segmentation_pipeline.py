import gi
# Initialize GStreamer
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
from hailo_common.common import (
    get_default_parser,
    detect_hailo_arch,
)
from hailo_gstreamer.gstreamer_helper_pipelines import(
    QUEUE,
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
)
from hailo_gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback
)
from hailo_common.utils import (
    load_environment,
    get_resource_path,
)

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESOURCES_DIR = PROJECT_ROOT / "resources"
LOCAL_RESOURCES = PROJECT_ROOT / "local_resources"

#-----------------------------------------------------------------------------------------------
# User GStreamer Application: Instance Segmentation
#-----------------------------------------------------------------------------------------------

class GStreamerInstanceSegmentationApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        # Load .env variables (e.g., RESOURCE_PATH)
        load_environment()

        if parser is None:
            parser = get_default_parser()
        super().__init__(parser, user_data)

        # Hailo parameters
        self.batch_size = 2
        self.video_width = 640
        self.video_height = 640

        # Detect architecture if not provided
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch

        # Set HEF path (string) for segmentation models
        if self.options_menu.hef_path:
            self.hef_path = str(self.options_menu.hef_path)
        else:
            # get_resource_path will use RESOURCE_PATH from env
            self.hef_path = str(get_resource_path(
                pipeline_name="seg",
                resource_type="models",
            ))

        # Determine which JSON config to use based on HEF filename
        hef_name = Path(self.hef_path).name
        if 'yolov5m_seg' in hef_name:
            self.config_file = str(LOCAL_RESOURCES / "yolov5m_seg.json")
        elif 'yolov5n_seg' in hef_name:
            self.config_file = str(LOCAL_RESOURCES / "yolov5n_seg.json")
        else:
            raise ValueError("HEF version not supported; please provide a compatible segmentation HEF or config file.")

        # Post-process shared object
        self.post_process_so = str(RESOURCES_DIR / "so" / "libyolov5seg_postprocess.so")
        self.post_function_name = "filter_letterbox"

        # Callback
        self.app_callback = app_callback

        # Set process title for easy identification
        setproctitle.setproctitle("Hailo Instance Segmentation App")

        # Build the GStreamer pipeline
        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(
            video_source=self.video_source,
            video_width=self.video_width,
            video_height=self.video_height,
        )
        infer_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.config_file,
        )
        infer_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(infer_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        display_pipeline = DISPLAY_PIPELINE(
            video_sink=self.video_sink,
            sync=self.sync,
            show_fps=self.show_fps,
        )

        pipeline_string = (
            f"{source_pipeline} ! "
            f"{infer_pipeline_wrapper} ! "
            f"{tracker_pipeline} ! "
            f"{user_callback_pipeline} ! "
            f"{display_pipeline}"
        )
        print(pipeline_string)
        return pipeline_string


def main():
    user_data = app_callback_class()
    app = GStreamerInstanceSegmentationApp(dummy_callback, user_data)
    app.run()

if __name__ == "__main__":
    print("Starting Hailo Instance Segmentation App...")
    main()
