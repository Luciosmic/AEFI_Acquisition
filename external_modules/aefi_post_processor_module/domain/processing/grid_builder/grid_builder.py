"""
grid_builder - Builds the square scan grid from coordinates and channel values (numpy only).
See grid_builder_intention.md.
"""

from typing import Dict, Optional, Sequence, Tuple

import numpy as np

# The six measured channels, in the order of the last axis of a grid.
VOLTAGE_CHANNELS: Tuple[str, ...] = (
    'voltage_x_in_phase', 'voltage_x_quadrature',
    'voltage_y_in_phase', 'voltage_y_quadrature',
    'voltage_z_in_phase', 'voltage_z_quadrature',
)


def build_square_grid(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    channel_names: Sequence[str],
    grid_size: Optional[int] = None,
) -> Tuple[np.ndarray, Dict[str, object]]:
    """
    Place scan points on a square grid, NaN where no point was measured.

    Args:
        x: x coordinate of each point, shape (n,)
        y: y coordinate of each point, shape (n,)
        values: channel values of each point, shape (n, num_channels)
        channel_names: name of each channel, in the order of ``values`` columns
        grid_size: side of the square grid. If None, max(nx, ny).

    Returns:
        (grid, metadata) - grid has shape (N, N, num_channels), indexed [y, x, channel];
        metadata holds extent [left, right, bottom, top], coordinates, steps and point counts.
    """
    if len(channel_names) == 0:
        raise ValueError("No voltage columns found in DataFrame")

    x_coords = np.unique(x)
    y_coords = np.unique(y)

    x_min, x_max = x_coords[0], x_coords[-1]
    y_min, y_max = y_coords[0], y_coords[-1]

    x_step = np.mean(np.diff(x_coords)) if len(x_coords) > 1 else 1.0
    y_step = np.mean(np.diff(y_coords)) if len(y_coords) > 1 else 1.0

    n_x = len(x_coords)
    n_y = len(y_coords)
    if grid_size is None:
        grid_size = max(n_x, n_y)

    num_channels = len(channel_names)
    grid = np.full((grid_size, grid_size, num_channels), np.nan)
    grid[np.searchsorted(y_coords, y), np.searchsorted(x_coords, x), :] = values

    extent = [
        x_min - x_step / 2,
        x_min + (grid_size - 1) * x_step + x_step / 2,
        y_min - y_step / 2,
        y_min + (grid_size - 1) * y_step + y_step / 2,
    ]

    metadata = {
        'extent': extent,
        'x_coords': x_coords.tolist(),
        'y_coords': y_coords.tolist(),
        'x_step': x_step,
        'y_step': y_step,
        'grid_size': grid_size,
        'original_nx': n_x,
        'original_ny': n_y,
        'num_channels': num_channels,
        'channel_names': list(channel_names),
        'valid_points': int(np.sum(~np.isnan(grid[:, :, 0]))),
        'total_points': grid_size * grid_size,
    }
    return grid, metadata
