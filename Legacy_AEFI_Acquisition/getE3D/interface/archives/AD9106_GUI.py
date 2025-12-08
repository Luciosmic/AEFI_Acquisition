#!/usr/bin/env python3
"""
Interface graphique moderne pour contrôler les 4 DDS AD9106.
Interface élégante avec thème sombre et design professionnel.
"""
import sys
import os
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QTabWidget,
                             QPushButton, QGroupBox, QSpinBox, QStatusBar,
                             QDoubleSpinBox, QMessageBox, QGridLayout, QStyle)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
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

# Couleurs modernes
COLORS = {
    'primary_blue': '#2E86AB',
    'accent_red': '#E63946',
    'success_green': '#2A9D8F',
    'warning_orange': '#F77F00',
    'info_purple': '#A23B72',
    'dark_bg': '#353535',
    'darker_bg': '#252525',
    'text_white': '#FFFFFF',
    'border_gray': '#555555'
}


class DDSControl(QWidget):
    """Widget de contrôle sobre pour un seul DDS."""

    def __init__(self, dds_number: int, communicator: SerialCommunicator, parent: QWidget = None):
        super().__init__(parent)
        self.dds_number = dds_number
        self.communicator = communicator
        self.mode = "AC"  # Toujours AC
        self.init_ui()
        # Initialisation automatique en mode AC
        if dds_number == 1:
            self.communicator.set_dds1_mode("AC")
        elif dds_number == 2:
            self.communicator.set_dds2_mode("AC")
        elif dds_number == 3:
            self.communicator.set_dds3_mode("AC")
        elif dds_number == 4:
            self.communicator.set_dds4_mode("AC")

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Titre sobre
        title = QLabel(f"DDS {self.dds_number}")
        title.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 18px; 
            color: {COLORS['primary_blue']};
            padding: 10px;
            border-bottom: 2px solid {COLORS['primary_blue']};
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Contrôles de paramètres
        self.gain_spin = self._create_parameter_box("Gain", 0, 16376, layout)
        self.phase_spin, self.phase_deg_spin = self._create_phase_box(layout)

        # Bouton d'application moderne (garde l'emoji ✅)
        apply_button = QPushButton("✅ Appliquer")
        apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success_green']};
                color: {COLORS['text_white']};
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #1a7a6f;
            }}
            QPushButton:pressed {{
                background-color: #155f57;
            }}
        """)
        apply_button.setToolTip("Applique Gain et Phase pour ce DDS")
        apply_button.clicked.connect(self.apply_parameters)
        layout.addWidget(apply_button)

    def _create_parameter_box(self, name: str, min_val: int, max_val: int, parent_layout: QVBoxLayout) -> QSpinBox:
        group = QGroupBox(name)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['primary_blue']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['primary_blue']};
            }}
        """)
        
        layout = QGridLayout(group)
        spin_box = QSpinBox()
        spin_box.setRange(min_val, max_val)
        spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border_gray']};
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['primary_blue']};
                border-radius: 2px;
            }}
        """)
        spin_box.editingFinished.connect(self.apply_parameters)
        
        layout.addWidget(QLabel("Valeur:"), 0, 0)
        layout.addWidget(spin_box, 0, 1)
        layout.addWidget(QLabel(f"({min_val}-{max_val})"), 0, 2)
        parent_layout.addWidget(group)
        return spin_box

    def _create_phase_box(self, parent_layout: QVBoxLayout) -> Tuple[QSpinBox, QSpinBox]:
        group = QGroupBox("Phase")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['info_purple']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['darker_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['info_purple']};
            }}
        """)
        
        layout = QGridLayout(group)
        
        # SpinBox pour la valeur numérique
        spin_box = QSpinBox()
        spin_box.setRange(0, 65535)
        spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border_gray']};
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['info_purple']};
                border-radius: 2px;
            }}
        """)
        spin_box.valueChanged.connect(self.on_phase_changed)
        spin_box.editingFinished.connect(self.apply_parameters)
        
        # SpinBox pour les degrés
        deg_spin_box = QSpinBox()
        deg_spin_box.setRange(0, 360)
        deg_spin_box.setSuffix("°")
        deg_spin_box.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border_gray']};
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['info_purple']};
                border-radius: 2px;
            }}
        """)
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
        self.phase_deg_spin.blockSignals(True)
        self.phase_deg_spin.setValue(degrees)
        self.phase_deg_spin.blockSignals(False)

    def on_deg_changed(self, degrees: int):
        """Met à jour la valeur numérique quand les degrés changent."""
        value = round(degrees * 65535 / 360)
        self.phase_spin.blockSignals(True)
        self.phase_spin.setValue(value)
        self.phase_spin.blockSignals(False)

    def apply_parameters(self):
        self.communicator.set_dds_gain(self.dds_number, self.gain_spin.value())
        self.communicator.set_dds_phase(self.dds_number, self.phase_spin.value())
        print(f"✅ Paramètres appliqués pour DDS{self.dds_number}")


