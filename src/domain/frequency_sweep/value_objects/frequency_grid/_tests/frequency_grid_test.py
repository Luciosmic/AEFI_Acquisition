import pytest

from domain.frequency_sweep.value_objects.frequency_grid.frequency_grid import FrequencyGrid


def test_per_decade_grid_is_anchored_on_the_decades() -> None:
    assert FrequencyGrid.per_decade(100.0, 10000.0, 1).frequencies_hz == (100.0, 1000.0, 10000.0)
    assert FrequencyGrid.per_decade(100.0, 1000.0, 4).frequencies_hz == (100.0, 177.828, 316.228, 562.341, 1000.0)


def test_per_decade_grids_share_their_common_frequencies_whatever_the_bounds() -> None:
    wide = FrequencyGrid.per_decade(100.0, 100000.0, 10).frequencies_hz
    narrow = FrequencyGrid.per_decade(150.0, 2000.0, 10).frequencies_hz
    assert set(narrow) <= set(wide)
    assert narrow[0] == 158.489  # first decade point above the start bound


def test_a_list_is_swept_in_ascending_order() -> None:
    assert FrequencyGrid.from_list([1000.0, 100.0, 250.0]).frequencies_hz == (100.0, 250.0, 1000.0)


def test_a_list_with_a_duplicate_is_refused() -> None:
    with pytest.raises(ValueError):
        FrequencyGrid.from_list([100.0, 1000.0, 100.0])


@pytest.mark.parametrize("frequencies", [(1000.0,), (100.0, 100.0), (1000.0, 100.0), (0.0, 100.0), (-1.0, 100.0)])
def test_refuses_a_grid_that_cannot_be_compared(frequencies):
    with pytest.raises(ValueError):
        FrequencyGrid(frequencies)


@pytest.mark.parametrize("start, stop, per_decade", [(100.0, 100.0, 5), (0.0, 100.0, 5), (100.0, 1000.0, 0), (110.0, 120.0, 10)])
def test_refuses_impossible_per_decade_bounds(start, stop, per_decade):
    with pytest.raises(ValueError):
        FrequencyGrid.per_decade(start, stop, per_decade)


def test_index_of_a_grid_frequency() -> None:
    grid = FrequencyGrid((100.0, 200.0, 400.0))
    assert grid.index_of(200.0) == 1
    with pytest.raises(ValueError):
        grid.index_of(300.0)
