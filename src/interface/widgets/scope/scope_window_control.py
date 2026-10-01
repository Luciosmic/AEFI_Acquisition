"""
ScopeWindowControl - Interface V2
"From start" vs "Sliding window" display-window selector for continuous-reading
plots. Computes the visible slice of a buffer at draw time — the buffer itself
is never trimmed, so switching back to "From start" always shows full history.
Composed into panels (electric_field_probe_panel, aefi_continuous_reading_panel);
not a shared base class.
"""

from typing import Dict, List, Tuple

from PySide6.QtWidgets import QGroupBox, QFormLayout, QComboBox, QDoubleSpinBox
from PySide6.QtCore import Signal


class ScopeWindowControl(QGroupBox):
    """Owns the Display mode combo + sliding duration spinbox and slices buffers for plotting."""

    changed = Signal()

    def __init__(self, parent=None, default_window_s: float = 10.0, title: str = "Window"):
        super().__init__(title, parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["From start", "Sliding window"])
        self.mode_combo.setCurrentText("Sliding window")
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addRow("Display:", self.mode_combo)

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 3600.0)
        self.duration_spin.setValue(default_window_s)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.valueChanged.connect(lambda _value: self.changed.emit())
        layout.addRow("Duration:", self.duration_spin)

        self._update_duration_visibility()

    def is_sliding(self) -> bool:
        return self.mode_combo.currentText().startswith("Sliding")

    def window_seconds(self) -> float:
        return self.duration_spin.value()

    def visible_slice(
        self, times: List[float], values: Dict[str, List[float]]
    ) -> Tuple[List[float], Dict[str, List[float]]]:
        """Return the (times, values) slice to plot for the current mode. Input buffers are untouched."""
        if not times or not self.is_sliding():
            return times, values

        t_min = times[-1] - self.window_seconds()
        idx_start = 0
        for i, t in enumerate(times):
            if t >= t_min:
                idx_start = i
                break
        return times[idx_start:], {name: ys[idx_start:] for name, ys in values.items()}

    def _on_mode_changed(self, _text: str):
        self._update_duration_visibility()
        self.changed.emit()

    def _update_duration_visibility(self):
        is_sliding = self.is_sliding()
        self.duration_spin.setVisible(is_sliding)
        label = self.layout().labelForField(self.duration_spin)
        if label is not None:
            label.setVisible(is_sliding)
