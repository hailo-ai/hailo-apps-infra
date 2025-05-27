# region imports
# Standard library imports
import datetime
from datetime import datetime
import threading
from pathlib import Path

# Third-party imports
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import gradio as gr

# Local application-specific imports
import hailo
from hailo_apps_infra.hailo_apps.hailo_gstreamer.gstreamer_app import app_callback_class
from hailo_apps_infra.hailo_apps.hailo_pipelines.face_recognition_pipeline import GStreamerFaceRecognitionApp
from hailo_apps_infra.hailo_core.hailo_common.telegram_handler import TelegramHandler
from hailo_apps_infra.hailo_core.hailo_common.core import get_resource_path
from hailo_apps_infra.hailo_core.hailo_common.defines import RESOURCES_PHOTOS_DIR_NAME, HAILO_LOGO_PHOTO_NAME
from face_ui_callbacks import UICallbacks
from face_ui_elements import UIElements, CustomTheme

# endregion

class user_callbacks_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.latest_track_id = -1
        self.detected_persons = []  # Store detected persons

        # Telegram settings as instance attributes
        self.telegram_enabled = False  # Set to True to enable Telegram notifications
        self.telegram_token = ''  # Add your Telegram bot token here
        self.telegram_chat_id = ''  # Add your Telegram chat ID here

        # Initialize TelegramHandler if Telegram is enabled
        self.telegram_handler = None
        if self.telegram_enabled and self.telegram_token and self.telegram_chat_id:
            self.telegram_handler = TelegramHandler(self.telegram_token, self.telegram_chat_id)

    # region Core application functions that are part of the main program logic and are called directly during pipeline execution, but are not GStreamer callback handlers themselves
    def send_notification(self, name, global_id, distance, frame):
        """
        Check if Telegram is enabled and send a notification via the TelegramHandler.
        """
        if not self.telegram_enabled or not self.telegram_handler:
            return

        # Check if the notification should be sent
        if self.telegram_handler.should_send_notification(global_id):
            self.telegram_handler.send_notification(name, global_id, distance, frame)
    # endregion

def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK
    user_data.increment()
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    for detection in detections:
        label = detection.get_label()
        detection_confidence = detection.get_confidence()
        if label == "face":
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) > 0:
                track_id = track[0].get_id()
            string_to_print = f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]: Face detection ID: {track_id} (Confidence: {detection_confidence:.1f}), '
            classifications = detection.get_objects_typed(hailo.HAILO_CLASSIFICATION)
            if len(classifications) > 0:
                for classification in classifications:
                    string_to_print += f'Person recognition: {classification.get_label()} (Confidence: {classification.get_confidence():.1f})'
                    if track_id > user_data.latest_track_id:
                        user_data.latest_track_id = track_id
                        if len(user_data.detected_persons) >= 10:
                            user_data.detected_persons.pop(0)  # Remove the oldest entry to maintain size
                        user_data.detected_persons.append(string_to_print)
    return Gst.PadProbeReturn.OK

# region wrappers to launch threads
def launch_stream_ui(ui):
    """
    Function to launch the stream UI.
    """
    ui.launch(allowed_paths=[Path(Path(__file__).parent, HAILO_LOGO_PHOTO_NAME)])

def run_app(app):
    """
    Function to run the GStreamer application in a separate thread.
    """
    app.run()
# endregion

