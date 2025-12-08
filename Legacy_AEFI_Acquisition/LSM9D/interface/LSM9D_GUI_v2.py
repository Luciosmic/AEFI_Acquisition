import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                            QComboBox, QGroupBox, QTextEdit, QTabWidget,
                            QProgressBar, QStatusBar, QFrame, QSpinBox, QCheckBox)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
from datetime import datetime
import time
import os

# Import du manager LSM9D
components_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'components'))
if components_dir not in sys.path:
    sys.path.insert(0, components_dir)
from LSM9D_acquisition_manager import LSM9D_AcquisitionManager, AcquisitionStatus


# --- SensorWidget avec stats par axe ---
class SensorWidget(QGroupBox):
    def __init__(self, name, color='#2E86AB', emoji='📊'):
        print(f"[DEBUG] SensorWidget {name} construit")
        super().__init__(f"{emoji} {name}")
        layout = QGridLayout()
        self.x_label = QLabel("X:")
        self.y_label = QLabel("Y:")
        self.z_label = QLabel("Z:")
        self.x_value = QLabel("0.0")
        self.y_value = QLabel("0.0")
        self.z_value = QLabel("0.0")
        self.x_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #0000FF;")
        self.y_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFA500;")
        self.z_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF0000;")
        self.x_label.setStyleSheet("color: #0000FF; font-weight: bold;")
        self.y_label.setStyleSheet("color: #FFA500; font-weight: bold;")
        self.z_label.setStyleSheet("color: #FF0000; font-weight: bold;")
        layout.addWidget(self.x_label, 0, 0)
        layout.addWidget(self.x_value, 0, 1)
        layout.addWidget(self.y_label, 1, 0)
        layout.addWidget(self.y_value, 1, 1)
        layout.addWidget(self.z_label, 2, 0)
        layout.addWidget(self.z_value, 2, 1)
        # Stats par axe
        self.x_stats = QLabel("μ: --  σ: --")
        self.x_stats.setStyleSheet("color: #0000FF; font-family: 'Courier New'; font-size: 12px;")
        self.y_stats = QLabel("μ: --  σ: --")
        self.y_stats.setStyleSheet("color: #FFA500; font-family: 'Courier New'; font-size: 12px;")
        self.z_stats = QLabel("μ: --  σ: --")
        self.z_stats.setStyleSheet("color: #FF0000; font-family: 'Courier New'; font-size: 12px;")
        layout.addWidget(self.x_stats, 0, 2)
        layout.addWidget(self.y_stats, 1, 2)
        layout.addWidget(self.z_stats, 2, 2)
        self.setLayout(layout)
    def update_values(self, x, y, z, buffer=None):
        self.x_value.setText(f"{x:.0f}")
        self.y_value.setText(f"{y:.0f}")
        self.z_value.setText(f"{z:.0f}")
        if buffer:
            mag_x = [d['x'] for d in buffer]
            mu_x, sigma_x = (np.mean(mag_x), np.std(mag_x, ddof=1)) if len(mag_x) > 1 else (0, 0)
            self.x_stats.setText(f"μ: {mu_x:.2f}  σ: {sigma_x:.2f}")
            mag_y = [d['y'] for d in buffer]
            mu_y, sigma_y = (np.mean(mag_y), np.std(mag_y, ddof=1)) if len(mag_y) > 1 else (0, 0)
            self.y_stats.setText(f"μ: {mu_y:.2f}  σ: {sigma_y:.2f}")
            mag_z = [d['z'] for d in buffer]
            mu_z, sigma_z = (np.mean(mag_z), np.std(mag_z, ddof=1)) if len(mag_z) > 1 else (0, 0)
            self.z_stats.setText(f"μ: {mu_z:.2f}  σ: {sigma_z:.2f}")
        else:
            self.x_stats.setText("μ: --  σ: --")
            self.y_stats.setText("μ: --  σ: --")
            self.z_stats.setText("μ: --  σ: --")

