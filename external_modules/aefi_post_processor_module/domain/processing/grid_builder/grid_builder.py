"""
grid_builder - Builds the scan grid from coordinates and channel values: the planned grid when known, else a square one (numpy only).
See grid_builder_intention.md.
"""

from enum import Enum
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

from ..planned_scan_grid.planned_scan_grid import PlannedScanGrid

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


class GridOrigin(Enum):
    """Where the shape of the grid came from."""

    PLANNED = 'planned'  # the grid the acquisition planned
    NO_PLAN = 'no_plan'  # no planned grid known: square grid on the measured points
    POINTS_OFF_PLAN = 'points_off_plan'  # a measured point lies outside the planned grid: square grid on the measured points


def build_planned_grid(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    channel_names: Sequence[str],
    planned: PlannedScanGrid,
) -> Optional[Tuple[np.ndarray, Dict[str, object]]]:
    """
    Place scan points on the grid the acquisition planned, NaN where no point was measured.

    A complete rectangular scan fills its grid; an interrupted scan keeps its planned rows and columns, empty
    where it stopped. Returns None when a point lies more than half a step from every node of the planned grid.

    Returns:
        (grid, metadata) - grid has shape (planned y points, planned x points, num_channels), indexed [y, x, channel];
        metadata holds the same keys as build_square_grid, with grid_shape instead of grid_size.
    """
    if len(channel_names) == 0:
        raise ValueError("No voltage columns found in DataFrame")

    columns = planned.x.node_indices(x)
    rows = planned.y.node_indices(y)
    if columns is None or rows is None:
        return None

    n_rows, n_columns = planned.y.points, planned.x.points
    num_channels = len(channel_names)
    grid = np.full((n_rows, n_columns, num_channels), np.nan)
    grid[rows, columns, :] = values

    x_step, y_step = planned.x.step, planned.y.step
    extent = [
        planned.x.minimum - x_step / 2,
        planned.x.maximum + x_step / 2,
        planned.y.minimum - y_step / 2,
        planned.y.maximum + y_step / 2,
    ]

    metadata = {
        'extent': extent,
        'x_coords': planned.x.nodes().tolist(),
        'y_coords': planned.y.nodes().tolist(),
        'x_step': x_step,
        'y_step': y_step,
        'grid_shape': [n_rows, n_columns],
        'grid_origin': GridOrigin.PLANNED.value,
        'original_nx': len(np.unique(x)),
        'original_ny': len(np.unique(y)),
        'num_channels': num_channels,
        'channel_names': list(channel_names),
        'valid_points': int(np.sum(~np.isnan(grid[:, :, 0]))),
        'total_points': n_rows * n_columns,
    }
    return grid, metadata


def build_scan_grid(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    channel_names: Sequence[str],
    planned: Optional[PlannedScanGrid],
) -> Tuple[np.ndarray, Dict[str, object], GridOrigin]:
    """
    The grid of a scan: the planned one when it is known and holds every point, else the square grid
    on the measured points (unchanged, so that scans without a description keep their numbers).
    """
    if planned is not None:
        built = build_planned_grid(x, y, values, channel_names, planned)
        if built is not None:
            grid, metadata = built
            return grid, metadata, GridOrigin.PLANNED
        grid, metadata = build_square_grid(x, y, values, channel_names)
        return grid, metadata, GridOrigin.POINTS_OFF_PLAN
    grid, metadata = build_square_grid(x, y, values, channel_names)
    return grid, metadata, GridOrigin.NO_PLAN
