"""
AEFI Spectral Analysis Panel - Interface V2
Continuous FFT amplitude spectrum of the corrected AEFI signal (same 6
channels as AefiContinuousReadingPanel), passive view pattern.
"""

from typing import Any, Dict, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QGroupBox,
    QGridLayout,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg  # type: ignore[import]

from interface.widgets.layouts.flow_layout import FlowLayout
from interface.widgets.panels.aefi_continuous_reading_panel import AefiContinuousReadingPanel


def _compact_group(title: str, layout_cls):
    """Titled group with tight margins — keeps the controls strip thin (same
    helper as aefi_continuous_reading_panel.py)."""
    group = QGroupBox(title)
    layout = layout_cls(group)
    layout.setContentsMargins(4, 2, 4, 2)
    layout.setSpacing(3)
    return group, layout


class AefiSpectralAnalysisPanel(QWidget):
    """
    Single panel showing the continuous FFT amplitude spectrum of the
    corrected AEFI signal (6 channels: Ux/Uy/Uz In-Phase/Quadrature).

    Features:
    - Window duration control (QDoubleSpinBox)
    - Channel visibility toggles (same channels/colors as AefiContinuousReadingPanel)
    - pyqtgraph spectrum plot (Fréquence (Hz) / Amplitude (V))
    """

    # Same channel set/colors as the time-domain panel — the FFT is computed
    # on the same corrected signal, so reusing the class attribute keeps the
    # two panels visually consistent without duplicating the list.
    CHANNELS = AefiContinuousReadingPanel.CHANNELS

    window_duration_changed = Signal(float)

    def __init__(self, parent=None, default_window_duration_s: float = 2.0):
        super().__init__(parent)
        self.channel_checkboxes: Dict[str, QPushButton] = {}

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(4, 4, 4, 4)
        vlayout.setSpacing(4)

        controls_host = QWidget()
        controls_host.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        controls_layout = FlowLayout(controls_host, spacing=4)

        # 1. Window duration
        grp_window, l_window = _compact_group("Window", QGridLayout)
        self.spin_window_duration = QDoubleSpinBox()
        self.spin_window_duration.setRange(0.1, 3600.0)
        self.spin_window_duration.setValue(default_window_duration_s)
        self.spin_window_duration.setSuffix(" s")
        self.spin_window_duration.valueChanged.connect(self._on_window_duration_changed)
        l_window.addWidget(QLabel("Duration:"), 0, 0)
        l_window.addWidget(self.spin_window_duration, 0, 1)
        self.lbl_sample_count = QLabel("—")
        l_window.addWidget(QLabel("Samples:"), 1, 0)
        l_window.addWidget(self.lbl_sample_count, 1, 1)
        controls_layout.addWidget(grp_window)

        # 2. Channel toggles — 3 columns (X, Y, Z) x 2 rows (In-Phase, Quadrature)
        grp_channels, channel_grid_layout = _compact_group("Channels", QGridLayout)
        for i, ch in enumerate(self.CHANNELS):
            cb = QPushButton(ch["label"])
            cb.setCheckable(True)
            cb.setChecked("In-Phase" in ch["name"])
            cb.setStyleSheet(f"QPushButton {{ color: {ch['color']}; font-weight: bold; padding: 1px 6px; }}"
                             f"QPushButton:checked {{ border: 2px solid {ch['color']}; }}")
            cb.clicked.connect(self._on_channel_toggled)
            self.channel_checkboxes[ch["name"]] = cb
            channel_grid_layout.addWidget(cb, i % 2, i // 2)
        controls_layout.addWidget(grp_channels)

        vlayout.addWidget(controls_host)

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.setBackground("#353535")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("left", "Amplitude (V)")
        self.plot.setLabel("bottom", "Fréquence (Hz)")
        self.plot.addLegend()

        self.curves: Dict[str, pg.PlotDataItem] = {}
        for ch in self.CHANNELS:
            pen = pg.mkPen(ch["color"], width=2, style=ch["style"])
            curve = self.plot.plot([], [], pen=pen, name=ch["label"])
            curve.setVisible("In-Phase" in ch["name"])
            self.curves[ch["name"]] = curve

        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.plot.setMinimumHeight(150)
        vlayout.addWidget(self.plot, 1)

    def _on_window_duration_changed(self, value: float):
        self.window_duration_changed.emit(value)

    def _on_channel_toggled(self):
        for name, btn in self.channel_checkboxes.items():
            if name in self.curves:
                self.curves[name].setVisible(btn.isChecked())

    def on_spectrum_updated(self, vm: Any):
        """Called for each new spectral analysis result (from presenter).
        `vm` is an AefiSpectralAnalysisViewModel."""
        self.lbl_sample_count.setText(str(vm.sample_count))
        frequencies: List[float] = vm.frequencies_hz
        for name, curve in self.curves.items():
            amplitudes = vm.amplitudes_by_channel.get(name, [])
            curve.setData(frequencies, amplitudes)