class LidarWidget(QGroupBox):
    def __init__(self):
        print("[DEBUG] LidarWidget construit")
        super().__init__("📏 LIDAR")
        layout = QVBoxLayout()
        self.distance_label = QLabel("Distance:")
        self.distance_value = QLabel("0")
        self.distance_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #A23B72;")
        layout.addWidget(self.distance_label)
        layout.addWidget(self.distance_value)
        self.stats_label = QLabel("μ: --  σ: --")
        self.stats_label.setStyleSheet("color: #A23B72; font-family: 'Courier New'; font-size: 12px;")
        layout.addWidget(self.stats_label)
        self.setLayout(layout)
    def update_values(self, value, buffer=None):
        self.distance_value.setText(f"{value:.0f}")
        if buffer:
            mu, sigma = (np.mean(buffer), np.std(buffer, ddof=1)) if len(buffer) > 1 else (0, 0)
            self.stats_label.setText(f"μ: {mu:.2f}  σ: {sigma:.2f}")
        else:
            self.stats_label.setText("μ: --  σ: --")

class PlotWidget(QWidget):
    """Widget pour les graphiques temps réel"""
    
    def __init__(self, title, max_points=500):
        super().__init__()
        self.max_points = max_points
        
        layout = QVBoxLayout()
        
        # Graphique
        self.plot_widget = pg.PlotWidget(title=title)
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Valeur')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.showGrid(x=True, y=True)
        
        # Courbes avec les bonnes couleurs et légendes
        # X = Bleu, Y = Jaune, Z = Rouge
        self.curve_x = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='X (Bleu)')
        self.curve_y = self.plot_widget.plot(pen=pg.mkPen('y', width=2), name='Y (Jaune)')
        self.curve_z = self.plot_widget.plot(pen=pg.mkPen('r', width=2), name='Z (Rouge)')
        
        # Ajouter la légende
        self.plot_widget.addLegend(offset=(10, 10))
        
        # Données
        self.time_data = []
        self.x_data = []
        self.y_data = []
        self.z_data = []
        
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
    
    def update_plot(self, x, y, z, timestamp=None):
        """Met à jour le graphique"""
        if timestamp is None:
            timestamp = time.time()
        
        # Ajouter les nouvelles données
        self.time_data.append(timestamp)
        self.x_data.append(x)
        self.y_data.append(y)
        self.z_data.append(z)
        
        # Limiter le nombre de points
        if len(self.time_data) > self.max_points:
            self.time_data = self.time_data[-self.max_points:]
            self.x_data = self.x_data[-self.max_points:]
            self.y_data = self.y_data[-self.max_points:]
            self.z_data = self.z_data[-self.max_points:]
        
        # Convertir en temps relatif
        if self.time_data:
            relative_time = [t - self.time_data[0] for t in self.time_data]
            
            # Mettre à jour les courbes avec le bon ordre
            self.curve_x.setData(relative_time, self.x_data)  # Bleu
            self.curve_y.setData(relative_time, self.y_data)  # Jaune
            self.curve_z.setData(relative_time, self.z_data)  # Rouge
    
    def clear_plot(self):
        """Efface le graphique"""
        self.time_data.clear()
        self.x_data.clear()
        self.y_data.clear()
        self.z_data.clear()
        self.curve_x.setData([], [])
        self.curve_y.setData([], [])
        self.curve_z.setData([], [])

