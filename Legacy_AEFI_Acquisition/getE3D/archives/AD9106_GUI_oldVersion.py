#!/usr/bin/env python3
"""
Interface graphique pour contrôler les 4 DDS.
Cette version est refactorisée pour utiliser un module de communication
centralisé, assurant une meilleure architecture et maintenance.
"""
import sys
import os
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QGroupBox, QSpinBox,
                             QDoubleSpinBox, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt
from typing import Tuple

# --- Bloc d'importation robuste pour le module de communication ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
except (ImportError, ModuleNotFoundError):
    try:
        from getE3D.instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
    except (ImportError, ModuleNotFoundError):
        QMessageBox.critical(None, "Erreur Critique",
                             "Impossible de trouver le module de communication requis.\n"
                             "Vérifiez l'arborescence du projet et le PYTHONPATH.")
        sys.exit(1)
# --- Fin du bloc d'importation ---


class DDSControl(QWidget):
    """Widget de contrôle pour un seul DDS (mode AC uniquement)."""

    def __init__(self, dds_number: int, communicator: SerialCommunicator, parent: QWidget = None):
        super().__init__(parent)
        self.dds_number = dds_number
        self.communicator = communicator
        self.mode = "AC"  # Toujours AC
        self.init_ui()
        self.communicator.set_dds1_mode("AC") if dds_number == 1 else None
        self.communicator.set_dds2_mode("AC") if dds_number == 2 else None
        self.communicator.set_dds3_mode("AC") if dds_number == 3 else None
        self.communicator.set_dds4_mode("AC") if dds_number == 4 else None

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        title = QLabel(f"DDS {self.dds_number}")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        # Plus de choix de mode
        self.gain_spin = self._create_parameter_box("Gain", 0, 16376, layout)
        self.phase_spin, self.phase_deg_spin = self._create_phase_box(layout)
        apply_button = QPushButton("Appliquer Paramètres")
        apply_button.setToolTip("Applique Gain et Phase pour ce DDS.")
        apply_button.clicked.connect(self.apply_parameters)
        layout.addWidget(apply_button)

    def _create_parameter_box(self, name: str, min_val: int, max_val: int, parent_layout: QVBoxLayout) -> QSpinBox:
        group = QGroupBox(name)
        layout = QGridLayout(group)
        spin_box = QSpinBox()
        spin_box.setRange(min_val, max_val)
        spin_box.editingFinished.connect(self.apply_parameters)
        layout.addWidget(QLabel("Valeur:"), 0, 0)
        layout.addWidget(spin_box, 0, 1)
        layout.addWidget(QLabel(f"({min_val}-{max_val})"), 0, 2)
        parent_layout.addWidget(group)
        return spin_box

    def _create_phase_box(self, parent_layout: QVBoxLayout) -> Tuple[QSpinBox, QSpinBox]:
        group = QGroupBox("Phase")
        layout = QGridLayout(group)
        
        # SpinBox pour la valeur numérique
        spin_box = QSpinBox()
        spin_box.setRange(0, 65535)
        spin_box.valueChanged.connect(self.on_phase_changed)
        spin_box.editingFinished.connect(self.apply_parameters)
        
        # SpinBox pour les degrés
        deg_spin_box = QSpinBox()
        deg_spin_box.setRange(0, 360)
        deg_spin_box.setSuffix("°")
        deg_spin_box.valueChanged.connect(self.on_deg_changed)
        deg_spin_box.editingFinished.connect(self.apply_parameters)
        
        layout.addWidget(QLabel("Valeur:"), 0, 0)
        layout.addWidget(spin_box, 0, 1)
        layout.addWidget(QLabel("(0-65535)"), 0, 2)
        layout.addWidget(QLabel("Degrés:"), 1, 0)
        layout.addWidget(deg_spin_box, 1, 1)
        layout.addWidget(QLabel("(0-360°)"), 1, 2)
        
        parent_layout.addWidget(group)
        return spin_box, deg_spin_box

    def on_phase_changed(self, value: int):
        """Met à jour l'affichage des degrés quand la valeur numérique change."""
        degrees = round(value / 65535 * 360)
        # Éviter la récursion en bloquant temporairement le signal
        self.phase_deg_spin.blockSignals(True)
        self.phase_deg_spin.setValue(degrees)
        self.phase_deg_spin.blockSignals(False)

    def on_deg_changed(self, degrees: int):
        """Met à jour la valeur numérique quand les degrés changent."""
        value = round(degrees * 65535 / 360)
        # Éviter la récursion en bloquant temporairement le signal
        self.phase_spin.blockSignals(True)
        self.phase_spin.setValue(value)
        self.phase_spin.blockSignals(False)

    def apply_parameters(self):
        self.communicator.set_dds_gain(self.dds_number, self.gain_spin.value())
        self.communicator.set_dds_phase(self.dds_number, self.phase_spin.value())
        print(f"Paramètres appliqués pour DDS{self.dds_number}")


