# region imports
# Standard library imports
import setproctitle
import json
import os

# Third-party imports
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Local application-specific imports
import hailo
from hailo_apps.hailo_app_python.core.common.core import get_default_parser, get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import TAPPAS_STREAM_ID_TOOL_SO_FILENAME, MULTI_SOURCE_APP_TITLE, SIMPLE_DETECTION_PIPELINE, RESOURCES_MODELS_DIR_NAME, RESOURCES_SO_DIR_NAME, DETECTION_POSTPROCESS_SO_FILENAME, DETECTION_POSTPROCESS_FUNCTION, TAPPAS_POSTPROC_PATH_KEY
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import get_source_type, USER_CALLBACK_PIPELINE, TRACKER_PIPELINE, QUEUE, SOURCE_PIPELINE, INFERENCE_PIPELINE, DISPLAY_PIPELINE
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import GStreamerApp, app_callback_class, dummy_callback
# endregion imports

# User Gstreamer Application: This class inherits from the common.GStreamerApp class
class GStreamerMultisourceApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):

        if parser == None:
            parser = get_default_parser()
        parser.add_argument("--sources", default='', help="The list of sources to use for the multisource pipeline, separated with comma e.g., /dev/video0,/dev/video1")
        parser.add_argument("--width", default=640, help="Video width (resolution) for ALL the sources. Default is 640.")
        parser.add_argument("--height", default=640, help="Video height (resolution) for ALL the sources. Default is 640.")

        super().__init__(parser, user_data)  # Call the parent class constructor

        setproctitle.setproctitle(MULTI_SOURCE_APP_TITLE)  # Set the process title

        self.hef_path = get_resource_path(SIMPLE_DETECTION_PIPELINE, RESOURCES_MODELS_DIR_NAME, self.arch)
        self.post_process_so = get_resource_path(SIMPLE_DETECTION_PIPELINE, RESOURCES_SO_DIR_NAME, self.arch, DETECTION_POSTPROCESS_SO_FILENAME)
        self.post_function_name = DETECTION_POSTPROCESS_FUNCTION
        self.video_sources_types = [(video_source, get_source_type(video_source)) for video_source in (self.options_menu.sources.split(',') if self.options_menu.sources else [self.video_source, self.video_source])]  # Default to 2 sources if none specified
        self.num_sources = len(self.video_sources_types)
        self.video_height = self.options_menu.height
        self.video_width = self.options_menu.width

        self.app_callback = app_callback
        self.generate_callbacks()
        self.create_pipeline()
        self.connect_src_callbacks()

    def get_pipeline_string(self):
        sources_string = ''
        router_string = ''

        tappas_post_process_dir = os.environ.get(TAPPAS_POSTPROC_PATH_KEY, '')
        set_stream_id_so = os.path.join(tappas_post_process_dir, TAPPAS_STREAM_ID_TOOL_SO_FILENAME)
        for id in range(self.num_sources):
            sources_string += SOURCE_PIPELINE(video_source=self.video_sources_types[id][0],
                                              video_width=self.video_width, video_height=self.video_height,
                                              frame_rate=self.frame_rate, sync=self.sync, name=f"source_{id}", no_webcam_compression=False)
            sources_string += f"! hailofilter name=set_src_{id} so-path={set_stream_id_so} config-path=src_{id} "
            sources_string += f"! robin.sink_{id} "
            router_string += f"router.src_{id} ! {USER_CALLBACK_PIPELINE(name=f'src_{id}_callback')} ! {QUEUE(name=f'callback_q_{id}')} ! {DISPLAY_PIPELINE(video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps, name=f'hailo_display_{id}')} "

        self.thresholds_str = (
            f"nms-score-threshold=0.3 "
            f"nms-iou-threshold=0.45 "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Create the detection pipeline
        detection_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            additional_params=self.thresholds_str)

        inference_string = f"hailoroundrobin mode=1 name=robin ! {detection_pipeline} ! {TRACKER_PIPELINE(class_id=-1)} ! {USER_CALLBACK_PIPELINE()} ! {QUEUE(name='call_q')} ! hailostreamrouter name=router "
        for id in range(self.num_sources):
            inference_string += f"src_{id}::input-streams=\"<sink_{id}>\" "

        pipeline_string = sources_string + inference_string + router_string
        print(pipeline_string)
        return pipeline_string

    def generate_callbacks(self):
        # Dynamically define callback functions per sources
        for id in range(self.num_sources):
            def callback_function(pad, info, user_data, id=id):  # roi.get_stream_id() == id
                buffer = info.get_buffer()
                if buffer is None:
                    return Gst.PadProbeReturn.OK
                roi = hailo.get_roi_from_buffer(buffer)
                detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
                for detection in detections:
                    track_id = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)[0].get_id()
                    print(f'{roi.get_stream_id()}_{detection.get_label()}_{track_id}')
                return Gst.PadProbeReturn.OK

            # Attach the callback function to the instance
            setattr(self, f'src_{id}_callback', callback_function)

    def connect_src_callbacks(self):
        for id in range(self.num_sources):
            identity = self.pipeline.get_by_name(f'src_{id}_callback')
            identity_pad = identity.get_static_pad(f'src')
            callback_function = getattr(self, f'src_{id}_callback', None)
            identity_pad.add_probe(Gst.PadProbeType.BUFFER, callback_function, self.user_data)

def main():
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerMultisourceApp(app_callback, user_data)
    app.run()

if __name__ == "__main__":
    print("Starting Hailo Multisource App...")
    main()