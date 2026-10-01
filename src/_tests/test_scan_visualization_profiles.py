"""Profiles view of ScanVisualizationPanel: selection -> plotted series."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.interface.widgets.panels.scan_visualization_panel import ScanVisualizationPanel

_app = QApplication.instance() or QApplication([])


def _panel():
    p = ScanVisualizationPanel()
    p.combo_view_mode.setCurrentText("Profiles")
    # 3 x by 2 y grid, value = 10*x_idx + y_idx
    p.initialize_scan(0, 20, 3, 0, 10, 2, channels=['x_in_phase'])
    for xi in range(3):
        for yi in range(2):
            p.update_data_point(xi, yi, {'x_in_phase': 10 * xi + yi})
    return p


def test_nothing_checked_by_default():
    p = _panel()
    assert p.list_profiles.count() == 3  # one per X column
    assert p._checked_profiles() == []
    assert p.axes_dict['profiles'].get_lines() == []


def test_profile_along_x_plots_column_vs_y():
    p = _panel()
    p.list_profiles.item(1).setCheckState(Qt.Checked)  # X = 10 mm -> x_idx 1
    lines = p.axes_dict['profiles'].get_lines()
    assert len(lines) == 1
    assert list(lines[0].get_xdata()) == [0.0, 10.0]      # Y coords
    assert list(lines[0].get_ydata()) == [10.0, 11.0]     # column x_idx=1


def test_profile_along_y_plots_row_vs_x():
    p = _panel()
    p.combo_profile_axis.setCurrentIndex(1)  # fixed Y
    assert p.list_profiles.count() == 2
    p.list_profiles.item(1).setCheckState(Qt.Checked)  # Y = 10 mm -> y_idx 1
    lines = p.axes_dict['profiles'].get_lines()
    assert len(lines) == 1
    assert list(lines[0].get_xdata()) == [0.0, 10.0, 20.0]   # X coords
    assert list(lines[0].get_ydata()) == [1.0, 11.0, 21.0]   # row y_idx=1


def test_switching_axis_clears_selection():
    p = _panel()
    p.list_profiles.item(0).setCheckState(Qt.Checked)
    p.combo_profile_axis.setCurrentIndex(1)
    assert p._checked_profiles() == []
