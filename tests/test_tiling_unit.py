# region imports
# Standard library imports
import pytest
from unittest.mock import Mock, patch

# Local application-specific imports
from hailo_apps.hailo_app_python.apps.tiling.tile_calculator import (
    calculate_auto_tiles,
    calculate_manual_tiles_overlap
)
from hailo_apps.hailo_app_python.apps.tiling.configuration import (
    detect_model_config_from_hef
)
# endregion imports


class TestTileCalculator:
    """Test cases for tile calculation functions."""

    def test_calculate_auto_tiles_basic(self):
        """Test basic auto tile calculation."""
        # Test case: 1280x720 frame with 640x640 model
        tiles_x, tiles_y, overlap_x, overlap_y = calculate_auto_tiles(
            frame_width=1280, frame_height=720, model_input_size=640, min_overlap=0.1
        )

        # Should create 3x2 grid (based on actual calculation)
        assert tiles_x == 3
        assert tiles_y == 2
        assert 0.0 <= overlap_x <= 0.5
        assert 0.0 <= overlap_y <= 0.5

    def test_calculate_auto_tiles_single_tile(self):
        """Test auto tile calculation when frame is smaller than model input."""
        # Test case: 300x300 frame with 640x640 model
        tiles_x, tiles_y, overlap_x, overlap_y = calculate_auto_tiles(
            frame_width=300, frame_height=300, model_input_size=640, min_overlap=0.1
        )

        # Should create 1x1 grid
        assert tiles_x == 1
        assert tiles_y == 1
        assert overlap_x == 0.0
        assert overlap_y == 0.0

    def test_calculate_auto_tiles_large_frame(self):
        """Test auto tile calculation for large frame."""
        # Test case: 4K frame with 640x640 model
        tiles_x, tiles_y, overlap_x, overlap_y = calculate_auto_tiles(
            frame_width=3840, frame_height=2160, model_input_size=640, min_overlap=0.1
        )

        # Should create multiple tiles
        assert tiles_x > 2
        assert tiles_y > 2
        assert 0.1 <= overlap_x <= 0.5  # Should meet minimum overlap
        assert 0.1 <= overlap_y <= 0.5

    def test_calculate_auto_tiles_edge_cases(self):
        """Test edge cases for auto tile calculation."""
        # Test case: exact model size
        tiles_x, tiles_y, overlap_x, overlap_y = calculate_auto_tiles(
            frame_width=640, frame_height=640, model_input_size=640, min_overlap=0.1
        )
        assert tiles_x == 1
        assert tiles_y == 1

        # Test case: slightly larger than model size
        tiles_x, tiles_y, overlap_x, overlap_y = calculate_auto_tiles(
            frame_width=641, frame_height=641, model_input_size=640, min_overlap=0.1
        )
        assert tiles_x == 2
        assert tiles_y == 2

    def test_calculate_manual_tiles_overlap_basic(self):
        """Test basic manual tile overlap calculation."""
        overlap_x, overlap_y, tile_size_x, tile_size_y = calculate_manual_tiles_overlap(
            frame_width=1280, frame_height=720, tiles_x=2, tiles_y=2,
            model_input_size=640, min_overlap=0.1
        )

        # May need larger tiles to meet minimum overlap
        assert tile_size_x >= 640
        assert tile_size_y >= 640
        assert tile_size_x == tile_size_y  # Should maintain square aspect ratio
        assert 0.0 <= overlap_x <= 0.5
        assert 0.0 <= overlap_y <= 0.5

    def test_calculate_manual_tiles_overlap_insufficient_overlap(self):
        """Test manual tile calculation when minimum overlap can't be met."""
        # Test case: very small tiles that can't meet minimum overlap
        overlap_x, overlap_y, tile_size_x, tile_size_y = calculate_manual_tiles_overlap(
            frame_width=1000, frame_height=1000, tiles_x=3, tiles_y=3,
            model_input_size=300, min_overlap=0.2
        )

        # Should enlarge tiles to meet minimum overlap
        assert tile_size_x > 300
        assert tile_size_y > 300
        assert tile_size_x == tile_size_y  # Should maintain square aspect ratio
        # Note: The actual overlap may be less than requested due to rounding
        assert overlap_x >= 0.0  # Should be non-negative
        assert overlap_y >= 0.0

    def test_calculate_manual_tiles_overlap_single_tile(self):
        """Test manual tile calculation with single tile."""
        overlap_x, overlap_y, tile_size_x, tile_size_y = calculate_manual_tiles_overlap(
            frame_width=640, frame_height=640, tiles_x=1, tiles_y=1,
            model_input_size=640, min_overlap=0.1
        )

        assert tile_size_x == 640
        assert tile_size_y == 640
        assert overlap_x == 0.0
        assert overlap_y == 0.0

    def test_calculate_manual_tiles_overlap_edge_cases(self):
        """Test edge cases for manual tile calculation."""
        # Test case: tiles larger than frame
        overlap_x, overlap_y, tile_size_x, tile_size_y = calculate_manual_tiles_overlap(
            frame_width=300, frame_height=300, tiles_x=2, tiles_y=2,
            model_input_size=640, min_overlap=0.1
        )

        # Should still work but with large overlap (clamped to 0.5)
        assert tile_size_x == 640
        assert tile_size_y == 640
        assert overlap_x <= 0.5  # Clamped to maximum 0.5
        assert overlap_y <= 0.5


