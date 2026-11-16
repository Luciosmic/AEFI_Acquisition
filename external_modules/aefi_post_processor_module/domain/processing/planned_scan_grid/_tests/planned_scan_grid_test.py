import numpy as np
import pytest

from ..planned_scan_grid import PlannedAxis


def test_nodes_are_evenly_spaced_with_both_ends_included():
    axis = PlannedAxis(minimum=300.0, maximum=900.0, points=150)

    nodes = axis.nodes()

    assert len(nodes) == 150 and nodes[0] == 300.0 and nodes[-1] == 900.0
    assert axis.step == pytest.approx(600.0 / 149)


def test_each_coordinate_gets_the_index_of_its_nearest_node():
    axis = PlannedAxis(minimum=0.0, maximum=4.0, points=3)  # nodes 0, 2, 4

    assert axis.node_indices(np.array([0.0, 2.0, 4.0, 2.9, 0.4])).tolist() == [0, 1, 2, 1, 0]


def test_a_coordinate_beyond_half_a_step_from_the_zone_is_not_described():
    axis = PlannedAxis(minimum=0.0, maximum=4.0, points=3)

    assert axis.node_indices(np.array([0.0, 5.5])) is None
    assert axis.node_indices(np.array([-1.5])) is None


def test_a_single_node_axis_accepts_only_its_own_coordinate():
    axis = PlannedAxis(minimum=10.0, maximum=10.0, points=1)

    assert axis.step == 1.0
    assert axis.node_indices(np.array([10.0, 10.0])).tolist() == [0, 0]
    assert axis.node_indices(np.array([10.5])) is None


@pytest.mark.parametrize("minimum, maximum, points", [(0.0, 1.0, 0), (1.0, 1.0, 3), (2.0, 1.0, 2)])
def test_an_axis_without_points_or_without_extent_is_refused(minimum, maximum, points):
    with pytest.raises(ValueError):
        PlannedAxis(minimum=minimum, maximum=maximum, points=points)