class PlotWidget1D(QWidget):
    """Widget pour les graphiques de valeurs scalaires (LIDAR)"""
    
    def __init__(self, title, color='#A23B72', max_points=500):
        super().__init__()
        self.max_points = max_points
        
        layout = QVBoxLayout()
        
        # Graphique
        self.plot_widget = pg.PlotWidget(title=title)
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Distance')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.showGrid(x=True, y=True)
        
        # Courbe unique pour le LIDAR
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color, width=3), name='Distance')
        
        # Ajouter la légende
        self.plot_widget.addLegend(offset=(10, 10))
        
        # Données
        self.time_data = []
        self.value_data = []
        
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
    
    def update_plot(self, value, timestamp=None):
        """Met à jour le graphique"""
        if timestamp is None:
            timestamp = time.time()
        
        # Ajouter les nouvelles données
        self.time_data.append(timestamp)
        self.value_data.append(value)
        
        # Limiter le nombre de points
        if len(self.time_data) > self.max_points:
            self.time_data = self.time_data[-self.max_points:]
            self.value_data = self.value_data[-self.max_points:]
        
        # Convertir en temps relatif
        if self.time_data:
            relative_time = [t - self.time_data[0] for t in self.time_data]
            
            # Mettre à jour la courbe
            self.curve.setData(relative_time, self.value_data)
    
    def clear_plot(self):
        """Efface le graphique"""
        self.time_data.clear()
        self.value_data.clear()
        self.curve.setData([], [])

class RealtimeGraphWidgetLSM9D(QWidget):
    """Widget graphique temps réel pyqtgraph pour LSM9D (Mx, My, Mz, Ax, Ay, Az, Gx, Gy, Gz, LIDAR)"""
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.window_duration = 5.0  # secondes (fenêtre glissante)
        self.max_points = 500
        self.signal_names = [
            ('Mx', 'magnetometer', 'x', '#2E86AB'),
            ('My', 'magnetometer', 'y', '#2E86AB'),
            ('Mz', 'magnetometer', 'z', '#2E86AB'),
            ('Ax', 'accelerometer', 'x', '#2A9D8F'),
            ('Ay', 'accelerometer', 'y', '#2A9D8F'),
            ('Az', 'accelerometer', 'z', '#2A9D8F'),
            ('Gx', 'gyroscope', 'x', '#F77F00'),
            ('Gy', 'gyroscope', 'y', '#F77F00'),
            ('Gz', 'gyroscope', 'z', '#F77F00'),
            ('LIDAR', 'lidar', None, '#A23B72')
        ]
        self.curves = {}
        self.data_buffers = {name: [] for name, *_ in self.signal_names}
        self.time_buffer = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Checkboxes pour chaque signal
        controls_layout = QHBoxLayout()
        self.checkboxes = {}
        for name, *_ in self.signal_names:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_checkbox_changed)
            self.checkboxes[name] = cb
            controls_layout.addWidget(cb)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        # Stats glissantes
        self.stats_labels = {}
        stats_layout = QHBoxLayout()
        for name, *_ in self.signal_names:
            label = QLabel(f"{name}: μ --  σ --")
            label.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px; padding: 2px;")
            self.stats_labels[name] = label
            stats_layout.addWidget(label)
        layout.addLayout(stats_layout)
        # Graphique pyqtgraph
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel('left', 'Valeur')
        self.plot_widget.setLabel('bottom', 'Temps (s)')
        self.plot_widget.addLegend()
        for name, _, _, color in self.signal_names:
            curve = self.plot_widget.plot([], [], pen=pg.mkPen(color, width=2), name=name)
            self.curves[name] = curve
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def _on_checkbox_changed(self):
        for name in self.checkboxes:
            self.curves[name].setVisible(self.checkboxes[name].isChecked())

    def update_graph(self):
        # Récupération des données du buffer du manager
        buffer = self.manager.get_latest_data(self.max_points)
        if not buffer:
            return
        # Extraction temps et valeurs
        times = [d['timestamp'] for d in buffer]
        t0 = times[0] if times else 0
        times = [t - t0 for t in times]
        self.time_buffer = times
        import numpy as np
        for name, capteur, axe, color in self.signal_names:
            values = []
            for d in buffer:
                if capteur == 'lidar':
                    v = d['lidar']
                else:
                    v = d[capteur][axe]
                values.append(v)
            self.data_buffers[name] = values
            self.curves[name].setData(self.time_buffer, values)
            # Stats glissantes
            if len(values) > 1:
                mu = np.mean(values)
                sigma = np.std(values, ddof=1)
                self.stats_labels[name].setText(f"{name}: μ {mu:.1f}  σ {sigma:.1f}")
            else:
                self.stats_labels[name].setText(f"{name}: μ --  σ --")

