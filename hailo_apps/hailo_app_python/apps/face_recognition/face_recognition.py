# region imports
# Standard library imports
import datetime
from datetime import datetime

# Third-party imports
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Local application-specific imports
import hailo
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.face_recognition.face_recognition_pipeline import GStreamerFaceRecognitionApp
from hailo_apps.hailo_app_python.core.common.telegram_handler import TelegramHandler
from hailo_apps.hailo_app_python.core.common.defines import HAILO_LOGO_PHOTO_NAME
# endregion

# region Constants
TELEGRAM_ENABLED = False  # Enable Telegram notifications
TELEGRAM_TOKEN = ''  # Telegram bot token
TELEGRAM_CHAT_ID = ''  # Telegram chat ID
# endregion

class user_callbacks_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.latest_track_id = -1

        # Telegram settings as instance attributes
        self.telegram_enabled = TELEGRAM_ENABLED
        self.telegram_token = TELEGRAM_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID

        # Initialize TelegramHandler if Telegram is enabled
        self.telegram_handler = None
        if self.telegram_enabled and self.telegram_token and self.telegram_chat_id:
            self.telegram_handler = TelegramHandler(self.telegram_token, self.telegram_chat_id)

    # region Core application functions that are part of the main program logic and are called directly during pipeline execution, but are not GStreamer callback handlers themselves
    def send_notification(self, name, global_id, confidence, frame):
        """
        Check if Telegram is enabled and send a notification via the TelegramHandler.
        """
        if not self.telegram_enabled or not self.telegram_handler:
            return

        # Check if the notification should be sent
        if self.telegram_handler.should_send_notification(global_id):
            self.telegram_handler.send_notification(name, global_id, confidence, frame)
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
                    if classification.get_label() == 'Unknown':
                        string_to_print += 'Unknown person detected'
                    else:
                        string_to_print += f'Person recognition: {classification.get_label()} (Confidence: {classification.get_confidence():.1f})'
                    if track_id > user_data.latest_track_id:
                        user_data.latest_track_id = track_id
                        print(string_to_print)
    return Gst.PadProbeReturn.OK

def main():  
    user_data = user_callbacks_class()
    pipeline = GStreamerFaceRecognitionApp(app_callback, user_data)  # appsink_callback argument provided anyway although in non UI interface where eventually not used - since here we don't have access to requested UI/CLI mode
    if pipeline.options_menu.mode == 'delete':
        pipeline.db_handler.clear_table()
        exit(0)
    elif pipeline.options_menu.mode == 'train':
        pipeline.run()
        exit(0)
    else:  # 'run' mode
        pipeline.run()

if __name__ == "__main__": 
    main()