# region imports
# Standard library imports
import os
import setproctitle
from pathlib import Path
import sys

# Local application-specific imports
from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch
from hailo_apps.hailo_app_python.core.common.core import get_default_parser, get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import POSE_ESTIMATION_APP_TITLE, POSE_ESTIMATION_PIPELINE, RESOURCES_MODELS_DIR_NAME, RESOURCES_SO_DIR_NAME, POSE_ESTIMATION_POSTPROCESS_SO_FILENAME, POSE_ESTIMATION_POSTPROCESS_FUNCTION, HAILO_ARCH_KEY
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import SOURCE_PIPELINE, INFERENCE_PIPELINE, INFERENCE_PIPELINE_WRAPPER, TRACKER_PIPELINE, USER_CALLBACK_PIPELINE, DISPLAY_PIPELINE
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import GStreamerApp, app_callback_class, dummy_callback
# endregion imports

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
            detected_arch = os.getenv(HAILO_ARCH_KEY, detect_hailo_arch())
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch



        # Set the HEF file path based on the architecture
        if self.options_menu.hef_path:
            self.hef_path = self.options_menu.hef_path
        else: # Set models based on hailo8 or hailo8l
            self.hef_path = get_resource_path(
                pipeline_name=POSE_ESTIMATION_PIPELINE,
                resource_type=RESOURCES_MODELS_DIR_NAME,
            )
        self.app_callback = app_callback

        # Set the post-processing shared object file
        self.post_process_so = get_resource_path(POSE_ESTIMATION_PIPELINE, RESOURCES_SO_DIR_NAME, POSE_ESTIMATION_POSTPROCESS_SO_FILENAME)

        self.post_process_function = POSE_ESTIMATION_POSTPROCESS_FUNCTION

        # Set the process title
        setproctitle.setproctitle(POSE_ESTIMATION_APP_TITLE)

        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(video_source=self.video_source,
                                          video_width=self.video_width, video_height=self.video_height,
                                          frame_rate=self.frame_rate, sync=self.sync)
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

def main():    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app = GStreamerPoseEstimationApp(dummy_callback, user_data)
    app.run()

if __name__ == "__main__":
    print("Starting Hailo Pose Estimation App...")
    main()