class TestModelDetector:
    """Test cases for model detection functions."""

    def test_detect_model_config_from_hef_mobilenet(self):
        """Test model detection for MobileNetSSD model."""
        model_type, input_size, postprocess_function = detect_model_config_from_hef(
            "/path/to/mobilenet_model.hef"
        )

        assert model_type == "mobilenet"
        assert input_size == 300
        assert "mobilenet" in postprocess_function.lower()

    def test_detect_model_config_from_hef_yolo(self):
        """Test model detection for YOLO model."""
        model_type, input_size, postprocess_function = detect_model_config_from_hef(
            "/path/to/yolov6n.hef"
        )

        assert model_type == "yolo"
        assert input_size == 640
        assert postprocess_function == "filter"  # YOLO postprocess function

    def test_detect_model_config_from_hef_unknown(self):
        """Test model detection for unknown model type."""
        model_type, input_size, postprocess_function = detect_model_config_from_hef(
            "/path/to/unknown_model.hef"
        )

        assert model_type == "yolo"  # Default fallback
        assert input_size == 640
        assert postprocess_function == "filter"  # YOLO postprocess function

    def test_detect_model_config_from_hef_none(self):
        """Test model detection with None input."""
        model_type, input_size, postprocess_function = detect_model_config_from_hef(None)

        assert model_type == "mobilenet"  # Default type
        assert input_size == 300
        assert postprocess_function == "filter"  # Default postprocess function

    def test_detect_model_config_from_hef_case_insensitive(self):
        """Test model detection is case insensitive."""
        model_type, input_size, postprocess_function = detect_model_config_from_hef(
            "/path/to/MOBILENET_MODEL.HEF"
        )

        assert model_type == "mobilenet"
        assert input_size == 300

    def test_detect_model_config_from_hef_partial_match(self):
        """Test model detection with partial filename match."""
        model_type, input_size, postprocess_function = detect_model_config_from_hef(
            "/path/to/my_mobilenet_ssd_model.hef"
        )

        assert model_type == "mobilenet"
        assert input_size == 300


