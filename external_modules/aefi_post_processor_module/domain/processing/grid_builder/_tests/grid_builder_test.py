import numpy as np
import pytest

from ...grid_builder.grid_builder import build_square_grid

CHANNELS = ['voltage_x_in_phase', 'voltage_x_quadrature']


def _points(xs, ys):
    """All (x, y) pairs, x varying fastest, with value (10*y_index + x_index, -1)."""
    x, y, values = [], [], []
    for j, yv in enumerate(ys):
        for i, xv in enumerate(xs):
            x.append(xv)
            y.append(yv)
            values.append([10.0 * j + i, -1.0])
    return np.array(x), np.array(y), np.array(values)


def test_complete_square_scan_fills_every_cell_at_its_row_and_column():
    x, y, values = _points([0.0, 1.0, 2.0], [5.0, 6.0, 7.0])

    grid, meta = build_square_grid(x, y, values, CHANNELS)

    assert grid.shape == (3, 3, 2)
    assert grid[2, 1, 0] == 21.0  # row = y index, column = x index
    assert not np.isnan(grid).any()
    assert meta['valid_points'] == 9 and meta['total_points'] == 9


def test_incomplete_scan_is_padded_with_nan_to_the_larger_side():
    x, y, values = _points([0.0, 1.0, 2.0], [5.0, 6.0])  # 3 columns, 2 rows

    grid, meta = build_square_grid(x, y, values, CHANNELS)

    assert grid.shape == (3, 3, 2)
    assert np.isnan(grid[2, :, :]).all()
    assert meta['original_nx'] == 3 and meta['original_ny'] == 2
    assert meta['valid_points'] == 6 and meta['total_points'] == 9


def test_extent_is_cell_edges_of_the_grid_not_of_the_points():
    x, y, values = _points([0.0, 2.0, 4.0], [10.0, 12.0])

    _, meta = build_square_grid(x, y, values, CHANNELS)

    # step 2 on both axes, grid of 3: x from -1 to 5, y from 9 to 15
    assert meta['extent'] == [-1.0, 5.0, 9.0, 15.0]
    assert meta['x_step'] == 2.0 and meta['y_step'] == 2.0


def test_fixed_grid_size_overrides_the_scan_size():
    x, y, values = _points([0.0, 1.0], [0.0, 1.0])

    grid, meta = build_square_grid(x, y, values, CHANNELS, grid_size=4)

    assert grid.shape == (4, 4, 2)
    assert meta['grid_size'] == 4 and meta['valid_points'] == 4


def test_no_channel_is_refused():
    with pytest.raises(ValueError):
        build_square_grid(np.array([0.0]), np.array([0.0]), np.empty((1, 0)), [])
