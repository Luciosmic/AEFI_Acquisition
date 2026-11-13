import pytest

from domain.frequency_sweep.value_objects.frequency_grid.frequency_grid import FrequencyGrid


def test_logarithmic_grid_spans_bounds_evenly_on_a_log_scale() -> None:
    grid = FrequencyGrid.logarithmic(100.0, 10000.0, 3)
    assert grid.frequencies_hz == (100.0, 1000.0, 10000.0)


def test_logarithmic_grids_from_the_same_bounds_are_equal() -> None:
    assert FrequencyGrid.logarithmic(200.0, 50000.0, 17) == FrequencyGrid.logarithmic(200.0, 50000.0, 17)


@pytest.mark.parametrize("frequencies", [(1000.0,), (100.0, 100.0), (1000.0, 100.0), (0.0, 100.0), (-1.0, 100.0)])
def test_refuses_a_grid_that_cannot_be_compared(frequencies):
    with pytest.raises(ValueError):
        FrequencyGrid(frequencies)


@pytest.mark.parametrize("start, stop, count", [(100.0, 100.0, 5), (0.0, 100.0, 5), (100.0, 1000.0, 1)])
def test_refuses_impossible_logarithmic_bounds(start, stop, count):
    with pytest.raises(ValueError):
        FrequencyGrid.logarithmic(start, stop, count)


def test_index_of_a_grid_frequency() -> None:
    grid = FrequencyGrid((100.0, 200.0, 400.0))
    assert grid.index_of(200.0) == 1
    with pytest.raises(ValueError):
        grid.index_of(300.0)
