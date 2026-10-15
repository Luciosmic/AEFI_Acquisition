"""ScanVisualizationPanel: a hidden panel does not draw its canvas; it draws
(tight_layout included) at its first show."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.scan_visualization_panel import ScanVisualizationPanel

_ALIVE = []  # keep top-level test widgets alive (Qt still lays them out)


def _panel(**kwargs):
    QApplication.instance() or QApplication([])
    panel = ScanVisualizationPanel(**kwargs)
    _ALIVE.append(panel)
    return panel


def _drawn(panel) -> bool:
    return hasattr(panel.canvas, "renderer")  # set by the first Agg draw


def test_hidden_panel_is_not_drawn_at_construction():
    for kwargs in ({}, {"profiles": True}):
        panel = _panel(**kwargs)
        assert not _drawn(panel)


def test_first_show_draws_and_lays_out_once():
    panel = _panel()
    panel.combo_view_mode.setCurrentText(ScanVisualizationPanel.ALL)  # heatmap grid: needs a tight_layout
    calls = []
    original = panel.figure.tight_layout
    panel.figure.tight_layout = lambda *a, **k: (calls.append(1), original(*a, **k))

    panel.show()
    assert _drawn(panel)
    assert len(calls) == 1

    calls.clear()
    panel.initialize_scan(0, 1, 2, 0, 1, 2)  # a new scan rebuilds the grid: one tight_layout
    panel.update_data_point(0, 0, {"x_in_phase": 1.0}, redraw=False)
    panel._redraw_now()
    panel.update_data_point(1, 0, {"x_in_phase": 2.0}, redraw=False)
    panel._redraw_now()
    assert len(calls) == 1  # heatmap redraws during the scan: no tight_layout
    panel.close()


def test_data_received_while_hidden_is_drawn_at_show():
    panel = _panel()
    panel.initialize_scan(0, 1, 2, 0, 1, 2)
    panel.update_data_point(0, 0, {"x_in_phase": 1.0})
    assert not _drawn(panel)

    panel.show()
    assert _drawn(panel)
    assert not panel._render_pending
    panel.close()
