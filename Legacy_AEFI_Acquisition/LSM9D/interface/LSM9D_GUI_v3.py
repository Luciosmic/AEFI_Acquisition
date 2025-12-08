#!/usr/bin/env python3
"""
Interface d'Affichage LSM9D - Version épurée avec sélection du mode
Affichage des valeurs numériques, statistiques associées, et graphe temps réel.
Connexion automatique au lancement, choix du mode via QComboBox (ALL_SENSORS par défaut).
"""

import sys
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg

# --- Correction import manager LSM9D (copié de la v2) ---
components_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'components'))
if components_dir not in sys.path:
    sys.path.insert(0, components_dir)
from LSM9D_acquisition_manager import LSM9D_AcquisitionManager

COLORS = {
    'primary_blue': '#2E86AB',
    'mag_blue': '#4A90E2',
    'acc_green': '#2A9D8F',
    'gyr_orange': '#F77F00',
    'lidar_purple': '#A23B72',
    'dark_bg': '#353535',
    'darker_bg': '#252525',
    'text_white': '#FFFFFF',
}

SENSORS = [
    ('magnetometer', '🧲 Magnétomètre', COLORS['mag_blue']),
    ('accelerometer', '📐 Accéléromètre', COLORS['acc_green']),
    ('gyroscope', '🌀 Gyroscope', COLORS['gyr_orange']),
]

class SensorDisplayWidget(QWidget):
    """Affichage live + stats pour un capteur 3 axes"""
    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self.label = label
        self.color = color
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(self.label)
        title.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {self.color};")
        layout.addWidget(title)
        grid = QHBoxLayout()
        self.axis_labels = {}
        self.axis_stats = {}
        for axis in ['x', 'y', 'z']:
            vbox = QVBoxLayout()
            axis_label = QLabel(f"{axis.upper()} : 0.000")
            axis_label.setStyleSheet(f"background-color: {COLORS['darker_bg']}; border: 2px solid {self.color}; border-radius: 5px; padding: 8px; color: {COLORS['text_white']}; font-family: 'Courier New', monospace; font-weight: bold; font-size: 14px; min-width: 80px;")
            axis_label.setAlignment(Qt.AlignCenter)
            self.axis_labels[axis] = axis_label
            stats_label = QLabel("μ: --\nσ: --")
            stats_label.setStyleSheet(f"color: {self.color}; font-size: 13px; font-family: 'Courier New', monospace; font-weight: bold; padding-top: 4px; padding-bottom: 8px; min-width: 100px; padding-left: 8px; padding-right: 8px;")
            stats_label.setAlignment(Qt.AlignCenter)
            stats_label.setWordWrap(True)
            self.axis_stats[axis] = stats_label
            vbox.addWidget(axis_label)
            vbox.addWidget(stats_label)
            grid.addLayout(vbox)
        layout.addLayout(grid)
    def update(self, values, buffer=None):
        for axis in ['x', 'y', 'z']:
            v = values.get(axis, 0)
            self.axis_labels[axis].setText(f"{axis.upper()} : {v:.3f}")
            if buffer:
                vals = [d[axis] for d in buffer if axis in d]
                if len(vals) > 1:
                    mu = np.mean(vals)
                    sigma = np.std(vals, ddof=1)
                    self.axis_stats[axis].setText(f"μ: {mu:.2f}\nσ: {sigma:.2f}")
                else:
                    self.axis_stats[axis].setText("μ: --\nσ: --")
            else:
                self.axis_stats[axis].setText("μ: --\nσ: --")

