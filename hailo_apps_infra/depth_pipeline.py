from hailo_apps_infra.gstreamer_helper_pipelines import DISPLAY_PIPELINE, INFERENCE_PIPELINE, INFERENCE_PIPELINE_WRAPPER, SOURCE_PIPELINE, USER_CALLBACK_PIPELINE
from hailo_apps_infra.hailo_rpi_common import detect_hailo_arch, get_default_parser
from hailo_apps_infra.gstreamer_app import GStreamerApp
import setproctitle
import os
import gi

# User Gstreamer Application: This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDepthApp(GStreamerApp):
    def __init__(self, app_callback, user_data):
        gi.require_version('Gst', '1.0')
        parser = get_default_parser()
        parser.add_argument('--algo', default='fast_depth', help='Optional argument. What neural network to use for depth estimations: "fast_depth" (default) or "scdepthv3"')
        args = parser.parse_args()

        # Determine the architecture if not specified
        if args.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError('Could not auto-detect Hailo architecture. Please specify --arch manually.')
            self.arch = detected_arch
        else:
            self.arch = args.arch

        if args.algo not in ['fast_depth', 'scdepthv3']:
            raise ValueError('Please specify the depth estimation algorithm with argument "--algo" to one of: "fast_depth" or "scdepthv3" or renove the argument (will default to "fast_depth")')

        super().__init__(args, user_data)  # Call the parent class constructor
        self.app_callback = app_callback
        setproctitle.setproctitle("Hailo Depth App")  # Set the process title

        # Set the HEF file path & depth post processing method name based on the arch and depth algo
        if self.arch == "hailo8":
            if args.algo == "fast_depth":
                self.depth_hef_path = os.path.join(self.current_path, '../resources/fast_depth.hef')
                self.depth_post_function_name = "filter_fast_depth"
            elif args.algo == "scdepthv3":
                self.depth_hef_path = os.path.join(self.current_path, '../resources/scdepthv3.hef')
                self.depth_post_function_name = "filter_scdepth"
        else:  # hailo8l
            if args.algo == "fast_depth":
                self.depth_hef_path = os.path.join(self.current_path, '../resources/fast_depth_h8l.hef')
                self.depth_post_function_name = "filter_fast_depth"
            elif args.algo == "scdepthv3":
                self.depth_hef_path = os.path.join(self.current_path, '../resources/scdepthv3_h8l.hef')
                self.depth_post_function_name = "filter_scdepth"

        # Set the post-processing shared object file
        self.depth_post_process_so = os.path.join(self.current_path, '../resources/libdepth_postprocess.so')

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