def create_interface(ui_elements, ui_callbacks, pipeline):
    custom_theme = CustomTheme().set(
        loader_color="rgb(73, 175, 219)", 
        slider_color="rgb(73, 175, 219)")
    # UI elements to callbacks connection happens here because event listeners must be declared within gr.Blocks context
    with gr.Blocks(css=ui_elements.ui_css, theme=custom_theme) as interface:
        # region rendering
        with gr.Row():
            gr.Markdown("## Live Video Stream, Embeddings Visualization & Parameters tuning", elem_classes=["center-text"])
        # Row for buttons
        with gr.Row():
            ui_elements.start_btn.render()
            ui_elements.stop_btn.render()
            
        # Row for live video stream and embeddings_stream
        with gr.Row():
            with gr.Column(elem_classes=["fixed-size"]):  # Apply fixed size for live_video_stream
                ui_elements.live_video_stream.render()
            with gr.Column(elem_classes=["fixed-size"]):  # Apply fixed size for embeddings_stream
                ui_elements.embeddings_stream.render()
        
        # Row for sliders and detected persons
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    with gr.Column():
                        ui_elements.embedding_distance_tolerance.render()
                        ui_elements.min_face_pixels_tolerance.render()
                        ui_elements.blurriness_tolerance.render()
                    with gr.Column():
                        ui_elements.max_faces_per_person.render()
                        ui_elements.last_image_sent_threshold_time.render()
                        ui_elements.procrustes_distance_threshold.render()
            with gr.Column(elem_classes=["limited-height"]):  # Apply same-height class
                ui_elements.detected_persons.render()
        
        # Add the logo just above the footer
        # Define the original file and the alias (symlink) paths
        original_file = get_resource_path(pipeline_name=None, resource_type=RESOURCES_PHOTOS_DIR_NAME, model=HAILO_LOGO_PHOTO_NAME) 
        alias_file = Path(Path(__file__).parent, HAILO_LOGO_PHOTO_NAME)
        if not (alias_file.exists() or alias_file.is_symlink()):
            alias_file.symlink_to(original_file)
        with gr.Row():
            gr.HTML(
                f"""
                    <img src=/gradio_api/file={Path(Path(__file__).parent, HAILO_LOGO_PHOTO_NAME)} style="display: block; margin: 0 auto; max-width: 300px;">
                """
            )
        # endregion rendrering

        # region Event handlers: must be declared within gr.Blocks context
        ui_elements.live_video_stream.stream(  
            fn=ui_callbacks.process_frames,
            outputs=ui_elements.live_video_stream,
            trigger=ui_elements.start_btn.click
        )

        ui_elements.start_btn.click(
            fn=ui_callbacks.process_detected_persons,
            inputs=None,
            outputs=ui_elements.detected_persons
        )

        ui_elements.stop_btn.click(
            fn=ui_callbacks.stop_processing,
            inputs=None,
            outputs=None
        )

        if pipeline.options_menu.visualize:
            interface.load(
                fn=ui_callbacks.consume_plot_queue,
                inputs=None,
                outputs=ui_elements.embeddings_stream
            )

        # Dynamically adjust initial values for sliders from pipeline
        ui_elements.embedding_distance_tolerance.value = pipeline.embedding_distance_tolerance 
        ui_elements.min_face_pixels_tolerance.value = pipeline.min_face_pixels_tolerance
        ui_elements.blurriness_tolerance.value = pipeline.blurriness_tolerance
        ui_elements.max_faces_per_person.value = pipeline.max_faces_per_person
        ui_elements.last_image_sent_threshold_time.value = pipeline.last_image_sent_threshold_time
        ui_elements.procrustes_distance_threshold.value = pipeline.procrustes_distance_threshold

        ui_elements.embedding_distance_tolerance.change(ui_callbacks.on_embedding_distance_change, inputs=ui_elements.embedding_distance_tolerance)
        ui_elements.min_face_pixels_tolerance.change(ui_callbacks.on_min_face_pixels_change, inputs=ui_elements.min_face_pixels_tolerance)
        ui_elements.blurriness_tolerance.change(ui_callbacks.on_blurriness_change, inputs=ui_elements.blurriness_tolerance)
        ui_elements.max_faces_per_person.change(ui_callbacks.on_max_faces_change, inputs=ui_elements.max_faces_per_person)
        ui_elements.last_image_sent_threshold_time.change(ui_callbacks.on_last_image_time_change, inputs=ui_elements.last_image_sent_threshold_time)
        ui_elements.procrustes_distance_threshold.change(ui_callbacks.on_procrustes_distance_change, inputs=ui_elements.procrustes_distance_threshold)
        # endregion event handlers

    return interface

if __name__ == "__main__":   
    user_data = user_callbacks_class()
    pipeline = GStreamerFaceRecognitionApp(app_callback, user_data)  # appsink_callback argument provided anyway although in non UI interface where eventually not used - since here we don't have access to requested UI/CLI mode
    if pipeline.options_menu.mode == 'delete':  # always CLI even if mistakenly GUI mode is selected
        pipeline.db_handler.clear_table()
        print("All records deleted from the database")
        exit(0)
    elif pipeline.options_menu.mode == 'train':  # always CLI even if mistakenly GUI mode is selected
        pipeline.run()
        exit(0)
    elif not pipeline.options_menu.ui:  # must be then run in CLI interface
        pipeline.run()
    else:  # # must be then run in GUI interface
        ui_interface = create_interface(UIElements(), UICallbacks(pipeline), pipeline)  # create the Gradio interface: connect UI elements to callbacks
        # launch the stream UI in a separate thread from the Gstreamer pipeline
        ui_thread = threading.Thread(target=launch_stream_ui, args=(ui_interface,), daemon=False)
        ui_thread.start()
        ui_thread.join()  # otherwise not working