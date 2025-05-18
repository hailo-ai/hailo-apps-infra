import gi
gi.require_version('Gst', '1.0')
import setproctitle

from hailo_apps_infra.gstreamer.hailo_gstreamer.gstreamer_app import (
    app_callback_class,
    dummy_callback,
    GStreamerApp,
)
from hailo_apps_infra.gstreamer.hailo_gstreamer.gstreamer_helper_pipelines import (
    DISPLAY_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    SOURCE_PIPELINE,
    USER_CALLBACK_PIPELINE,
)
from hailo_apps_infra.common.hailo_common.core import get_default_parser, get_resource_path
from hailo_apps_infra.common.hailo_common.installation_utils import detect_hailo_arch
from hailo_apps_infra.common.hailo_common.defines import (
    DEPTH_POSTPROCESS_FUNCTION,
    RESOURCES_SO_DIR_NAME,
    DEPTH_POSTPROCESS_SO_FILENAME,
    RESOURCES_MODELS_DIR_NAME,
    DEPTH_PIPELINE,
    DEPTH_APP_TITLE,
)
# User Gstreamer Application: This class inherits from the common.GStreamerApp class
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
        setproctitle.setproctitle(DEPTH_APP_TITLE)  # Set the process title

        self.hef_path = get_resource_path(DEPTH_PIPELINE, RESOURCES_MODELS_DIR_NAME)
        self.post_process_so = get_resource_path(DEPTH_PIPELINE, RESOURCES_SO_DIR_NAME, DEPTH_POSTPROCESS_SO_FILENAME)
        self.post_function_name = DEPTH_POSTPROCESS_FUNCTION
        self.create_pipeline()

    def get_pipeline_string(self):
        source_pipeline = SOURCE_PIPELINE(self.video_source, self.video_width, self.video_height)
        depth_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
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

def main():
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDepthApp(app_callback, user_data)
    app.run()
    
if __name__ == "__main__":
    print("Starting Hailo Depth App...")
    main()