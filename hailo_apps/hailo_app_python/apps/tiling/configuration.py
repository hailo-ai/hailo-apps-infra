# region imports
# Standard library imports
from pathlib import Path
from typing import Optional, Tuple

# Local application-specific imports
from hailo_apps.hailo_app_python.core.common.defines import (
    TILING_VIDEO_EXAMPLE_NAME,
    TILING_YOLO_POSTPROCESS_SO_FILENAME,
    TILING_MOBILENET_POSTPROCESS_SO_FILENAME,
    TILING_YOLO_MODEL_NAME_H8,
    TILING_YOLO_MODEL_NAME_H8L,
    TILING_MOBILENET_MODEL_NAME_H8,
    TILING_MOBILENET_MODEL_NAME_H8L,
    TILING_DEFAULT_MODEL_TYPE,
    TILING_DEFAULT_MODEL_INPUT_SIZE,
    TILING_YOLO_POSTPROCESS_FUNCTION,
    TILING_YOLO_DEFAULT_MODEL_INPUT_SIZE,
    TILING_MOBILENET_DEFAULT_MODEL_INPUT_SIZE,
    TILING_MOBILENET_POSTPROCESS_FUNCTION,
    RESOURCES_SO_DIR_NAME,
    RESOURCES_MODELS_DIR_NAME,
    RESOURCES_VIDEOS_DIR_NAME,
    RESOURCES_ROOT_PATH_DEFAULT,
    BASIC_PIPELINES_VIDEO_EXAMPLE_NAME,
    USB_CAMERA,
)
from hailo_apps.hailo_app_python.core.common.core import get_resource_path
from hailo_apps.hailo_app_python.core.common.hailo_logger import get_logger
from hailo_apps.hailo_app_python.core.common.camera_utils import get_usb_video_devices
from .tile_calculator import calculate_auto_tiles, calculate_manual_tiles_overlap

hailo_logger = get_logger(__name__)
# endregion imports


def detect_model_config_from_hef(hef_path: str) -> Tuple[str, int, str]:
    """
    Automatically detect model configuration from HEF filename.

    Args:
        hef_path: Path to the HEF file

    Returns:
        tuple: (model_type, input_size, postprocess_function)
    """
    if hef_path is None:
        return TILING_DEFAULT_MODEL_TYPE, TILING_DEFAULT_MODEL_INPUT_SIZE, TILING_YOLO_POSTPROCESS_FUNCTION

    hef_name = Path(hef_path).name.lower()

    # If filename contains 'mobilenet', use MobileNetSSD defaults
    if 'mobilenet' in hef_name:
        return "mobilenet", TILING_MOBILENET_DEFAULT_MODEL_INPUT_SIZE, TILING_MOBILENET_POSTPROCESS_FUNCTION

    # Otherwise, use YOLO defaults
    return "yolo", TILING_YOLO_DEFAULT_MODEL_INPUT_SIZE, TILING_YOLO_POSTPROCESS_FUNCTION


