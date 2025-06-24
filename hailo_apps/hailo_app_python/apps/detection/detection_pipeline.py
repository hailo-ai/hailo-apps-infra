# region imports
# Standard library imports
import setproctitle

# Local application-specific imports
from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch
from hailo_apps.hailo_app_python.core.common.core import get_default_parser, get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import DETECTION_APP_TITLE, DETECTION_PIPELINE, RESOURCES_MODELS_DIR_NAME, RESOURCES_SO_DIR_NAME, DETECTION_POSTPROCESS_SO_FILENAME, DETECTION_POSTPROCESS_FUNCTION
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import SOURCE_PIPELINE, INFERENCE_PIPELINE, INFERENCE_PIPELINE_WRAPPER, TRACKER_PIPELINE, USER_CALLBACK_PIPELINE, DISPLAY_PIPELINE
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import GStreamerApp, app_callback_class, dummy_callback
# endregion imports

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
        else:
            self.hef_path = get_resource_path(DETECTION_PIPELINE, RESOURCES_MODELS_DIR_NAME)


            # Set the post-processing shared object file
        self.post_process_so = get_resource_path(
            DETECTION_PIPELINE, RESOURCES_SO_DIR_NAME, DETECTION_POSTPROCESS_SO_FILENAME
        )

         
  
        self.post_function_name = DETECTION_POSTPROCESS_FUNCTION
        # User-defined label JSON file
        self.labels_json = self.options_menu.labels_json

        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Set the process title
        setproctitle.setproctitle(DETECTION_APP_TITLE)

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(video_source=self.video_source,
                                          video_width=self.video_width, video_height=self.video_height,
                                          frame_rate=self.frame_rate, sync=self.sync)
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

def main():
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
    
if __name__ == "__main__":
    print("Starting Hailo Detection App...")
    main()
 