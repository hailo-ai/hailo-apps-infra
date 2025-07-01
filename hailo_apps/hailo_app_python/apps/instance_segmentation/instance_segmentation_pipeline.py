# region imports
# Standard library imports
import os
import setproctitle
from pathlib import Path
import sys

# Local application-specific imports
from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch
from hailo_apps.hailo_app_python.core.common.core import get_default_parser, get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import RESOURCES_JSON_DIR_NAME, HAILO_ARCH_KEY, INSTANCE_SEGMENTATION_APP_TITLE, INSTANCE_SEGMENTATION_PIPELINE, RESOURCES_MODELS_DIR_NAME, RESOURCES_SO_DIR_NAME, INSTANCE_SEGMENTATION_MODEL_NAME_H8, INSTANCE_SEGMENTATION_MODEL_NAME_H8L, INSTANCE_SEGMENTATION_POSTPROCESS_SO_FILENAME, INSTANCE_SEGMENTATION_POSTPROCESS_FUNCTION, DEFAULT_LOCAL_RESOURCES_PATH, JSON_FILE_EXTENSION
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import SOURCE_PIPELINE, INFERENCE_PIPELINE, INFERENCE_PIPELINE_WRAPPER, TRACKER_PIPELINE, USER_CALLBACK_PIPELINE, DISPLAY_PIPELINE
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import GStreamerApp, app_callback_class, dummy_callback
# endregion imports

#-----------------------------------------------------------------------------------------------
# User GStreamer Application: Instance Segmentation
#-----------------------------------------------------------------------------------------------

class GStreamerInstanceSegmentationApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):

        if parser is None:
            parser = get_default_parser()
        super().__init__(parser, user_data)

        # Hailo parameters
        self.batch_size = 2
        self.video_width = 640
        self.video_height = 640

        # Detect architecture if not provided
        if self.options_menu.arch is None:
            detected_arch = os.getenv(HAILO_ARCH_KEY, detect_hailo_arch())
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
                pipeline_name=INSTANCE_SEGMENTATION_PIPELINE,
                resource_type=RESOURCES_MODELS_DIR_NAME,
            ))

        # Determine which JSON config to use based on HEF filename
        hef_name = Path(self.hef_path).name
        if INSTANCE_SEGMENTATION_MODEL_NAME_H8 in hef_name:
            self.config_file = get_resource_path(INSTANCE_SEGMENTATION_PIPELINE, RESOURCES_JSON_DIR_NAME , (INSTANCE_SEGMENTATION_MODEL_NAME_H8 + JSON_FILE_EXTENSION))
            print(f"Using config file: {self.config_file}")
        elif INSTANCE_SEGMENTATION_MODEL_NAME_H8L in hef_name:
            self.config_file = get_resource_path(INSTANCE_SEGMENTATION_PIPELINE, RESOURCES_JSON_DIR_NAME , (INSTANCE_SEGMENTATION_MODEL_NAME_H8L + JSON_FILE_EXTENSION))
        else:
            raise ValueError("HEF version not supported; please provide a compatible segmentation HEF or config file.")

        # Post-process shared object
        self.post_process_so = get_resource_path(INSTANCE_SEGMENTATION_PIPELINE, RESOURCES_SO_DIR_NAME, INSTANCE_SEGMENTATION_POSTPROCESS_SO_FILENAME)
        self.post_function_name = INSTANCE_SEGMENTATION_POSTPROCESS_FUNCTION

        # Callback
        self.app_callback = app_callback

        # Set process title for easy identification
        setproctitle.setproctitle(INSTANCE_SEGMENTATION_APP_TITLE)

        # Build the GStreamer pipeline
        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(video_source=self.video_source,
                                          video_width=self.video_width, video_height=self.video_height,
                                          frame_rate=self.frame_rate, sync=self.sync
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
