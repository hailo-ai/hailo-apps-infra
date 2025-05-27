# region imports
# Local application-specific imports
from hailo_apps_infra.hailo_core.hailo_common.base_ui_elements import BaseUIElements
# Third-party imports
from fastrtc import WebRTC
import gradio as gr
# endregion imports

class UIElements(BaseUIElements):
    """
    A class to hold references to all Gradio UI components.
    """
    def __init__(self):
        super().__init__()
        # Buttons
        self.start_btn = gr.Button("Start", variant="primary", elem_id="start-btn")
        self.stop_btn = gr.Button("Stop", variant="primary", elem_id="stop-btn")
        # Video Stream
        self.live_video_stream = WebRTC(modality="video", mode="receive", height="480px")

        # Embeddings
        self.embeddings_stream = gr.Plot(label="Embeddings Plot")

        # Sliders
        self.embedding_distance_tolerance = gr.Slider(
            minimum=0.0, maximum=1.0, value=0.1, label="Embedding Distance Tolerance", elem_id="embedding-distance-slider"
        )
        self.min_face_pixels_tolerance = gr.Slider(
            minimum=10000, maximum=100000, value=60000, label="Min Face Pixels Tolerance", elem_id="min-face-pixels-slider"
        )
        self.blurriness_tolerance = gr.Slider(
            minimum=0, maximum=1000, value=300, label="Blurriness Tolerance", elem_id="blurriness-slider"
        )
        self.max_faces_per_person = gr.Slider(
            minimum=1, maximum=10, value=3, label="Max Faces Per Person", elem_id="max-faces-slider"
        )
        self.last_image_sent_threshold_time = gr.Slider(
            minimum=0, maximum=10, value=1, label="Last Image Sent Threshold Time", elem_id="last-image-slider"
        )
        self.procrustes_distance_threshold = gr.Slider(
            minimum=0.0, maximum=1.0, value=0.3, label="Procrustes Distance Threshold", elem_id="procrustes-distance-slider"
        )
        # Text Areas
        self.detected_persons = gr.TextArea(label="Detected Persons", interactive=False, elem_id="detected-persons-textarea")  # ID for custom styling

        # css
        self.ui_css = """
        .center-text { 
            text-align: center; 
        } 
        .fixed-size { 
            width: 480px; 
            height: 360px; 
        } 
        /* Ensure consistent size for video and embeddings */ 
        .equal-size { 
            width: 100%; 
        } 
        .same-height { 
            height: 360px;  /* Set a consistent height for sliders and detected persons */ 
        } 
        .limited-height {
            max-height: 600px;  /* Set a maximum height */
            outline: none;  /* Remove the orange focus outline */
            box-shadow: none;  /* Remove any focus-related shadow */
        }
        /* Enable scrolling for the detected persons TextArea */
        #detected-persons-textarea textarea {
            overflow-y: scroll;  /* Enable vertical scrolling */
            max-height: 80px; /* Match the height of the sliders */
            outline: none;  /* Remove the orange focus outline */
            box-shadow: none;  /* Remove any focus-related shadow */
        }
        .generating {
            border: none;
        }
        """

# Define a custom theme
class CustomTheme(gr.themes.Default):
    def __init__(self):
        super().__init__()
        # Set the primary and secondary hues for the theme
        self.primary_hue = "rgb(66, 117, 233)"
        self.secondary_hue = "rgb(73, 175, 219)"
        
        # Set the font for all text
        self.font = "'Montserrat', sans-serif"
        
        # Customize button styles
        self.button_primary_background_fill = "linear-gradient(90deg, rgb(66, 117, 233) 0%, rgb(73, 175, 219) 100%)"
        self.button_primary_text_color = "white"
        self.button_primary_border_color = "transparent"
        self.button_primary_border_radius = "5px"

        # Add hover styles for buttons
        self.button_primary_background_fill_hover = "linear-gradient(90deg, rgb(73, 175, 219) 0%, rgb(66, 117, 233) 100%)"
        self.button_primary_text_color_hover = "white"