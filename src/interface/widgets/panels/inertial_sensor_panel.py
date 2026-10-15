"""
Inertial Sensor Panel

Live values of the inertial sensor (accelerometer, gyroscope, magnetometer)
and of the lidar that travels in the same stream. Connection and start are
operator actions, never tied to application startup.

The widget never imports domain/ types: it receives booleans, strings and the
frozen InertialSensorReadingViewModel.
"""

from typing import Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from interface.presentation.inertial_sensor_view_model import (
    ABSENT,
    CHANNELS,
    InertialSensorReadingViewModel,
)

_UNVERIFIED_STYLE = "color: #E67E22; font-size: 11px; font-weight: bold;"
_NOTE_STYLE = "color: #888; font-size: 11px; font-style: italic;"
_VALUE_STYLE = "font-family: Consolas; font-size: 18px; min-width: 110px;"


# ponytail: the lidar row is displayed here only because the lidar travels in the
# same stream (same board, same serial link). Ceiling: one panel carries both.
# Upgrade: a separate lidar panel once it has its own concept and port.
class InertialSensorPanel(QWidget):
    connect_requested = Signal()
    disconnect_requested = Signal()
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._connected = False
        self._acquiring = False
        self._labels: Dict[str, QLabel] = {}
        self._banners: Dict[str, QLabel] = {}
        self._notes: Dict[str, QLabel] = {}
        self._values: Dict[str, List[QLabel]] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(5, 5, 5, 5)
        root.setSpacing(8)

        controls = QHBoxLayout()
        self.btn_connect = QPushButton("Connecter")
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.btn_start = QPushButton("Démarrer")
        self.btn_start.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_stop = QPushButton("Arrêter")
        self.btn_stop.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        controls.addWidget(self.btn_connect)
        controls.addWidget(self.btn_start)
        controls.addWidget(self.btn_stop)
        controls.addStretch()
        root.addLayout(controls)

        self.lbl_state = QLabel("● Non connecté")
        self.lbl_state.setStyleSheet("color: #888; font-weight: bold;")
        self.lbl_rate = QLabel("Cadence mesurée : — · échantillons : 0")
        self.lbl_rate.setStyleSheet("color: #888;")
        root.addWidget(self.lbl_state)
        root.addWidget(self.lbl_rate)

        for descriptor in CHANNELS:
            group = QGroupBox()
            grid = QGridLayout(group)
            title = QLabel(descriptor.label)
            title.setStyleSheet("font-weight: bold;")
            self._labels[descriptor.key] = title
            grid.addWidget(title, 0, 0, 1, max(1, len(descriptor.axis_labels)))

            value_labels: List[QLabel] = []
            for column, axis in enumerate(descriptor.axis_labels):
                axis_label = QLabel(axis)
                axis_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                axis_label.setStyleSheet("color: #888;")
                value = QLabel(ABSENT)
                value.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value.setStyleSheet(_VALUE_STYLE)
                grid.addWidget(axis_label, 1, column)
                grid.addWidget(value, 2, column)
                value_labels.append(value)
            self._values[descriptor.key] = value_labels

            banner = QLabel(descriptor.unverified_reason)
            banner.setStyleSheet(_UNVERIFIED_STYLE)
            banner.setVisible(descriptor.unverified)
            self._banners[descriptor.key] = banner
            grid.addWidget(banner, 3, 0, 1, max(1, len(descriptor.axis_labels)))

            note = QLabel(descriptor.note)
            note.setStyleSheet(_NOTE_STYLE)
            note.setVisible(bool(descriptor.note))
            self._notes[descriptor.key] = note
            grid.addWidget(note, 4, 0, 1, max(1, len(descriptor.axis_labels)))

            root.addWidget(group)
        root.addStretch()

    # ------------------------------------------------------------------ #
    # Inspection helpers (tests, accessibility)
    # ------------------------------------------------------------------ #

    def channel_label_text(self, key: str) -> str:
        return self._labels[key].text()

    def unverified_banner_text(self, key: str) -> str:
        return self._banners[key].text()

    def note_text(self, key: str) -> str:
        return self._notes[key].text()

    def value_texts(self, key: str) -> List[str]:
        return [label.text() for label in self._values[key]]

    # ------------------------------------------------------------------ #
    # Panel -> Presenter
    # ------------------------------------------------------------------ #

    def _on_connect_clicked(self) -> None:
        if self._connected:
            self.disconnect_requested.emit()
        else:
            self.connect_requested.emit()

    # ------------------------------------------------------------------ #
    # Presenter -> Panel
    # ------------------------------------------------------------------ #

    def on_connection_changed(self, connected: bool, label: str) -> None:
        self._connected = connected
        self.btn_connect.setText("Déconnecter" if connected else "Connecter")
        if connected:
            self.lbl_state.setText(f"● {label}")
            self.lbl_state.setStyleSheet("color: #2ECC71; font-weight: bold;")
        else:
            color = "#888" if label == "Déconnecté" else "#E74C3C"
            self.lbl_state.setText(f"● {label}")
            self.lbl_state.setStyleSheet(f"color: {color}; font-weight: bold;")
        self._refresh_buttons()

    def on_acquisition_started(self) -> None:
        self._acquiring = True
        self.lbl_state.setText("● Acquisition en cours")
        self.lbl_state.setStyleSheet("color: #2ECC71; font-weight: bold;")
        self._refresh_buttons()

    def on_acquisition_stopped(self) -> None:
        self._acquiring = False
        if self._connected and "échec" not in self.lbl_state.text():
            self.lbl_state.setText("● Connecté")
            self.lbl_state.setStyleSheet("color: #2ECC71; font-weight: bold;")
        self._refresh_buttons()

    def on_acquisition_failed(self, reason: str) -> None:
        self.lbl_state.setText(f"● Flux en échec : {reason}")
        self.lbl_state.setStyleSheet("color: #E74C3C; font-weight: bold;")

    def on_reading_updated(self, reading: InertialSensorReadingViewModel) -> None:
        for channel in reading.channels:
            for label, text in zip(self._values[channel.key], channel.values):
                label.setText(text)
        rate = "—" if reading.measured_rate_hz is None else f"{reading.measured_rate_hz:.1f} Hz"
        self.lbl_rate.setText(
            f"Cadence mesurée : {rate} · échantillons : {reading.sample_count}"
        )

    def _refresh_buttons(self) -> None:
        self.btn_start.setEnabled(self._connected and not self._acquiring)
        self.btn_stop.setEnabled(self._connected and self._acquiring)