class MainApp(QMainWindow):
    """Fenêtre principale moderne de l'application."""

    def __init__(self):
        super().__init__()
        self.communicator = SerialCommunicator()
        self.init_ui()
        self.apply_dark_theme()
        self.enable_controls(False)

    def apply_dark_theme(self):
        """Applique le thème sombre moderne."""
        QApplication.setStyle('Fusion')
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.setPalette(palette)

    def init_ui(self):
        """Initialise la fenêtre principale avec design moderne et sobre."""
        self.setWindowTitle("Contrôleur DDS AD9106")
        self.setGeometry(100, 100, 1200, 900)
        
        # Widget central avec onglets
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Barre de contrôle principale
        main_layout.addWidget(self._create_control_bar())
        
        # Onglet unique pour le contrôle DDS
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {COLORS['border_gray']};
                border-radius: 8px;
                background-color: {COLORS['dark_bg']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary_blue']};
                font-weight: bold;
            }}
        """)
        
        # Onglet de contrôle principal
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        control_layout.addWidget(self._create_dds_group())
        tab_widget.addTab(control_tab, "Contrôle DDS")
        
        main_layout.addWidget(tab_widget)

        # Barre de statut moderne
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                border-top: 1px solid {COLORS['border_gray']};
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🔴 Non connecté")

        self.setCentralWidget(central_widget)

    def _create_control_bar(self) -> QGroupBox:
        """Crée la barre de contrôle principale."""
        group = QGroupBox("🎮 Contrôles Principaux")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['primary_blue']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['primary_blue']};
            }}
        """)
        
        layout = QHBoxLayout(group)
        layout.setSpacing(15)

        # Sélection du port
        port_label = QLabel("🔌 Port:")
        port_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.port_combo = QComboBox()
        self.port_combo.addItems([f"COM{i}" for i in range(1, 21)])
        self.port_combo.setCurrentText("COM10")
        self.port_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border_gray']};
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['text_white']};
            }}
        """)

        # Bouton de connexion
        self.connect_button = QPushButton("🔌 Connecter")
        self.connect_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success_green']};
                color: {COLORS['text_white']};
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #1a7a6f;
            }}
            QPushButton:pressed {{
                background-color: #155f57;
            }}
        """)
        self.connect_button.clicked.connect(self.toggle_connection)

        # Contrôle de fréquence
        freq_label = QLabel("📡 Fréquence:")
        freq_label.setStyleSheet(f"color: {COLORS['text_white']}; font-weight: bold;")
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1_000_000)
        self.freq_spin.setValue(1000)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {COLORS['darker_bg']};
                color: {COLORS['text_white']};
                border: 1px solid {COLORS['border_gray']};
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {COLORS['primary_blue']};
                border-radius: 2px;
            }}
        """)
        
        self.set_freq_button = QPushButton("📡 Définir")
        self.set_freq_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary_blue']};
                color: {COLORS['text_white']};
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1e6b8a;
            }}
        """)
        self.set_freq_button.clicked.connect(self.set_frequency)

        # Assemblage du layout
        layout.addWidget(port_label)
        layout.addWidget(self.port_combo)
        layout.addWidget(self.connect_button)
        layout.addStretch()
        layout.addWidget(freq_label)
        layout.addWidget(self.freq_spin)
        layout.addWidget(self.set_freq_button)
        
        return group

    def _create_dds_group(self) -> QGroupBox:
        """Crée le groupe de contrôle des DDS avec sobriété et contraste."""
        group = QGroupBox("Configuration des 4 DDS")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS['primary_blue']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {COLORS['text_white']};
                background-color: {COLORS['dark_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {COLORS['primary_blue']};
            }}
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(20)
        
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
        """Gère la connexion/déconnexion avec style moderne."""
        is_connected = self.communicator.ser is not None and self.communicator.ser.is_open
        if not is_connected:
            port = self.port_combo.currentText()
            success, message = self.communicator.connect(port)
            if success:
                self.connect_button.setText("🔌 Déconnecter")
                self.connect_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['accent_red']};
                        color: {COLORS['text_white']};
                        border: none;
                        padding: 10px 20px;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 120px;
                    }}
                    QPushButton:hover {{
                        background-color: #c42e3a;
                    }}
                """)
                self.status_bar.showMessage("🟢 Connecté et prêt")
                self.enable_controls(True)
            else:
                QMessageBox.warning(self, "❌ Erreur de Connexion", message)
        else:
            self.communicator.disconnect()
            self.connect_button.setText("🔌 Connecter")
            self.connect_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['success_green']};
                    color: {COLORS['text_white']};
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: #1a7a6f;
                }}
            """)
            self.status_bar.showMessage("🔴 Déconnecté")
            self.enable_controls(False)

    def enable_controls(self, enabled: bool):
        """Active/désactive les contrôles avec style."""
        self.port_combo.setEnabled(not enabled)
        self.freq_spin.setEnabled(enabled)
        self.set_freq_button.setEnabled(enabled)
        
        # Active/désactive tous les groupes sauf celui de la connexion
        for group in self.findChildren(QGroupBox):
            if "Contrôles Principaux" not in group.title():
                group.setEnabled(enabled)

    def set_frequency(self):
        """Définit la fréquence avec feedback moderne."""
        freq_hz = self.freq_spin.value()
        success, response = self.communicator.set_dds_frequency(freq_hz)
        if not success:
            QMessageBox.warning(self, "❌ Erreur", f"Fréquence: {response}")
            self.status_bar.showMessage("❌ Erreur de configuration de fréquence")
        else:
            self.status_bar.showMessage(f"✅ Fréquence configurée à {freq_hz} Hz")
            print(f"✅ Fréquence configurée à {freq_hz} Hz")

    def closeEvent(self, event):
        """Gestion propre de la fermeture."""
        self.communicator.disconnect()
        self.status_bar.showMessage("🔴 Fermeture de l'application")
        event.accept()


def main():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 