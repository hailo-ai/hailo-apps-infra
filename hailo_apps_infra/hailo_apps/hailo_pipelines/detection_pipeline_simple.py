import numpy as np
import setproctitle
from pathlib import Path
import sys

# Ensure hailo_core is importable from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/dev/hailo-apps-infra/hailo_apps_infra
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Common Hailo helpers ────────────────────────────────────────────────────────

try:
    from hailo_core.hailo_common.core import (
        get_default_parser,
        detect_hailo_arch,
    )
except ImportError:
    from hailo_apps_infra.hailo_core.hailo_common.core import (
        get_default_parser,
        detect_hailo_arch,
    )
try:
    from hailo_core.hailo_common.core import get_resource_path
except ImportError:
    from hailo_apps_infra.hailo_core.hailo_common.core import get_resource_path
try:
    from hailo_core.hailo_common.defines import (
        SIMPLE_DETECTION_PIPELINE,
        RESOURCES_VIDEOS_DIR_NAME,
        RESOURCES_MODELS_DIR_NAME,
        RESOURCES_SO_DIR_NAME,
        SIMPLE_DETECTION_VIDEO_NAME,
        SIMPLE_DETECTION_POSTPROCESS_SO_FILENAME,
        SIMPLE_DETECTION_POSTPROCESS_FUNCTION,
        SIMPLE_DETECTION_APP_TITLE,
    )
except ImportError:
    from hailo_apps_infra.hailo_core.hailo_common.defines import (
        SIMPLE_DETECTION_PIPELINE,
        RESOURCES_VIDEOS_DIR_NAME,
        RESOURCES_MODELS_DIR_NAME,
        RESOURCES_SO_DIR_NAME,
        SIMPLE_DETECTION_VIDEO_NAME,
        SIMPLE_DETECTION_POSTPROCESS_SO_FILENAME,
        SIMPLE_DETECTION_POSTPROCESS_FUNCTION,
        SIMPLE_DETECTION_APP_TITLE,
    )
# ─── GStreamer routines (from your hailo_gstreamer package) ────────────────────
try:
    from hailo_apps.hailo_gstreamer.gstreamer_helper_pipelines import (
        SOURCE_PIPELINE,
        INFERENCE_PIPELINE,
        USER_CALLBACK_PIPELINE,
        DISPLAY_PIPELINE,
    )
except ImportError:
    from hailo_apps_infra.hailo_apps.hailo_gstreamer.gstreamer_helper_pipelines import (
        SOURCE_PIPELINE,
        INFERENCE_PIPELINE,
        USER_CALLBACK_PIPELINE,
        DISPLAY_PIPELINE,
    )
try:
    from hailo_apps.hailo_gstreamer.gstreamer_app import (
        GStreamerApp,
        app_callback_class,
        dummy_callback,
    )
except ImportError:
    from hailo_apps_infra.hailo_apps.hailo_gstreamer.gstreamer_app import (
        GStreamerApp,
        app_callback_class,
        dummy_callback,
    )
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
        parser.add_argument(
            "--so-path",
            default=None,
            help="Path to the shared object file for post-processing",
        )
        parser.add_argument(
            "--pp-function",
            default=None,
            help="Name of the post-processing function in the shared object file",
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
            self.video_source = get_resource_path(
                pipeline_name=SIMPLE_DETECTION_PIPELINE,
                resource_type=RESOURCES_VIDEOS_DIR_NAME,
                model=SIMPLE_DETECTION_VIDEO_NAME
            )
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
        else: 
            self.hef_path = get_resource_path(
                pipeline_name=SIMPLE_DETECTION_PIPELINE,
                resource_type=RESOURCES_MODELS_DIR_NAME,
            )
        
        print(f"Using HEF path: {self.hef_path}")
        if self.options_menu.so_path is not None:
            self.post_process_so = self.options_menu.so_path
        else:
            self.post_process_so = get_resource_path(
                pipeline_name=SIMPLE_DETECTION_PIPELINE,
                resource_type=RESOURCES_SO_DIR_NAME,
                model=SIMPLE_DETECTION_POSTPROCESS_SO_FILENAME
            )
        print(f"Using post-process shared object: {self.post_process_so}")

        if self.options_menu.pp_function is not None:
            self.post_function_name = self.options_menu.pp_function
        else:
            self.post_function_name = SIMPLE_DETECTION_POSTPROCESS_FUNCTION

        # User-defined label JSON file
        self.labels_json = self.options_menu.labels_json

        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Set the process title
        setproctitle.setproctitle(SIMPLE_DETECTION_APP_TITLE)

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(video_source=self.video_source,
                                          video_width=self.video_width, video_height=self.video_height,
                                          frame_rate=self.frame_rate, sync=self.sync,
                                          no_webcam_compression=True)
        
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

def main():
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()

if __name__ == "__main__":
    print("Starting Hailo Detection App...")
    main()
