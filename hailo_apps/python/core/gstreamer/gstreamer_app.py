import multiprocessing
import os
import queue
import signal
import sys
import threading
from pathlib import Path
import cv2
import setproctitle

import gi
gi.require_version('Gtk', '3.0')
gi.require_version("Gst", "1.0")
from gi.repository import GLib, GObject, Gst, Gtk

# Suppress GStreamer buffer warnings by installing a custom log handler
# These warnings are cosmetic in GStreamer 1.26+ with complex pipelines
_suppressed_gstreamer_patterns = ["write map requested on non-writable buffer"]

def _gstreamer_log_filter(log_domain, log_level, message, user_data):
    """
    Custom GLib log handler that filters out specific GStreamer warnings.

    This handler suppresses cosmetic warnings that appear in GStreamer 1.26+ when
    complex pipelines (like instance segmentation) use buffers with multiple references.
    These warnings don't indicate functional problems - GStreamer handles them internally.
    """
    # Suppress messages containing our specific patterns
    if message and not any(pattern in message for pattern in _suppressed_gstreamer_patterns):
        # For non-suppressed messages, use default behavior (print to stderr)
        if log_level & (GLib.LogLevelFlags.LEVEL_ERROR | GLib.LogLevelFlags.LEVEL_CRITICAL):
            sys.stderr.write(f"({log_domain}): CRITICAL: {message}\n")
            sys.stderr.flush()

# Install the custom log handler for all GStreamer logs
GLib.log_set_handler("GStreamer", GLib.LogLevelFlags.LEVEL_MASK, _gstreamer_log_filter, None)

from hailo_apps.python.core.common.buffer_utils import (
    get_caps_from_pad,
    get_numpy_from_buffer,
)
from hailo_apps.python.core.common.camera_utils import (
    get_usb_video_devices,
)
from hailo_apps.python.core.common.core import (
    load_environment,
)
from hailo_apps.python.core.common.installation_utils import detect_hailo_arch


# Absolute imports for your common utilities
from hailo_apps.python.core.common.defines import (
    BASIC_PIPELINES_VIDEO_EXAMPLE_NAME,
    GST_VIDEO_SINK,
    HAILO_ARCH_KEY,
    HAILO_RGB_VIDEO_FORMAT,
    RESOURCES_ROOT_PATH_DEFAULT,
    RESOURCES_VIDEOS_DIR_NAME,
    RPI_NAME_I,
    TAPPAS_POSTPROC_PATH_KEY,
    USB_CAMERA,
)
from hailo_apps.python.core.common.hailo_logger import get_logger

# python/core/gstreamer/gstreamer_app.py
# Absolute import for your local helper
from hailo_apps.python.core.gstreamer.gstreamer_helper_pipelines import (
    get_source_type,
)

hailo_logger = get_logger(__name__)

try:
    from picamera2 import Picamera2
except ImportError:
    pass

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
class app_callback_class:
    def __init__(self):
        hailo_logger.debug("Initializing app_callback_class")
        self.frame_count = 0
        self.use_frame = False
        self.frame_queue = multiprocessing.Queue(maxsize=3)
        self.running = True

    def increment(self):
        self.frame_count += 1
        hailo_logger.debug(f"Frame count incremented to {self.frame_count}")

    def get_count(self):
        hailo_logger.debug(f"Returning frame count: {self.frame_count}")
        return self.frame_count

    def set_frame(self, frame):
        if not self.frame_queue.full():
            hailo_logger.debug("Adding frame to queue")
            self.frame_queue.put(frame)
        else:
            hailo_logger.warning("Frame queue is full; dropping frame.")

    def get_frame(self):
        if not self.frame_queue.empty():
            hailo_logger.debug("Retrieving frame from queue")
            return self.frame_queue.get()
        else:
            hailo_logger.debug("Frame queue is empty")
            return None


def dummy_callback(pad, info, user_data):
    hailo_logger.debug("dummy_callback invoked; doing nothing.")
    return Gst.PadProbeReturn.OK