class LSM9D_GUI(QMainWindow):
    """Interface graphique principale pour le LSM9D"""
    
    def __init__(self):
        super().__init__()
        self.manager = LSM9D_AcquisitionManager()
        
        # Offsets pour la composante alternative
        self.offsets = {
            'magnetometer': {'x': 0, 'y': 0, 'z': 0},
            'accelerometer': {'x': 0, 'y': 0, 'z': 0},
            'gyroscope': {'x': 0, 'y': 0, 'z': 0}
        }
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timer()
        
        # Configuration initiale
        self.setWindowTitle("LSM9D - Interface Temps Réel")
        self.setGeometry(100, 100, 1200, 800)
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Barre de contrôle
        control_layout = self.create_control_panel()
        main_layout.addLayout(control_layout)
        
        # Contenu principal avec onglets
        tab_widget = QTabWidget()
        
        # Onglet données temps réel
        realtime_tab = self.create_realtime_tab()
        tab_widget.addTab(realtime_tab, "🔴 Temps Réel")
        
        # Onglet graphiques
        graphs_tab = self.create_graphs_tab()
        tab_widget.addTab(graphs_tab, "📈 Graphiques")
        
        main_layout.addWidget(tab_widget)
        
        central_widget.setLayout(main_layout)
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Déconnecté")
    
    def create_control_panel(self):
        """Crée le panneau de contrôle"""
        layout = QHBoxLayout()
        
        # Connexion
        self.connect_btn = QPushButton("🔌 Connecter")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)
        
        # Mode de capteur
        layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "MAG_ONLY - Magnétomètre seul",
            "ACC_GYR - Accéléromètre + Gyroscope", 
            "MAG_ACC_GYR - Magnétomètre + Accéléromètre + Gyroscope",
            "ALL_SENSORS - Tous capteurs + LIDAR"
        ])
        layout.addWidget(self.mode_combo)
        
        # Bouton d'initialisation
        self.init_btn = QPushButton("🚀 Initialiser")
        self.init_btn.clicked.connect(self.initialize_sensor)
        self.init_btn.setEnabled(False)
        layout.addWidget(self.init_btn)
        
        # Contrôle streaming
        self.stream_btn = QPushButton("▶️ Démarrer")
        self.stream_btn.clicked.connect(self.toggle_streaming)
        self.stream_btn.setEnabled(False)
        layout.addWidget(self.stream_btn)
        
        # Effacer données
        self.clear_btn = QPushButton("🗑️ Effacer")
        self.clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(self.clear_btn)
        
        layout.addStretch()
        
        # Fréquence d'affichage
        layout.addWidget(QLabel("Freq (Hz):"))
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 100)
        self.freq_spin.setValue(20)
        self.freq_spin.valueChanged.connect(self.update_timer_frequency)
        layout.addWidget(self.freq_spin)
        
        return layout
    
    def create_realtime_tab(self):
        """Crée l'onglet des données temps réel"""
        widget = QWidget()
        layout = QGridLayout()
        
        # Widgets des capteurs
        self.mag_widget = SensorWidget("Magnétomètre", "#E63946", "🧲")
        self.acc_widget = SensorWidget("Accéléromètre", "#2A9D8F", "📐")
        self.gyr_widget = SensorWidget("Gyroscope", "#F77F00", "🌀")
        self.lidar_widget = LidarWidget()
        
        # Disposition en grille
        layout.addWidget(self.mag_widget, 0, 0)
        layout.addWidget(self.acc_widget, 0, 1)
        layout.addWidget(self.gyr_widget, 1, 0)
        layout.addWidget(self.lidar_widget, 1, 1)
        
        # Informations système
        info_group = QGroupBox("ℹ️ Informations")
        info_layout = QVBoxLayout()
        
        self.data_count_label = QLabel("Points de données: 0")
        self.mode_label = QLabel("Mode: Aucun")
        self.frequency_label = QLabel("Fréquence: 0 Hz")
        
        info_layout.addWidget(self.data_count_label)
        info_layout.addWidget(self.mode_label)
        info_layout.addWidget(self.frequency_label)
        info_group.setLayout(info_layout)
        
        layout.addWidget(info_group, 0, 2, 2, 1)
        
        widget.setLayout(layout)
        return widget
    
    def create_graphs_tab(self):
        """Crée l'onglet des graphiques"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Checkboxes de sélection des signaux
        controls_layout = QHBoxLayout()
        self.graph_checkboxes = {}
        for name in ["Mx", "My", "Mz", "Ax", "Ay", "Az", "Gx", "Gy", "Gz", "LIDAR"]:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_graph_visibility)
            self.graph_checkboxes[name] = cb
            controls_layout.addWidget(cb)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        # Panneau de contrôle des offsets
        offset_group = QGroupBox("⚙️ Réglages d'Offset (Composante Alternative)")
        offset_layout = QHBoxLayout()
        
        # Boutons pour capturer les offsets
        self.capture_mag_offset_btn = QPushButton("📍 Capturer Offset Magnétomètre")
        self.capture_acc_offset_btn = QPushButton("📍 Capturer Offset Accéléromètre")
        self.capture_gyr_offset_btn = QPushButton("📍 Capturer Offset Gyroscope")
        
        self.capture_mag_offset_btn.clicked.connect(lambda: self.capture_offset('magnetometer'))
        self.capture_acc_offset_btn.clicked.connect(lambda: self.capture_offset('accelerometer'))
        self.capture_gyr_offset_btn.clicked.connect(lambda: self.capture_offset('gyroscope'))
        
        offset_layout.addWidget(self.capture_mag_offset_btn)
        offset_layout.addWidget(self.capture_acc_offset_btn)
        offset_layout.addWidget(self.capture_gyr_offset_btn)
        
        # Bouton pour reset tous les offsets
        self.reset_offsets_btn = QPushButton("🔄 Reset Tous Offsets")
        self.reset_offsets_btn.clicked.connect(self.reset_all_offsets)
        offset_layout.addWidget(self.reset_offsets_btn)
        
        # Affichage des offsets actuels
        self.offset_status_label = QLabel("Offsets: MAG(0,0,0) ACC(0,0,0) GYR(0,0,0)")
        offset_layout.addWidget(self.offset_status_label)
        
        offset_group.setLayout(offset_layout)
        main_layout.addWidget(offset_group)
        
        # Graphiques pour les capteurs 3D + LIDAR
        graphs_layout = QGridLayout()
        
        self.mag_plot = PlotWidget("🧲 Magnétomètre")
        self.acc_plot = PlotWidget("📐 Accéléromètre")
        self.gyr_plot = PlotWidget("🌀 Gyroscope")
        self.lidar_plot = PlotWidget1D("📏 LIDAR", "#A23B72")
        
        # Disposition: 2x2 avec les graphiques 3D et le LIDAR
        graphs_layout.addWidget(self.mag_plot, 0, 0)
        graphs_layout.addWidget(self.acc_plot, 0, 1)
        graphs_layout.addWidget(self.gyr_plot, 1, 0)
        graphs_layout.addWidget(self.lidar_plot, 1, 1)
        
        graphs_widget = QWidget()
        graphs_widget.setLayout(graphs_layout)
        main_layout.addWidget(graphs_widget)
        
        widget.setLayout(main_layout)
        return widget
    
    def create_realtime_graphs_tab(self):
        """Crée l'onglet des graphiques temps réel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.graph_widget = RealtimeGraphWidgetLSM9D(self.manager)
        layout.addWidget(self.graph_widget)
        return widget
    
    def setup_connections(self):
        """Configure les connexions backend"""
        self.manager.add_data_callback(self.on_data_received)
        self.manager.add_status_callback(self.on_status_changed)
    
    def setup_timer(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.last_update_time = time.time()
        self.last_data_count = 0
        self.update_timer.start(100)
        print("[DEBUG] update_timer started")
    
    def toggle_connection(self):
        """Gère la connexion/déconnexion"""
        if self.manager.is_connected:
            self.manager.disconnect()
        else:
            self.manager.connect()
    
    def initialize_sensor(self):
        """Initialise le capteur avec le mode sélectionné"""
        mode_text = self.mode_combo.currentText()
        mode = mode_text.split(' - ')[0]
        self.manager.initialize_sensor_mode(mode)
    
    def toggle_streaming(self):
        """Démarre/arrête le streaming"""
        if self.manager.is_streaming:
            self.manager.stop_streaming()
        else:
            self.manager.start_streaming()
    
    def clear_data(self):
        """Efface toutes les données"""
        self.manager.clear_data()
        self.mag_plot.clear_plot()
        self.acc_plot.clear_plot()
        self.gyr_plot.clear_plot()
        self.lidar_plot.clear_plot()
    
    def update_timer_frequency(self):
        """Met à jour la fréquence du timer d'affichage"""
        freq = self.freq_spin.value()
        if self.update_timer.isActive():
            self.update_timer.setInterval(1000 // freq)
    
    def capture_offset(self, sensor_type):
        """Capture l'offset actuel pour un capteur"""
        try:
            current_data = self.manager.get_current_data()
            sensor_data = current_data[sensor_type]
            
            # Capturer les valeurs actuelles comme offset
            self.offsets[sensor_type]['x'] = sensor_data['x']
            self.offsets[sensor_type]['y'] = sensor_data['y']
            self.offsets[sensor_type]['z'] = sensor_data['z']
            
            self.update_offset_display()
            
            # Feedback à l'utilisateur
            self.status_bar.showMessage(f"Offset capturé pour {sensor_type}: ({sensor_data['x']:.0f}, {sensor_data['y']:.0f}, {sensor_data['z']:.0f})")
            
        except Exception as e:
            self.status_bar.showMessage(f"Erreur capture offset: {e}")
    
    def reset_all_offsets(self):
        """Remet tous les offsets à zéro"""
        for sensor in self.offsets:
            self.offsets[sensor] = {'x': 0, 'y': 0, 'z': 0}
        
        self.update_offset_display()
        self.status_bar.showMessage("Tous les offsets ont été remis à zéro")
    
    def update_offset_display(self):
        """Met à jour l'affichage des offsets"""
        mag = self.offsets['magnetometer']
        acc = self.offsets['accelerometer']
        gyr = self.offsets['gyroscope']
        
        offset_text = f"Offsets: MAG({mag['x']:.0f},{mag['y']:.0f},{mag['z']:.0f}) ACC({acc['x']:.0f},{acc['y']:.0f},{acc['z']:.0f}) GYR({gyr['x']:.0f},{gyr['y']:.0f},{gyr['z']:.0f})"
        self.offset_status_label.setText(offset_text)
    
    def apply_offset(self, sensor_data, sensor_type):
        """Applique l'offset à des données de capteur"""
        offset = self.offsets[sensor_type]
        return {
            'x': sensor_data['x'] - offset['x'],
            'y': sensor_data['y'] - offset['y'],
            'z': sensor_data['z'] - offset['z']
        }
    
    def on_data_received(self):
        """Callback appelé lors de nouvelles données"""
        # La mise à jour de l'affichage est gérée par le timer
        pass
    
    def on_status_changed(self, status, message):
        """Callback appelé lors des changements de statut"""
        self.status_bar.showMessage(f"{status.upper()}: {message}")
        
        # Mettre à jour les boutons selon l'état
        if status == "connected":
            self.connect_btn.setText("🔌 Déconnecter")
            self.init_btn.setEnabled(True)
        elif status == "disconnected":
            self.connect_btn.setText("🔌 Connecter")
            self.init_btn.setEnabled(False)
            self.stream_btn.setEnabled(False)
            self.stream_btn.setText("▶️ Démarrer")
        elif status == "initialized":
            self.stream_btn.setEnabled(True)
        elif status == "streaming":
            self.stream_btn.setText("⏸️ Arrêter")
            self.update_timer.start(1000 // self.freq_spin.value())
        elif status == "stopped":
            self.stream_btn.setText("▶️ Démarrer")
            self.update_timer.stop()
    
    def update_display(self):
        print("[DEBUG] update_display called")
        try:
            current_data = self.manager.get_current_data()
            status = self.manager.get_status()
            buffer = self.manager.get_latest_data(100)
            mag_buffer = [d['magnetometer'] for d in buffer] if buffer else None
            acc_buffer = [d['accelerometer'] for d in buffer] if buffer else None
            gyr_buffer = [d['gyroscope'] for d in buffer] if buffer else None
            lidar_buffer = [d['lidar'] for d in buffer] if buffer else None
            # Appliquer les offsets aux données
            mag = self.apply_offset(current_data['magnetometer'], 'magnetometer')
            acc = self.apply_offset(current_data['accelerometer'], 'accelerometer')
            gyr = self.apply_offset(current_data['gyroscope'], 'gyroscope')
            lidar = current_data['lidar']
            self.mag_widget.update_values(mag['x'], mag['y'], mag['z'], mag_buffer)
            self.acc_widget.update_values(acc['x'], acc['y'], acc['z'], acc_buffer)
            self.gyr_widget.update_values(gyr['x'], gyr['y'], gyr['z'], gyr_buffer)
            self.lidar_widget.update_values(lidar, lidar_buffer)
            
            # Mettre à jour les graphiques avec les données offset
            timestamp = current_data['timestamp']
            if status['mode'] in ['MAG_ONLY', 'MAG_ACC_GYR', 'ALL_SENSORS']:
                self.mag_plot.update_plot(mag['x'], mag['y'], mag['z'], timestamp)
            if status['mode'] in ['ACC_GYR', 'MAG_ACC_GYR', 'ALL_SENSORS']:
                self.acc_plot.update_plot(acc['x'], acc['y'], acc['z'], timestamp)
                self.gyr_plot.update_plot(gyr['x'], gyr['y'], gyr['z'], timestamp)
            if status['mode'] in ['ALL_SENSORS']:
                self.lidar_plot.update_plot(lidar, timestamp)
            
            # Mettre à jour les graphiques temps réel
            # self.graph_widget.update_graph() # Supprimé
            
            # Mettre à jour les informations
            self.data_count_label.setText(f"Points de données: {status['data_points']}")
            self.mode_label.setText(f"Mode: {status['mode'] or 'Aucun'}")
            
            # Calculer la fréquence réelle
            current_time = time.time()
            data_count = status['data_points']
            if current_time - self.last_update_time > 1.0:  # Mise à jour chaque seconde
                freq = (data_count - self.last_data_count) / (current_time - self.last_update_time)
                self.frequency_label.setText(f"Fréquence: {freq:.1f} Hz")
                self.last_data_count = data_count
                self.last_update_time = current_time
            
            # Stats glissantes sur 100 derniers points
            # import numpy as np # Déjà importé au début
            # buffer = self.manager.get_latest_data(100) # Déjà récupéré
            # if buffer:
            #     # Magnétomètre
            #     mag_x = [d['magnetometer']['x'] for d in buffer]
            #     mag_y = [d['magnetometer']['y'] for d in buffer]
            #     mag_z = [d['magnetometer']['z'] for d in buffer]
            #     mu_x, sigma_x = (np.mean(mag_x), np.std(mag_x, ddof=1)) if len(mag_x) > 1 else (0, 0)
            #     mu_y, sigma_y = (np.mean(mag_y), np.std(mag_y, ddof=1)) if len(mag_y) > 1 else (0, 0)
            #     mu_z, sigma_z = (np.mean(mag_z), np.std(mag_z, ddof=1)) if len(mag_z) > 1 else (0, 0)
            #     print("[DEBUG] calling mag_widget.update_stats")
            #     self.mag_widget.update_stats(mu_x, sigma_x, mu_y, sigma_y, mu_z, sigma_z)
            #     # Accéléromètre
            #     acc_x = [d['accelerometer']['x'] for d in buffer]
            #     acc_y = [d['accelerometer']['y'] for d in buffer]
            #     acc_z = [d['accelerometer']['z'] for d in buffer]
            #     mu_x, sigma_x = (np.mean(acc_x), np.std(acc_x, ddof=1)) if len(acc_x) > 1 else (0, 0)
            #     mu_y, sigma_y = (np.mean(acc_y), np.std(acc_y, ddof=1)) if len(acc_y) > 1 else (0, 0)
            #     mu_z, sigma_z = (np.mean(acc_z), np.std(acc_z, ddof=1)) if len(acc_z) > 1 else (0, 0)
            #     print("[DEBUG] calling acc_widget.update_stats")
            #     self.acc_widget.update_stats(mu_x, sigma_x, mu_y, sigma_y, mu_z, sigma_z)
            #     # Gyroscope
            #     gyr_x = [d['gyroscope']['x'] for d in buffer]
            #     gyr_y = [d['gyroscope']['y'] for d in buffer]
            #     gyr_z = [d['gyroscope']['z'] for d in buffer]
            #     mu_x, sigma_x = (np.mean(gyr_x), np.std(gyr_x, ddof=1)) if len(gyr_x) > 1 else (0, 0)
            #     mu_y, sigma_y = (np.mean(gyr_y), np.std(gyr_y, ddof=1)) if len(gyr_y) > 1 else (0, 0)
            #     mu_z, sigma_z = (np.mean(gyr_z), np.std(gyr_z, ddof=1)) if len(gyr_z) > 1 else (0, 0)
            #     print("[DEBUG] calling gyr_widget.update_stats")
            #     self.gyr_widget.update_stats(mu_x, sigma_x, mu_y, sigma_y, mu_z, sigma_z)
            #     # LIDAR
            #     lidar_vals = [d['lidar'] for d in buffer]
            #     mu, sigma = (np.mean(lidar_vals), np.std(lidar_vals, ddof=1)) if len(lidar_vals) > 1 else (0, 0)
            #     print("[DEBUG] calling lidar_widget.update_stats")
            #     self.lidar_widget.update_stats(mu, sigma)
            
        except Exception as e:
            print(f"Erreur mise à jour affichage: {e}")
    
    def update_graph_visibility(self):
        # Masquer/afficher les courbes selon les checkboxes (onglet 2)
        for name, cb in self.graph_checkboxes.items():
            visible = cb.isChecked()
            if name.startswith("M"):
                if name == "Mx":
                    self.mag_plot.curve_x.setVisible(visible)
                elif name == "My":
                    self.mag_plot.curve_y.setVisible(visible)
                elif name == "Mz":
                    self.mag_plot.curve_z.setVisible(visible)
            elif name.startswith("A"):
                if name == "Ax":
                    self.acc_plot.curve_x.setVisible(visible)
                elif name == "Ay":
                    self.acc_plot.curve_y.setVisible(visible)
                elif name == "Az":
                    self.acc_plot.curve_z.setVisible(visible)
            elif name.startswith("G"):
                if name == "Gx":
                    self.gyr_plot.curve_x.setVisible(visible)
                elif name == "Gy":
                    self.gyr_plot.curve_y.setVisible(visible)
                elif name == "Gz":
                    self.gyr_plot.curve_z.setVisible(visible)
            elif name == "LIDAR":
                self.lidar_plot.curve.setVisible(visible)

    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        self.manager.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Style de l'application
    app.setStyle('Fusion')
    
    # Palette de couleurs sombre
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Créer et afficher l'interface
    window = LSM9D_GUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 