class LidarDisplayWidget(QWidget):
    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self.label = label
        self.color = color
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(self.label)
        title.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {self.color};")
        layout.addWidget(title)
        self.value_label = QLabel("0.000")
        self.value_label.setStyleSheet(f"background-color: {COLORS['darker_bg']}; border: 2px solid {self.color}; border-radius: 5px; padding: 8px; color: {COLORS['text_white']}; font-family: 'Courier New', monospace; font-weight: bold; font-size: 14px; min-width: 80px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        self.stats_label = QLabel("μ: --\nσ: --")
        self.stats_label.setStyleSheet(f"color: {self.color}; font-size: 13px; font-family: 'Courier New', monospace; font-weight: bold; padding-top: 4px; padding-bottom: 8px; min-width: 100px; padding-left: 8px; padding-right: 8px;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
    def update(self, value, buffer=None):
        self.value_label.setText(f"{value:.3f}")
        if buffer and len(buffer) > 1:
            mu = np.mean(buffer)
            sigma = np.std(buffer, ddof=1)
            self.stats_label.setText(f"μ: {mu:.2f}\nσ: {sigma:.2f}")
        else:
            self.stats_label.setText("μ: --\nσ: --")

class RealtimeGraphWidget(QWidget):
    """Graphe temps réel pour tous les capteurs"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_points = 200
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLORS['dark_bg'])
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel('left', 'Valeur')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.addLegend()
        self.curves = {}
        self.data_buffers = {}
        # 3 axes par capteur + LIDAR
        self.channels = [
            ('magnetometer', 'x', COLORS['mag_blue']),
            ('magnetometer', 'y', COLORS['mag_blue']),
            ('magnetometer', 'z', COLORS['mag_blue']),
            ('accelerometer', 'x', COLORS['acc_green']),
            ('accelerometer', 'y', COLORS['acc_green']),
            ('accelerometer', 'z', COLORS['acc_green']),
            ('gyroscope', 'x', COLORS['gyr_orange']),
            ('gyroscope', 'y', COLORS['gyr_orange']),
            ('gyroscope', 'z', COLORS['gyr_orange']),
            ('lidar', None, COLORS['lidar_purple'])
        ]
        for capteur, axe, color in self.channels:
            name = f"{capteur}_{axe}" if axe else "lidar"
            curve = self.plot_widget.plot([], [], pen=pg.mkPen(color, width=2), name=name)
            self.curves[name] = curve
            self.data_buffers[name] = []
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
    def update_graph(self, buffer, timestamps):
        if not buffer or not timestamps:
            return
        t0 = timestamps[0]
        times = [t - t0 for t in timestamps]
        for capteur, axe, color in self.channels:
            name = f"{capteur}_{axe}" if axe else "lidar"
            if capteur == 'lidar':
                values = [d for d in buffer['lidar']]
            else:
                values = [d[axe] for d in buffer[capteur]]
            self.data_buffers[name] = values
            self.curves[name].setData(times[:len(values)], values)

class MainApp(QMainWindow):
    MODES = [
        ("MAG_ONLY", "Magnétomètre seul"),
        ("ACC_GYR", "Accéléromètre + Gyroscope"),
        ("MAG_ACC_GYR", "Magnétomètre + Accéléro + Gyro"),
        ("ALL_SENSORS", "Tous capteurs + LIDAR")
    ]
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.apply_dark_theme()
        self.init_ui()
        self.connect_and_start()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 10 Hz
    def apply_dark_theme(self):
        self.setStyleSheet(f"QMainWindow {{background-color: {COLORS['dark_bg']}; color: {COLORS['text_white']};}}")
    def init_ui(self):
        self.setWindowTitle("Affichage LSM9D - Live")
        self.setGeometry(100, 100, 1200, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # Sélecteur de mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode capteur :")
        mode_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.mode_combo = QComboBox()
        for code, label in self.MODES:
            self.mode_combo.addItem(f"{code} - {label}", code)
        self.mode_combo.setCurrentIndex(3)  # ALL_SENSORS par défaut
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)
        # Affichage capteurs
        sensors_layout = QHBoxLayout()
        self.mag_widget = SensorDisplayWidget('🧲 Magnétomètre', COLORS['mag_blue'])
        self.acc_widget = SensorDisplayWidget('📐 Accéléromètre', COLORS['acc_green'])
        self.gyr_widget = SensorDisplayWidget('🌀 Gyroscope', COLORS['gyr_orange'])
        self.lidar_widget = LidarDisplayWidget('📏 LIDAR', COLORS['lidar_purple'])
        sensors_layout.addWidget(self.mag_widget)
        sensors_layout.addWidget(self.acc_widget)
        sensors_layout.addWidget(self.gyr_widget)
        sensors_layout.addWidget(self.lidar_widget)
        main_layout.addLayout(sensors_layout)
        # Graphe
        self.graph_widget = RealtimeGraphWidget()
        main_layout.addWidget(self.graph_widget)
    def connect_and_start(self):
        self.manager.connect()
        mode_code = self.mode_combo.currentData()
        self.manager.initialize_sensor_mode(mode_code)
        self.manager.start_streaming()
    def on_mode_changed(self, idx):
        mode_code = self.mode_combo.itemData(idx)
        self.manager.stop_streaming()
        self.manager.initialize_sensor_mode(mode_code)
        self.manager.start_streaming()
    def _update_display(self):
        data = self.manager.get_current_data()
        mag = data['magnetometer']
        acc = data['accelerometer']
        gyr = data['gyroscope']
        lidar = data['lidar']
        mag_buffer = self.manager.get_historical_data('magnetometer', 100)
        acc_buffer = self.manager.get_historical_data('accelerometer', 100)
        gyr_buffer = self.manager.get_historical_data('gyroscope', 100)
        lidar_buffer = self.manager.get_historical_data('lidar', 100)
        timestamps = self.manager.get_historical_data('timestamps', 100)
        self.mag_widget.update(mag, mag_buffer)
        self.acc_widget.update(acc, acc_buffer)
        self.gyr_widget.update(gyr, gyr_buffer)
        self.lidar_widget.update(lidar, lidar_buffer)
        buffer = {
            'magnetometer': mag_buffer,
            'accelerometer': acc_buffer,
            'gyroscope': gyr_buffer,
            'lidar': lidar_buffer
        }
        self.graph_widget.update_graph(buffer, timestamps)
    def closeEvent(self, event):
        self.manager.stop_streaming()
        self.manager.disconnect()
        event.accept()

def main():
    manager = LSM9D_AcquisitionManager()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainApp(manager)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 