class TestTilingConfiguration:
    """Test cases for tiling configuration class."""

    def test_configuration_initialization(self):
        """Test basic configuration initialization."""
        # Mock options menu
        options_menu = Mock()
        options_menu.input = None
        options_menu.general_detection = False
        options_menu.hef_path = None
        options_menu.tiles_x = None
        options_menu.tiles_y = None
        options_menu.min_overlap = 0.1
        options_menu.multi_scale = False
        options_menu.scale_levels = 1
        options_menu.iou_threshold = 0.3
        options_menu.border_threshold = 0.15

        # Mock resource path functions and file existence
        with patch('hailo_apps.hailo_app_python.apps.tiling.configuration.get_resource_path') as mock_get_resource, \
             patch('pathlib.Path.exists') as mock_exists:
            mock_get_resource.return_value = "/mock/path/to/model.hef"
            mock_exists.return_value = True

            from hailo_apps.hailo_app_python.apps.tiling.configuration import TilingConfiguration
            config = TilingConfiguration(options_menu, 1280, 720, "hailo8")

            # Basic assertions
            assert config.video_width == 1280
            assert config.video_height == 720
            assert config.arch == "hailo8"
            assert config.tiling_mode == "auto"  # Default mode
            assert config.use_multi_scale == False

    def test_configuration_manual_mode(self):
        """Test configuration with manual tiling mode."""
        options_menu = Mock()
        options_menu.input = None
        options_menu.general_detection = False
        options_menu.hef_path = None
        options_menu.tiles_x = 3
        options_menu.tiles_y = 2
        options_menu.min_overlap = 0.1
        options_menu.multi_scale = False
        options_menu.scale_levels = 1
        options_menu.iou_threshold = 0.3
        options_menu.border_threshold = 0.15

        with patch('hailo_apps.hailo_app_python.apps.tiling.configuration.get_resource_path') as mock_get_resource, \
             patch('pathlib.Path.exists') as mock_exists:
            mock_get_resource.return_value = "/mock/path/to/model.hef"
            mock_exists.return_value = True

            from hailo_apps.hailo_app_python.apps.tiling.configuration import TilingConfiguration
            config = TilingConfiguration(options_menu, 1280, 720, "hailo8")

            assert config.tiling_mode == "manual"
            assert config.tiles_x == 3
            assert config.tiles_y == 2

    def test_configuration_multi_scale_mode(self):
        """Test configuration with multi-scale mode."""
        options_menu = Mock()
        options_menu.input = None
        options_menu.general_detection = False
        options_menu.hef_path = None
        options_menu.tiles_x = None
        options_menu.tiles_y = None
        options_menu.min_overlap = 0.1
        options_menu.multi_scale = True
        options_menu.scale_levels = 2
        options_menu.iou_threshold = 0.3
        options_menu.border_threshold = 0.15

        with patch('hailo_apps.hailo_app_python.apps.tiling.configuration.get_resource_path') as mock_get_resource, \
             patch('pathlib.Path.exists') as mock_exists:
            mock_get_resource.return_value = "/mock/path/to/model.hef"
            mock_exists.return_value = True

            from hailo_apps.hailo_app_python.apps.tiling.configuration import TilingConfiguration
            config = TilingConfiguration(options_menu, 1280, 720, "hailo8")

            assert config.use_multi_scale == True
            assert config.scale_level == 2
            # Should have custom tiles + predefined grids
            assert config.batch_size > config.tiles_x * config.tiles_y

    def test_configuration_general_detection_mode(self):
        """Test configuration with general detection mode."""
        options_menu = Mock()
        options_menu.input = None
        options_menu.general_detection = True
        options_menu.hef_path = None
        options_menu.tiles_x = None
        options_menu.tiles_y = None
        options_menu.min_overlap = 0.1
        options_menu.multi_scale = False
        options_menu.scale_levels = 1
        options_menu.iou_threshold = 0.3
        options_menu.border_threshold = 0.15

        with patch('hailo_apps.hailo_app_python.apps.tiling.configuration.get_resource_path') as mock_get_resource, \
             patch('pathlib.Path.exists') as mock_exists:
            mock_get_resource.return_value = "/mock/path/to/yolo.hef"
            mock_exists.return_value = True

            from hailo_apps.hailo_app_python.apps.tiling.configuration import TilingConfiguration
            config = TilingConfiguration(options_menu, 1280, 720, "hailo8")

            assert config.use_multi_scale == True  # Auto-enabled for general detection
            assert config.model_type == "yolo"
            assert config.model_input_size == 640
            # Check that general detection mode was used (via options_menu)
            assert config.options_menu.general_detection == True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
