# region imports
# Standard library imports
import math
from typing import Tuple

# Local application-specific imports
from hailo_apps.hailo_app_python.core.common.hailo_logger import get_logger

hailo_logger = get_logger(__name__)
# endregion imports


def calculate_auto_tiles(frame_width: int, frame_height: int, model_input_size: int, min_overlap: float = 0.1) -> Tuple[int, int, float, float]:
    """
    Calculate optimal tile grid for auto mode where tiles are sized to model input.
    Ensures minimum overlap requirement is met.

    Args:
        frame_width: Input frame width in pixels
        frame_height: Input frame height in pixels
        model_input_size: Model's input resolution (e.g., 640 for 640x640)
        min_overlap: Minimum required overlap ratio (default: 0.1 = 10%)

    Returns:
        (tiles_x, tiles_y, overlap_x, overlap_y): Tile counts and overlap ratios
    """
    # Calculate effective tile coverage considering minimum overlap
    # effective_tile_size = tile_size * (1 - overlap)
    # We need: frame_size <= tile_size + (n-1) * effective_tile_size
    # Rearranging: n >= (frame_size - tile_size) / effective_tile_size + 1

    effective_tile_width = model_input_size * (1 - min_overlap)
    effective_tile_height = model_input_size * (1 - min_overlap)

    # Calculate minimum tiles needed with minimum overlap constraint
    if frame_width <= model_input_size:
        tiles_x = 1
    else:
        tiles_x = math.ceil((frame_width - model_input_size) / effective_tile_width) + 1

    if frame_height <= model_input_size:
        tiles_y = 1
    else:
        tiles_y = math.ceil((frame_height - model_input_size) / effective_tile_height) + 1

    # Calculate actual overlap based on tile count
    # Formula: overlap = (tiles * tile_size - frame_size) / ((tiles - 1) * tile_size)
    if tiles_x > 1:
        overlap_x = (tiles_x * model_input_size - frame_width) / ((tiles_x - 1) * model_input_size)
        overlap_x = max(min_overlap, min(0.5, overlap_x))  # Clamp to [min_overlap, 0.5]
    else:
        overlap_x = 0.0

    if tiles_y > 1:
        overlap_y = (tiles_y * model_input_size - frame_height) / ((tiles_y - 1) * model_input_size)
        overlap_y = max(min_overlap, min(0.5, overlap_y))  # Clamp to [min_overlap, 0.5]
    else:
        overlap_y = 0.0

    return tiles_x, tiles_y, overlap_x, overlap_y


def calculate_manual_tiles_overlap(
    frame_width: int,
    frame_height: int,
    tiles_x: int,
    tiles_y: int,
    model_input_size: int,
    min_overlap: float = 0.1
) -> Tuple[float, float, float, float]:
    """
    Calculate overlap for manual mode where user specifies tile counts.
    If minimum overlap can't be met with model input size, calculates larger tile sizes.

    Args:
        frame_width: Input frame width in pixels
        frame_height: Input frame height in pixels
        tiles_x: User-specified number of tiles horizontally
        tiles_y: User-specified number of tiles vertically
        model_input_size: Model's input resolution
        min_overlap: Minimum recommended overlap ratio (default: 0.1)

    Returns:
        (overlap_x, overlap_y, tile_size_x, tile_size_y): Overlap ratios and actual tile sizes
    """
    # First, try with model input size
    if tiles_x > 1:
        overlap_x = (tiles_x * model_input_size - frame_width) / ((tiles_x - 1) * model_input_size)
        overlap_x = max(0.0, min(0.5, overlap_x))
    else:
        overlap_x = 0.0

    if tiles_y > 1:
        overlap_y = (tiles_y * model_input_size - frame_height) / ((tiles_y - 1) * model_input_size)
        overlap_y = max(0.0, min(0.5, overlap_y))
    else:
        overlap_y = 0.0

    # Check if we need larger tiles to meet minimum overlap
    # Calculate required tile sizes for both dimensions
    tile_size_x = model_input_size
    tile_size_y = model_input_size

    if tiles_x > 1 and overlap_x < min_overlap:
        tile_size_x = (frame_width + (tiles_x - 1) * min_overlap * model_input_size) / tiles_x

    if tiles_y > 1 and overlap_y < min_overlap:
        tile_size_y = (frame_height + (tiles_y - 1) * min_overlap * model_input_size) / tiles_y

    # Use the larger of the two calculated sizes to maintain square aspect ratio
    if tile_size_x > model_input_size or tile_size_y > model_input_size:
        tile_size = max(tile_size_x, tile_size_y)
        tile_size_x = tile_size
        tile_size_y = tile_size

        # Recalculate overlap with the square tiles
        if tiles_x > 1:
            overlap_x = (tiles_x * tile_size - frame_width) / ((tiles_x - 1) * tile_size)
            overlap_x = max(0.0, min(0.5, overlap_x))

        if tiles_y > 1:
            overlap_y = (tiles_y * tile_size - frame_height) / ((tiles_y - 1) * tile_size)
            overlap_y = max(0.0, min(0.5, overlap_y))

    return overlap_x, overlap_y, tile_size_x, tile_size_y
