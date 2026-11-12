"""Profiles view of ScanVisualizationPanel: selection -> plotted series."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.interface.widgets.panels.scan_visualization_panel import ScanVisualizationPanel

_app = QApplication.instance() or QApplication([])


def _panel():
    p = ScanVisualizationPanel(profiles=True)
    p.combo_view_mode.setCurrentText("Single Channel")
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
    assert p.axes_dict['single'].get_lines() == []


def test_profile_along_x_plots_column_vs_y():
    p = _panel()
    p.list_profiles.item(1).setCheckState(Qt.Checked)  # X = 10 mm -> x_idx 1
    lines = p.axes_dict['single'].get_lines()
    assert len(lines) == 1
    assert list(lines[0].get_xdata()) == [0.0, 10.0]      # Y coords
    assert list(lines[0].get_ydata()) == [10.0, 11.0]     # column x_idx=1


def test_profile_along_y_plots_row_vs_x():
    p = _panel()
    p.combo_profile_axis.setCurrentIndex(1)  # fixed Y
    assert p.list_profiles.count() == 2
    p.list_profiles.item(1).setCheckState(Qt.Checked)  # Y = 10 mm -> y_idx 1
    lines = p.axes_dict['single'].get_lines()
    assert len(lines) == 1
    assert list(lines[0].get_xdata()) == [0.0, 10.0, 20.0]   # X coords
    assert list(lines[0].get_ydata()) == [1.0, 11.0, 21.0]   # row y_idx=1


def test_oblique_line_plots_value_vs_distance():
    p = _panel()  # previous 2D scan
    # 45° line, 3 points, length 2*sqrt(2)
    p.initialize_line(0, 0, 2, 2, 3, channels=['x_in_phase'])
    for i in range(3):
        p.update_data_point_from_position(i, i, {'x_in_phase': 5.0 + i})
    assert not p.profiles_box.isVisibleTo(p)  # a line is its own single profile
    lines = p.axes_dict['single'].get_lines()
    assert len(lines) == 1
    assert np.allclose(lines[0].get_xdata(), [0, np.sqrt(2), 2 * np.sqrt(2)])
    assert list(lines[0].get_ydata()) == [5.0, 6.0, 7.0]


def test_grid_scan_after_line_restores_profile_list():
    p = _panel()
    p.initialize_line(0, 0, 10, 0, 2)
    p.initialize_scan(0, 20, 3, 0, 10, 2, channels=['x_in_phase'])
    assert p.profiles_box.isVisibleTo(p)
    assert p.list_profiles.count() == 3


def test_switching_axis_clears_selection():
    p = _panel()
    p.list_profiles.item(0).setCheckState(Qt.Checked)
    p.combo_profile_axis.setCurrentIndex(1)
    assert p._checked_profiles() == []


def test_check_all_then_none():
    p = _panel()
    p.btn_check_all.click()
    assert len(p.axes_dict['single'].get_lines()) == 3
    p.btn_check_none.click()
    assert p.axes_dict['single'].get_lines() == []


def test_six_channel_profiles_plot_same_selection_on_every_channel():
    p = ScanVisualizationPanel(profiles=True)
    assert p.combo_view_mode.currentText() == "All Channels"
    assert p.profiles_box.isVisibleTo(p)  # list usable before any scan
    p.initialize_scan(0, 20, 3, 0, 10, 2)  # 6 default voltage channels
    p.update_data_point(1, 0, {ch: 1.0 for ch in p.available_channels})
    p.list_profiles.item(1).setCheckState(Qt.Checked)
    p.list_profiles.item(2).setCheckState(Qt.Checked)
    assert len(p.axes_dict) == 6
    assert all(len(ax.get_lines()) == 2 for ax in p.axes_dict.values())


def test_map_panel_offers_heatmaps_only():
    p = ScanVisualizationPanel()
    modes = [p.combo_view_mode.itemText(i) for i in range(p.combo_view_mode.count())]
    assert modes == ["Single Channel", "All Channels"]
    assert not p.profiles_box.isVisibleTo(p)


def test_lazy_field_channels_get_one_profile_plot_each():
    # Narda: channel set unknown until the first point (depends on the probe)
    p = ScanVisualizationPanel(profiles=True, channels=())
    p.initialize_scan(0, 20, 3, 0, 10, 2)
    assert p.axes_dict == {}
    p.list_profiles.item(0).setCheckState(Qt.Checked)
    p.update_data_point(0, 0, {'field_x': 1.0, 'field_y': 2.0, 'field_z': 3.0})
    assert list(p.axes_dict) == ['field_x', 'field_y', 'field_z']
    assert all(len(ax.get_lines()) == 1 for ax in p.axes_dict.values())


def test_deferred_update_redraws_on_the_timer_not_per_point():
    p = ScanVisualizationPanel(profiles=True)
    p.combo_view_mode.setCurrentText("Single Channel")
    p.initialize_scan(0, 20, 3, 0, 10, 2, channels=['x_in_phase'])
    p.update_data_point(0, 0, {'x_in_phase': 1.0})
    p.list_profiles.item(0).setCheckState(Qt.Checked)
    p.show()

    p.update_data_point(0, 1, {'x_in_phase': 2.0}, redraw=False)
    assert np.isnan(p.axes_dict['single'].get_lines()[0].get_ydata()[1])  # not drawn yet
    assert p._redraw_timer.isActive()

    p._redraw_timer.timeout.emit()
    assert list(p.axes_dict['single'].get_lines()[0].get_ydata()) == [1.0, 2.0]
