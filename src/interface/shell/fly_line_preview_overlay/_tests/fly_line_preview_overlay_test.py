"""The provisional points of a fly line disappear from the map unless the line is confirmed —
driven through the real ScanPresenter signals, panels faked."""
import math

import pytest

from interface.presenters._tests.scan_presenter_line_request_test import _presenter
from interface.shell.fly_line_preview_overlay.fly_line_preview_overlay import wire_fly_line_preview


class _FakePanel:
    def __init__(self):
        self.cells = {}

    def update_data_point_from_position(self, x, y, measurements, redraw=True):
        self.cells.setdefault((x, y), {}).update(measurements)


def _point(x, y, v):
    return {"x": x, "y": y, "value": {"x_in_phase": v, "y_in_phase": v}}


@pytest.fixture
def stack():
    presenter, _ = _presenter()
    panels = [_FakePanel(), _FakePanel()]
    wire_fly_line_preview(presenter, panels)
    presenter.present_scan_started("s1", {"x_min": 0, "x_max": 1, "x_nb_points": 2,
                                          "y_min": 0, "y_max": 1, "y_nb_points": 2})
    return presenter, panels


def _is_blank(panel, x, y):
    return all(math.isnan(v) for v in panel.cells[(x, y)].values())


def _preview_line_1(presenter):
    presenter.present_scan_line_preview(1, 0, _point(1.0, 0.0, 0.5))
    presenter.present_scan_line_preview(1, 1, _point(1.0, 1.0, 0.6))


@pytest.mark.parametrize("end", [
    lambda p: p.present_scan_line_abandoned(1, "paused"),
    lambda p: p.present_scan_cancelled("s1"),
    lambda p: p.present_scan_failed("s1", "boom"),
], ids=["abandoned", "cancelled", "failed"])
def test_unconfirmed_preview_points_are_erased_when_the_line_is_not_confirmed(stack, end):
    presenter, panels = stack
    presenter.present_scan_progress(0, 4, _point(0.0, 0.0, 0.1))  # line 0, definitive (drawn by the wiring)
    _preview_line_1(presenter)

    end(presenter)

    for panel in panels:
        assert _is_blank(panel, 1.0, 0.0) and _is_blank(panel, 1.0, 1.0)
        assert (0.0, 0.0) not in panel.cells  # a definitive point is never touched by the overlay


def test_preview_points_confirmed_by_definitive_points_are_kept(stack):
    presenter, panels = stack
    _preview_line_1(presenter)
    presenter.present_scan_progress(2, 4, _point(1.0, 0.0, 0.7))
    presenter.present_scan_progress(3, 4, _point(1.0, 1.0, 0.8))

    presenter.present_scan_cancelled("s1")  # after the line commit: nothing left to erase

    for panel in panels:
        assert panel.cells[(1.0, 0.0)]["x_in_phase"] == 0.5  # preview value; the wiring draws the definitive
        assert not _is_blank(panel, 1.0, 1.0)


def test_a_new_scan_forgets_the_previous_unconfirmed_points(stack):
    presenter, panels = stack
    _preview_line_1(presenter)
    presenter.present_scan_started("s2", {"x_min": 0, "x_max": 1, "x_nb_points": 2,
                                          "y_min": 0, "y_max": 1, "y_nb_points": 2})

    presenter.present_scan_line_abandoned(0, "paused")

    assert not _is_blank(panels[0], 1.0, 0.0)
