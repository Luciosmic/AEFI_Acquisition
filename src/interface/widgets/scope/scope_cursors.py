"""
ScopeCursors - Interface V2
Oscilloscope-style positionable X (time) / Y (amplitude) cursor pairs for a
pyqtgraph PlotWidget, with a live delta readout. When the host plot is in
sliding-window mode, call sync_to_window() each redraw so the cursors track
the window instead of scrolling out of view. Composed into panels; not a
shared base class.
"""

from typing import List, Optional

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
import pyqtgraph as pg  # type: ignore[import]

_TOGGLE_STYLE = (
    "QPushButton { color: #888; border: 1px solid #555; border-radius: 3px; padding: 2px 6px; }"
    "QPushButton:checked { background-color: #27AE60; color: white; border: 1px solid #27AE60; font-weight: bold; }"
)

_CURSOR_COLOR = "#FFFFFF"
_CURSOR_WIDTH = 2


class ScopeCursors(QGroupBox):
    """Draggable X1/X2 (time) and Y1/Y2 (amplitude) cursor lines plus a dX/dY readout."""

    def __init__(self, parent=None, y_unit: str = ""):
        super().__init__("Cursors", parent)
        self._y_unit = y_unit
        self._plot: Optional[pg.PlotWidget] = None
        self._lines: List[pg.InfiniteLine] = []
        self._last_window_start: Optional[float] = None
        self.x1 = self.x2 = self.y1 = self.y2 = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        self.btn_toggle = QPushButton("Show")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setStyleSheet(_TOGGLE_STYLE)
        self.btn_toggle.toggled.connect(self._on_toggled)
        self.lbl_readout = QLabel("—")
        self.lbl_readout.setStyleSheet("color: #888; font-size: 10px; font-family: monospace;")
        layout.addWidget(self.btn_toggle)
        layout.addWidget(self.lbl_readout)

    def set_y_unit(self, unit: str):
        self._y_unit = unit

    def attach(self, plot: pg.PlotWidget):
        """Bind cursors to a plot. Call again after plot.clear() to recreate lines on it."""
        self._plot = plot
        self._lines = []
        self._last_window_start = None
        self.x1 = self.x2 = self.y1 = self.y2 = None
        if self.btn_toggle.isChecked():
            self._create_lines()

    def sync_to_window(self, t_plot: List[float], sliding: bool):
        """Call once per plot update with the currently visible time slice."""
        if not sliding or not t_plot:
            self._last_window_start = None
            return
        start = t_plot[0]
        if self._last_window_start is not None:
            self._advance(start - self._last_window_start)
        self._last_window_start = start

    def _on_toggled(self, checked: bool):
        if not self._plot:
            return
        if checked:
            if not self._lines:
                self._create_lines()
            for line in self._lines:
                self._plot.addItem(line)
            self._update_readout()
        else:
            for line in self._lines:
                self._plot.removeItem(line)

    def _create_lines(self):
        (x_lo, x_hi), (y_lo, y_hi) = self._plot.getViewBox().viewRange()
        pen_1 = pg.mkPen(_CURSOR_COLOR, width=_CURSOR_WIDTH, style=Qt.PenStyle.DashLine)
        pen_2 = pg.mkPen(_CURSOR_COLOR, width=_CURSOR_WIDTH, style=Qt.PenStyle.DashDotLine)
        self.x1 = pg.InfiniteLine(
            pos=x_lo + (x_hi - x_lo) * 0.25, angle=90, movable=True, pen=pen_1,
            label="X1: {value:0.3f}s", labelOpts={"color": _CURSOR_COLOR},
        )
        self.x2 = pg.InfiniteLine(
            pos=x_lo + (x_hi - x_lo) * 0.75, angle=90, movable=True, pen=pen_2,
            label="X2: {value:0.3f}s", labelOpts={"color": _CURSOR_COLOR},
        )
        self.y1 = pg.InfiniteLine(
            pos=y_lo + (y_hi - y_lo) * 0.25, angle=0, movable=True, pen=pen_1,
            label="Y1: {value:0.3f}", labelOpts={"color": _CURSOR_COLOR},
        )
        self.y2 = pg.InfiniteLine(
            pos=y_lo + (y_hi - y_lo) * 0.75, angle=0, movable=True, pen=pen_2,
            label="Y2: {value:0.3f}", labelOpts={"color": _CURSOR_COLOR},
        )
        self._lines = [self.x1, self.x2, self.y1, self.y2]
        for line in self._lines:
            line.sigPositionChanged.connect(self._update_readout)

    def _advance(self, dt: float):
        if dt == 0 or self.x1 is None:
            return
        self.x1.blockSignals(True)
        self.x2.blockSignals(True)
        self.x1.setPos(self.x1.value() + dt)
        self.x2.setPos(self.x2.value() + dt)
        self.x1.blockSignals(False)
        self.x2.blockSignals(False)
        self._update_readout()

    def _update_readout(self):
        dx = abs(self.x2.value() - self.x1.value())
        dy = abs(self.y2.value() - self.y1.value())
        freq = f"  1/dX={1 / dx:.3g} Hz" if dx > 0 else ""
        self.lbl_readout.setText(f"dX={dx:.4g}s  dY={dy:.4g}{self._y_unit}{freq}")