# -----------------------------------------------------------------------------------------------
# GStreamerApp class
# -----------------------------------------------------------------------------------------------
class GStreamerApp:
    def __init__(self, args, user_data: app_callback_class):
        hailo_logger.debug("Initializing GStreamerApp")
        setproctitle.setproctitle("Hailo Python App")

        self.options_menu = args.parse_args()
        hailo_logger.debug(f"Parsed CLI options: {self.options_menu}")

        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                hailo_logger.error("Could not auto-detect Hailo architecture.")
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            hailo_logger.info(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch
            hailo_logger.info(f"Using user-specified architecture: {self.arch}")

        signal.signal(signal.SIGINT, self.shutdown)

        env_file = os.environ.get("HAILO_ENV_FILE")
        hailo_logger.debug(f"Loading environment from {env_file}")
        load_environment(env_file)

        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            arch = os.getenv(HAILO_ARCH_KEY, detect_hailo_arch())
            if not arch:
                hailo_logger.error("Could not detect Hailo architecture.")
                raise ValueError(
                    "Could not auto-detect Hailo architecture. Please specify --arch manually."
                )
            self.arch = arch
            hailo_logger.debug(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch
            hailo_logger.debug("Using user-specified arch: %s", self.arch)

        tappas_post_process_dir = Path(os.environ.get(TAPPAS_POSTPROC_PATH_KEY, ""))
        if tappas_post_process_dir == "":
            hailo_logger.error("TAPPAS_POST_PROC_DIR environment variable not set.")
            print(
                "TAPPAS_POST_PROC_DIR environment variable is not set. Please set it by running set-env in cli"
            )
            exit(1)

        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.postprocess_dir = tappas_post_process_dir

        if self.options_menu.input is None:
            self.video_source = str(
                Path(RESOURCES_ROOT_PATH_DEFAULT)
                / RESOURCES_VIDEOS_DIR_NAME
                / BASIC_PIPELINES_VIDEO_EXAMPLE_NAME
            )
        else:
            self.video_source = self.options_menu.input

        if self.video_source == USB_CAMERA:
            hailo_logger.debug("USB_CAMERA detected; scanning USB devices...")
            self.video_source = get_usb_video_devices()
            if not self.video_source:
                hailo_logger.error("No USB camera found for '--input usb'")
                print(
                    'Provided argument "--input" is set to "usb", however no available USB cameras found. Please connect a camera or specifiy different input method.'
                )
                exit(1)
            else:
                hailo_logger.debug(f"Using USB camera: {self.video_source[0]}")
                self.video_source = self.video_source[0]

        self.source_type = get_source_type(self.video_source)
        hailo_logger.debug(f"Source type determined: {self.source_type}")

        self.frame_rate = self.options_menu.frame_rate
        self.user_data = user_data
        self.video_sink = GST_VIDEO_SINK
        self.pipeline = None
        self.loop = None
        self.threads = []
        self.error_occurred = False
        self.pipeline_latency = 300

        # Handle batch-size from parser (default: 1)
        self.batch_size = getattr(self.options_menu, 'batch_size', 1)
        
        # Handle width/height from parser (defaults: 1280x720)
        # Check for None explicitly since getattr returns None if attribute exists but is None
        width = getattr(self.options_menu, 'width', None)
        self.video_width = width if width is not None else 1280
        height = getattr(self.options_menu, 'height', None)
        self.video_height = height if height is not None else 720
        
        self.video_format = HAILO_RGB_VIDEO_FORMAT
        
        # Handle hef-path from parser (default: None, apps can override)
        self.hef_path = getattr(self.options_menu, 'hef_path', None)
        
        self.app_callback = None

        user_data.use_frame = self.options_menu.use_frame

        self.sync = (
            "true" if (self.source_type == "file" and not self.options_menu.disable_sync) else "false"
        )
        self.show_fps = self.options_menu.show_fps

        if self.options_menu.dump_dot:
            hailo_logger.debug("Dump DOT enabled")
            os.environ["GST_DEBUG_DUMP_DOT_DIR"] = os.getcwd()

        self.webrtc_frames_queue = None

    def appsink_callback(self, appsink):
        hailo_logger.debug("appsink_callback triggered")
        sample = appsink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            if buffer:
                format, width, height = get_caps_from_pad(appsink.get_static_pad("sink"))
                hailo_logger.debug(f"Buffer received: format={format}, size={width}x{height}")
                frame = get_numpy_from_buffer(buffer, format, width, height)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    self.webrtc_frames_queue.put(frame)
                except queue.Full:
                    hailo_logger.warning("Frame queue full; dropping frame")
                    print("Frame queue is full. Dropping frame.")
        return Gst.FlowReturn.OK

    def on_fps_measurement(self, sink, fps, droprate, avgfps):
        hailo_logger.debug(f"FPS measurement: {fps:.2f}, drop={droprate:.2f}, avg={avgfps:.2f}")
        print(f"FPS: {fps:.2f}, Droprate: {droprate:.2f}, Avg FPS: {avgfps:.2f}")
        return True

    def create_pipeline(self):
        hailo_logger.debug("Creating pipeline...")
        Gst.init(None)
        pipeline_string = self.get_pipeline_string()
        hailo_logger.debug(f"Pipeline string: {pipeline_string}")
        try:
            self.pipeline = Gst.parse_launch(pipeline_string)
        except Exception as e:
            hailo_logger.error(f"Error creating pipeline: {e}")
            print(f"Error creating pipeline: {e}", file=sys.stderr)
            sys.exit(1)

        if self.show_fps:
            hailo_logger.debug("Connecting FPS measurement callback")
            self.pipeline.get_by_name("hailo_display").connect(
                "fps-measurements", self.on_fps_measurement
            )

        self.loop = GLib.MainLoop()

    def bus_call(self, bus, message, loop):
        t = message.type
        hailo_logger.debug(f"Bus message received: {t}")
        if t == Gst.MessageType.EOS:
            hailo_logger.debug("End of Stream")
            print("End-of-stream")
            self.on_eos()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            hailo_logger.error(f"GStreamer Error: {err}, debug: {debug}")
            print(f"Error: {err}, {debug}", file=sys.stderr)
            self.error_occurred = True
            self.shutdown()
        elif t == Gst.MessageType.QOS:
            if not hasattr(self, "qos_count"):
                self.qos_count = 0
            self.qos_count += 1
            # Only log every 100th QoS message to avoid spam
            # QoS messages are normal during pipeline rebuild/startup
            if self.qos_count % 100 == 0:
                qos_element = message.src.get_name()
                hailo_logger.warning(f"QoS messages: {self.qos_count} total (from {qos_element})")
                print(f"\033[93mQoS messages: {self.qos_count} total\033[0m")
        return True

    def on_eos(self):
        hailo_logger.debug("on_eos() called")
        if self.source_type == "file":
            hailo_logger.debug("File source detected; rebuilding pipeline")
            print("End-of-stream reached. Rebuilding pipeline...")
            # Use GLib.idle_add to defer pipeline rebuild and avoid blocking
            GLib.idle_add(self._rebuild_pipeline)
        else:
            hailo_logger.debug("Non-file source detected; shutting down")
            self.shutdown()

    def _rebuild_pipeline(self):
        """
        Completely rebuild the pipeline from scratch for clean looping.

        This destroys the old pipeline object and creates a new one,
        which is the only truly clean way to loop with stateful elements like trackers.

        Returns:
            False to remove this idle callback after execution.
        """
        hailo_logger.debug("_rebuild_pipeline() executing")

        try:
            # Step 1: Stop and destroy the old pipeline
            hailo_logger.debug("Stopping old pipeline")
            if self.pipeline:
                self.pipeline.set_state(Gst.State.NULL)
                # Wait briefly for NULL state
                self.pipeline.get_state(2 * Gst.SECOND)
                # Remove bus watch
                bus = self.pipeline.get_bus()
                bus.remove_signal_watch()
                # Dereference the pipeline
                self.pipeline = None

            hailo_logger.debug("Old pipeline destroyed")

            # Small delay to ensure all resources are released
            import time
            time.sleep(0.2)

            # Step 2: Rebuild the pipeline from scratch
            hailo_logger.debug("Creating new pipeline")
            pipeline_string = self.get_pipeline_string()
            hailo_logger.debug(f"New pipeline string: {pipeline_string}")

            self.pipeline = Gst.parse_launch(pipeline_string)

            # Step 3: Reattach bus callback
            hailo_logger.debug("Reattaching bus callback")
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.bus_call, self.loop)

            # Step 4: Reattach pad probe if needed
            if not self.options_menu.disable_callback:
                identity = self.pipeline.get_by_name("identity_callback")
                if identity:
                    hailo_logger.debug("Reattaching pad probe to identity_callback")
                    identity.get_static_pad("src").add_probe(
                        Gst.PadProbeType.BUFFER, self.app_callback, self.user_data
                    )

            # Step 5: Start the new pipeline
            hailo_logger.debug("Starting new pipeline")
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                hailo_logger.error("Failed to start new pipeline")
                print("Error: Failed to start new pipeline.", file=sys.stderr)
                self.loop.quit()
                return False

            hailo_logger.debug("Pipeline rebuilt and restarted successfully")
            print("Pipeline rebuilt successfully.")

        except Exception as e:
            hailo_logger.error(f"Exception during pipeline rebuild: {e}")
            print(f"Error rebuilding pipeline: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self.loop.quit()

        # Return False to remove this idle callback
        return False

    def shutdown(self, signum=None, frame=None):
        hailo_logger.warning("Shutdown initiated")
        print("Shutting down... Hit Ctrl-C again to force quit.")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.pipeline.set_state(Gst.State.PAUSED)
        GLib.usleep(100000)

        self.pipeline.set_state(Gst.State.READY)
        GLib.usleep(100000)

        self.pipeline.set_state(Gst.State.NULL)
        GLib.idle_add(self.loop.quit)

    def update_fps_caps(self, new_fps=30, source_name="source"):
        hailo_logger.debug(
            "update_fps_caps() called with new_fps=%s, source_name=%s", new_fps, source_name
        )
        videorate_name = f"{source_name}_videorate"
        capsfilter_name = f"{source_name}_fps_caps"

        videorate = self.pipeline.get_by_name(videorate_name)
        if videorate is None:
            hailo_logger.error(f"Element {videorate_name} not found")
            print(f"Element {videorate_name} not found in the pipeline.")
            return

        current_max_rate = videorate.get_property("max-rate")
        hailo_logger.debug(f"Current max-rate: {current_max_rate}")
        videorate.set_property("max-rate", new_fps)
        updated_max_rate = videorate.get_property("max-rate")
        hailo_logger.debug(f"Updated max-rate to {updated_max_rate}")

        capsfilter = self.pipeline.get_by_name(capsfilter_name)
        if capsfilter:
            new_caps_str = f"video/x-raw, framerate={new_fps}/1"
            hailo_logger.debug(f"Updating capsfilter to: {new_caps_str}")
            capsfilter.set_property("caps", Gst.Caps.from_string(new_caps_str))
            print("Updated capsfilter caps to match new rate")

        self.frame_rate = new_fps

    def get_pipeline_string(self):
        hailo_logger.debug("get_pipeline_string() called (should be overridden)")
        return ""

    def dump_dot_file(self):
        hailo_logger.debug("Dumping GStreamer dot file")
        print("Dumping dot file...")
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, "pipeline")
        return False

    def run(self):
        hailo_logger.debug("Running GStreamerApp main loop")
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)

        if not self.options_menu.disable_callback:
            identity = self.pipeline.get_by_name("identity_callback")
            if identity is None:
                hailo_logger.warning("identity_callback not found in pipeline")
                print("Warning: identity_callback element not found...")
            else:
                hailo_logger.debug("Adding pad probe to identity_callback")
                identity.get_static_pad("src").add_probe(
                    Gst.PadProbeType.BUFFER, self.app_callback, self.user_data
                )

        hailo_display = self.pipeline.get_by_name("hailo_display")
        if hailo_display is None and not getattr(self.options_menu, "ui", False):
            hailo_logger.warning("hailo_display not found in pipeline")
            print("Warning: hailo_display element not found...")

        disable_qos(self.pipeline)

        if self.options_menu.use_frame:
            hailo_logger.debug("Starting display_user_data_frame process")
            display_process = multiprocessing.Process(
                target=display_user_data_frame, args=(self.user_data,)
            )
            display_process.start()

        if self.source_type == RPI_NAME_I:
            hailo_logger.debug("Starting picamera_thread")
            picam_thread = threading.Thread(
                target=picamera_thread,
                args=(self.pipeline, self.video_width, self.video_height, self.video_format),
            )
            self.threads.append(picam_thread)
            picam_thread.start()

        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_latency(self.pipeline_latency * Gst.MSECOND)
        self.pipeline.set_state(Gst.State.PLAYING)

        if self.options_menu.dump_dot:
            GLib.timeout_add_seconds(3, self.dump_dot_file)

        self.loop.run()
        # Gtk.main()

        try:
            hailo_logger.debug("Cleaning up after loop exit")
            self.user_data.running = False
            self.pipeline.set_state(Gst.State.NULL)
            if self.options_menu.use_frame:
                display_process.terminate()
                display_process.join()
            for t in self.threads:
                t.join()
        except Exception as e:
            hailo_logger.error(f"Error during cleanup: {e}")
            print(f"Error during cleanup: {e}", file=sys.stderr)
        finally:
            if self.error_occurred:
                hailo_logger.error("Exiting with error")
                print("Exiting with error...", file=sys.stderr)
                sys.exit(1)
            else:
                hailo_logger.debug("Exiting successfully")
                print("Exiting...")
                sys.exit(0)