class MainApp(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()
        self.communicator = SerialCommunicator()
        self.init_ui()
        self.enable_controls(False)

    def init_ui(self):
        """Initialise la fenêtre principale."""
        self.setWindowTitle("Contrôleur DDS v2.0 (4 canaux)")
        self.setGeometry(100, 100, 900, 800)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        main_layout.addWidget(self._create_connection_group())
        main_layout.addWidget(self._create_common_controls_group())
        main_layout.addWidget(self._create_dds_group())

        self.setCentralWidget(central_widget)

    def _create_connection_group(self) -> QGroupBox:
        group = QGroupBox("Connexion")
        layout = QHBoxLayout(group)
        self.port_combo = QComboBox()
        self.port_combo.addItems([f"COM{i}" for i in range(1, 21)])
        self.port_combo.setCurrentText("COM10")
        self.connect_button = QPushButton("Connecter")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.status_label = QLabel("Non connecté")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.port_combo)
        layout.addWidget(self.connect_button)
        layout.addStretch()
        layout.addWidget(self.status_label)
        return group

    def _create_common_controls_group(self) -> QGroupBox:
        group = QGroupBox("Contrôles Communs")
        layout = QHBoxLayout(group)
        
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1_000_000)
        self.freq_spin.setValue(1000)
        self.freq_spin.setSuffix(" Hz")
        self.set_freq_button = QPushButton("Définir Fréquence")
        self.set_freq_button.clicked.connect(self.set_frequency)
        
        layout.addWidget(QLabel("Fréquence:"))
        layout.addWidget(self.freq_spin)
        layout.addWidget(self.set_freq_button)
        layout.addStretch()
        return group

    def _create_dds_group(self) -> QGroupBox:
        group = QGroupBox("Configuration des DDS")
        layout = QGridLayout(group)
        
        self.dds1_control = DDSControl(1, self.communicator)
        self.dds2_control = DDSControl(2, self.communicator)
        self.dds3_control = DDSControl(3, self.communicator)
        self.dds4_control = DDSControl(4, self.communicator)
        
        layout.addWidget(self.dds1_control, 0, 0)
        layout.addWidget(self.dds2_control, 0, 1)
        layout.addWidget(self.dds3_control, 1, 0)
        layout.addWidget(self.dds4_control, 1, 1)
        return group

    def toggle_connection(self):
        is_connected = self.communicator.ser is not None and self.communicator.ser.is_open
        if not is_connected:
            port = self.port_combo.currentText()
            success, message = self.communicator.connect(port)
            if success:
                self.status_label.setText("Connecté")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.connect_button.setText("Déconnecter")
                self.enable_controls(True)
            else:
                QMessageBox.warning(self, "Erreur", message)
        else:
            self.communicator.disconnect()
            self.status_label.setText("Déconnecté")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_button.setText("Connecter")
            self.enable_controls(False)

    def enable_controls(self, enabled: bool):
        self.port_combo.setEnabled(not enabled)
        # Active/désactive tous les groupes sauf celui de la connexion
        for group in self.findChildren(QGroupBox):
            if group.title() != "Connexion":
                group.setEnabled(enabled)

    def set_frequency(self):
        freq_hz = self.freq_spin.value()
        success, response = self.communicator.set_dds_frequency(freq_hz)
        if not success:
            QMessageBox.warning(self, "Erreur", f"Fréquence: {response}")
        else:
            print(f"Fréquence configurée à {freq_hz} Hz")

    def closeEvent(self, event):
        self.communicator.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 