class TilingConfiguration:
    """Configuration manager for tiling application."""

    def __init__(self, options_menu, video_width: int, video_height: int, arch: str):
        """
        Initialize tiling configuration.

        Args:
            options_menu: Parsed command line arguments
            video_width: Input video width
            video_height: Input video height
            arch: Hailo architecture (hailo8 or hailo8l)
        """
        self.options_menu = options_menu
        self.video_width = video_width
        self.video_height = video_height
        self.arch = arch

        # Set video source
        self._configure_video_source()

        # Set HEF path and model configuration
        self._configure_model()

        # Configure tiling parameters
        self._configure_tiling()

        # Configure multi-scale settings
        self._configure_multi_scale()

        # Configure detection parameters
        self._configure_detection()

    def _configure_video_source(self) -> None:
        """Configure video source based on options."""
        if self.options_menu.input is None:
            if self.options_menu.general_detection:
                # Use standard detection video for general detection mode
                self.video_source = str(
                    Path(RESOURCES_ROOT_PATH_DEFAULT)
                    / RESOURCES_VIDEOS_DIR_NAME
                    / BASIC_PIPELINES_VIDEO_EXAMPLE_NAME
                )
                hailo_logger.info(f"Using default detection video for general detection: {self.video_source}")
            else:
                # Use VisDrone video for aerial detection mode
                self.video_source = str(
                    Path(RESOURCES_ROOT_PATH_DEFAULT)
                    / RESOURCES_VIDEOS_DIR_NAME
                    / TILING_VIDEO_EXAMPLE_NAME
                )
                hailo_logger.info(f"Using default tiling video: {self.video_source}")
        else:
            # Handle USB camera input like the parent GStreamerApp class
            if self.options_menu.input == USB_CAMERA:
                hailo_logger.debug("USB_CAMERA detected; scanning USB devices...")
                usb_devices = get_usb_video_devices()
                if not usb_devices:
                    hailo_logger.error("No USB camera found for '--input usb'")
                    raise ValueError(
                        'Provided argument "--input" is set to "usb", however no available USB cameras found. Please connect a camera or specify different input method.'
                    )
                else:
                    hailo_logger.debug(f"Using USB camera: {usb_devices[0]}")
                    self.video_source = usb_devices[0]
            else:
                self.video_source = self.options_menu.input

    def _configure_model(self) -> None:
        """Configure model path and auto-detect model type."""
        # Set HEF path
        if self.options_menu.hef_path is not None:
            self.hef_path = self.options_menu.hef_path
            hailo_logger.info(f"Using user-specified HEF: {self.hef_path}")
        elif self.options_menu.general_detection:
            # Use YOLO model for general detection
            default_model_name = TILING_YOLO_MODEL_NAME_H8 if self.arch == "hailo8" else TILING_YOLO_MODEL_NAME_H8L
            self.hef_path = get_resource_path(
                pipeline_name=None,
                resource_type=RESOURCES_MODELS_DIR_NAME,
                arch=self.arch,
                model=default_model_name
            )
            hailo_logger.info(f"Using YOLO model for general detection: {self.hef_path}")
        else:
            # Use default VisDrone MobileNetSSD model
            default_model_name = TILING_MOBILENET_MODEL_NAME_H8 if self.arch == "hailo8" else TILING_MOBILENET_MODEL_NAME_H8L
            self.hef_path = get_resource_path(
                pipeline_name=None,
                resource_type=RESOURCES_MODELS_DIR_NAME,
                arch=self.arch,
                model=default_model_name
            )
            hailo_logger.info(f"Using default VisDrone MobileNetSSD HEF: {self.hef_path}")

        # Validate HEF path exists
        if self.hef_path is None or not Path(self.hef_path).exists():
            hailo_logger.error(f"HEF path is invalid or missing: {self.hef_path}")
            raise ValueError(f"HEF file not found: {self.hef_path}")

        # Auto-detect model configuration from HEF filename
        self.model_type, self.model_input_size, self.post_function = detect_model_config_from_hef(self.hef_path)
        hailo_logger.info(f"Auto-detected: {self.model_type} ({self.model_input_size}x{self.model_input_size}) - {self.post_function}")

        # Set post-processing resources
        postprocess_so_filename = (TILING_MOBILENET_POSTPROCESS_SO_FILENAME if self.model_type == "mobilenet"
                                 else TILING_YOLO_POSTPROCESS_SO_FILENAME)
        self.post_process_so = get_resource_path(
            pipeline_name=None,
            resource_type=RESOURCES_SO_DIR_NAME,
            arch=self.arch,
            model=postprocess_so_filename
        )

    def _configure_tiling(self) -> None:
        """Configure tiling parameters."""
        # Store and validate minimum overlap
        self.min_overlap = self.options_menu.min_overlap
        if self.min_overlap < 0.0 or self.min_overlap > 0.5:
            hailo_logger.warning(
                f"min_overlap {self.min_overlap} is out of range [0.0, 0.5]. "
                f"Clamping to valid range."
            )
            self.min_overlap = max(0.0, min(0.5, self.min_overlap))

        hailo_logger.info(
            f"Minimum overlap set to {self.min_overlap:.2%} "
            f"({int(self.min_overlap * self.model_input_size)}px)"
        )

        # Configure single-scale tiling
        self._configure_single_scale_tiling()

    def _configure_single_scale_tiling(self) -> None:
        """Configure tiling parameters for single-scale mode (auto or manual)."""
        # Check if manual mode (user specified tiles-x or tiles-y)
        user_tiles_x = self.options_menu.tiles_x
        user_tiles_y = self.options_menu.tiles_y

        if user_tiles_x is not None or user_tiles_y is not None:
            # Manual mode
            self.tiling_mode = "manual"

            # If only one dimension specified, auto-calculate the other
            if user_tiles_x is None:
                # Auto-calculate tiles_x based on tiles_y
                auto_tiles_x, _, _, _ = calculate_auto_tiles(
                    self.video_width, self.video_height, self.model_input_size, self.min_overlap
                )
                self.tiles_x = auto_tiles_x
                self.tiles_y = user_tiles_y
            elif user_tiles_y is None:
                # Auto-calculate tiles_y based on tiles_x
                _, auto_tiles_y, _, _ = calculate_auto_tiles(
                    self.video_width, self.video_height, self.model_input_size, self.min_overlap
                )
                self.tiles_x = user_tiles_x
                self.tiles_y = auto_tiles_y
            else:
                # Both specified
                self.tiles_x = user_tiles_x
                self.tiles_y = user_tiles_y

            # Calculate overlap for manual tile counts
            self.overlap_x, self.overlap_y, tile_size_x, tile_size_y = calculate_manual_tiles_overlap(
                self.video_width, self.video_height,
                self.tiles_x, self.tiles_y,
                self.model_input_size,
                self.min_overlap
            )

            # Check if we needed larger tiles to meet minimum overlap
            self.tile_size_x = tile_size_x
            self.tile_size_y = tile_size_y
            self.used_larger_tiles = (tile_size_x > self.model_input_size or tile_size_y > self.model_input_size)

            if self.used_larger_tiles:
                hailo_logger.info(
                    f"Manual tiling: {self.tiles_x}x{self.tiles_y} tiles "
                    f"(tile size: {int(tile_size_x)}x{int(tile_size_y)} to meet min overlap)"
                )
            else:
                hailo_logger.info(f"Manual tiling: {self.tiles_x}x{self.tiles_y} tiles")
        else:
            # Auto mode
            self.tiling_mode = "auto"
            self.tiles_x, self.tiles_y, self.overlap_x, self.overlap_y = calculate_auto_tiles(
                self.video_width, self.video_height, self.model_input_size, self.min_overlap
            )
            # In auto mode, tiles are always model input size
            self.tile_size_x = self.model_input_size
            self.tile_size_y = self.model_input_size
            self.used_larger_tiles = False
            hailo_logger.info(f"Auto tiling: {self.tiles_x}x{self.tiles_y} tiles (min overlap {self.min_overlap:.1%})")

        # Validate tile counts are within hardware limits (1-20)
        if self.tiles_x < 1 or self.tiles_x > 20:
            hailo_logger.error(f"tiles_x={self.tiles_x} is out of range [1, 20]")
            raise ValueError(f"Number of tiles in X direction must be between 1 and 20, got {self.tiles_x}")
        if self.tiles_y < 1 or self.tiles_y > 20:
            hailo_logger.error(f"tiles_y={self.tiles_y} is out of range [1, 20]")
            raise ValueError(f"Number of tiles in Y direction must be between 1 and 20, got {self.tiles_y}")

    def _configure_multi_scale(self) -> None:
        """Configure multi-scale settings."""
        # Auto-enable multi-scale for general detection mode
        if self.options_menu.general_detection and not self.options_menu.multi_scale:
            self.use_multi_scale = True
            hailo_logger.info("Auto-enabled multi-scale for general detection mode")
        else:
            self.use_multi_scale = self.options_menu.multi_scale

        if self.use_multi_scale:
            # Multi-scale: custom tiles PLUS predefined grids
            # scale_level: 1={1x1}, 2={1x1,2x2}, 3={1x1,2x2,3x3}
            self.scale_level = self.options_menu.scale_levels

            # Calculate total batch size: custom tiles + predefined grids
            custom_tiles = self.tiles_x * self.tiles_y
            if self.scale_level == 1:
                predefined_tiles = 1  # 1x1
            elif self.scale_level == 2:
                predefined_tiles = 1 + 4  # 1x1 + 2x2
            else:  # scale_level == 3
                predefined_tiles = 1 + 4 + 9  # 1x1 + 2x2 + 3x3

            self.batch_size = custom_tiles + predefined_tiles

            hailo_logger.info(f"Multi-scale mode: {self.tiles_x}x{self.tiles_y} + predefined grids = {self.batch_size} tiles")
        else:
            # Single-scale: only custom tiles
            self.scale_level = 0  # Not used
            self.batch_size = self.tiles_x * self.tiles_y
            hailo_logger.info(f"Single-scale mode: {self.tiles_x}x{self.tiles_y} = {self.batch_size} tiles")

    def _configure_detection(self) -> None:
        """Configure detection parameters."""
        self.iou_threshold = self.options_menu.iou_threshold
        self.border_threshold = self.options_menu.border_threshold if self.use_multi_scale else 0.0