def picamera_thread(pipeline, video_width, video_height, video_format, picamera_config=None):
    hailo_logger.debug("picamera_thread started")
    appsrc = pipeline.get_by_name("app_source")
    appsrc.set_property("is-live", True)
    appsrc.set_property("format", Gst.Format.TIME)
    print("appsrc properties: ", appsrc)

    with Picamera2() as picam2:
        if picamera_config is None:
            main = {"size": (1280, 720), "format": "RGB888"}
            lores = {"size": (video_width, video_height), "format": "RGB888"}
            controls = {"FrameRate": 30}
            config = picam2.create_preview_configuration(main=main, lores=lores, controls=controls)
        else:
            config = picamera_config

        picam2.configure(config)
        lores_stream = config["lores"]
        format_str = "RGB" if lores_stream["format"] == "RGB888" else video_format
        width, height = lores_stream["size"]
        hailo_logger.debug(f"Picamera2 config: width={width}, height={height}, format={format_str}")

        appsrc.set_property(
            "caps",
            Gst.Caps.from_string(
                f"video/x-raw, format={format_str}, width={width}, height={height}, framerate=30/1, pixel-aspect-ratio=1/1"
            ),
        )
        picam2.start()
        frame_count = 0
        print("picamera_process started")

        while True:
            frame_data = picam2.capture_array("lores")
            if frame_data is None:
                hailo_logger.error("Failed to capture frame")
                print("Failed to capture frame.")
                break

            frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
            buffer = Gst.Buffer.new_wrapped(frame.tobytes())
            buffer_duration = Gst.util_uint64_scale_int(1, Gst.SECOND, 30)
            buffer.pts = frame_count * buffer_duration
            buffer.duration = buffer_duration
            ret = appsrc.emit("push-buffer", buffer)

            if ret == Gst.FlowReturn.FLUSHING:
                hailo_logger.warning("Pipeline flushing; stopping picamera_thread")
                break
            if ret != Gst.FlowReturn.OK:
                hailo_logger.error(f"Failed to push buffer: {ret}")
                break
            frame_count += 1


def disable_qos(pipeline):
    hailo_logger.debug("disable_qos() called")
    if not isinstance(pipeline, Gst.Pipeline):
        hailo_logger.error("Provided object is not a GStreamer Pipeline")
        print("The provided object is not a GStreamer Pipeline")
        return

    it = pipeline.iterate_elements()
    while True:
        result, element = it.next()
        if result != Gst.IteratorResult.OK:
            break

        if "qos" in GObject.list_properties(element):
            element.set_property("qos", False)
            hailo_logger.debug(f"Set qos=False for {element.get_name()}")
            print(f"Set qos to False for {element.get_name()}")


def display_user_data_frame(user_data: app_callback_class):
    hailo_logger.debug("display_user_data_frame() started")
    while user_data.running:
        frame = user_data.get_frame()
        if frame is not None:
            hailo_logger.debug("Displaying user frame")
            cv2.imshow("User Frame", frame)
        cv2.waitKey(1)
    hailo_logger.debug("display_user_data_frame() exiting")
    cv2.destroyAllWindows()
