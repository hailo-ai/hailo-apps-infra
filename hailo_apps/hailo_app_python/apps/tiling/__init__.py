"""Tiling application for Hailo AI processors.

This package provides tiling functionality for processing high-resolution images
by splitting them into smaller tiles for efficient object detection.
"""

from .tiling_pipeline import GStreamerTilingApp
from .tile_calculator import calculate_auto_tiles, calculate_manual_tiles_overlap
from .configuration import TilingConfiguration, detect_model_config_from_hef

__all__ = [
    'GStreamerTilingApp',
    'calculate_auto_tiles',
    'calculate_manual_tiles_overlap',
    'detect_model_config_from_hef',
    'TilingConfiguration'
]
