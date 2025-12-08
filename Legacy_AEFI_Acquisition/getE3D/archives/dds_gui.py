#!/usr/bin/env python3
"""
Interface graphique pour contrôler les 2 DDS
Utilise les adresses validées par tests
"""
import sys
import json
import math
import serial
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSlider, QComboBox, 
                            QPushButton, QTabWidget, QGroupBox, QSpinBox, 
                            QDoubleSpinBox, QMessageBox, QCheckBox, QFrame,
                            QFileDialog, QGridLayout)
from PyQt5.QtCore import Qt, QTimer

# Adresses DDS validées par tests
DDS_ADDRESSES = {
    "Frequency": [62, 63],   # 62: MSB, 63: LSB
    "Mode": 39,              # Mode combiné pour DDS1 et DDS2
    "Gain": {1: 53, 2: 52},  # Gain DDS1: 53, Gain DDS2: 52
    "Offset": {1: 37, 2: 36},  # Offset DDS1: 37, Offset DDS2: 36
    "Phase": {1: 67, 2: 66},    # P   hase DDS1: 67, Phase DDS2: 66
    "Const": {1: 49, 2: 48}     # Constante DDS1: 49, Constante DDS2: 48
}

# Valeurs des modes
DDS_MODES = {
    1: {"AC": 49, "DC": 1},          # DDS1: AC = 49, DC = 1
    2: {"AC": 12544, "DC": 256}      # DDS2: AC = 12544, DC = 256
}

# Combinaisons des modes
MODE_COMBINATIONS = {
    "Les deux en DC": 257,            # 1 + 256
    "DDS1 AC, DDS2 DC": 305,         # 49 + 256
    "DDS1 DC, DDS2 AC": 12545,       # 1 + 12544
    "Les deux en AC": 12593          # 49 + 12544
}

class SerialCommunicator:
    """Gère la communication série avec le matériel"""
    
    def __init__(self, port="COM10", baudrate=1500000, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connected = False
    
    def connect(self):
        """Établit la connexion série"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=self.timeout
            )
            self.connected = True
            return True, "Connexion établie"
        except Exception as e:
            self.connected = False
            return False, f"Erreur de connexion: {e}"
    
    def disconnect(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            return True, "Déconnexion réussie"
        return False, "Pas de connexion active"
    
    def send_command(self, cmd):
        """Envoie une commande et retourne la réponse"""
        if not self.connected or not self.ser:
            return False, "Non connecté"
        
        # Ajouter * si nécessaire
        if not cmd.endswith('*'):
            cmd += '*'
        
        try:
            self.ser.write(cmd.encode())
            time.sleep(0.2)  # Attendre la réponse
            
            response = b""
            start_time = time.time()
            while self.ser.in_waiting > 0 or (time.time() - start_time < 0.5):
                if self.ser.in_waiting > 0:
                    response += self.ser.read(self.ser.in_waiting)
                time.sleep(0.05)
            
            return True, response.decode().strip() if response else ""
        except Exception as e:
            return False, f"Erreur d'envoi: {e}"
    
    def set_address(self, address):
        """Sélectionne une adresse"""
        return self.send_command(f"a{address}")
    
    def set_value(self, value):
        """Envoie une valeur à l'adresse précédemment sélectionnée"""
        return self.send_command(f"d{value}")
    
    def configure_parameter(self, address, value):
        """Configure un paramètre en envoyant l'adresse puis la valeur"""
        success, response = self.set_address(address)
        if not success:
            return success, response
        
        return self.set_value(value)

class DDSControl(QWidget):
    """Widget de contrôle pour un DDS spécifique"""
    
    def __init__(self, dds_number, communicator, parent=None):
        super().__init__(parent)
        self.dds_number = dds_number
        self.communicator = communicator
        self.mode = "AC"  # Mode par défaut
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel(f"DDS {self.dds_number}")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Mode (AC/DC)
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["AC", "DC"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Gain
        gain_group = QGroupBox("Gain")
        gain_layout = QGridLayout()
        self.gain_spin = QSpinBox()
        self.gain_spin.setRange(0, 32768)
        self.gain_spin.setValue(0)
        self.gain_spin.valueChanged.connect(self.on_gain_changed)
        
        gain_layout.addWidget(QLabel("Valeur:"), 0, 0)
        gain_layout.addWidget(self.gain_spin, 0, 1)
        gain_layout.addWidget(QLabel("(0-32768)"), 0, 2)
        
        gain_group.setLayout(gain_layout)
        layout.addWidget(gain_group)
        
        # Offset
        offset_group = QGroupBox("Offset")
        offset_layout = QGridLayout()
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 65535)
        self.offset_spin.setValue(0)
        self.offset_spin.valueChanged.connect(self.on_offset_changed)
        
        offset_layout.addWidget(QLabel("Valeur:"), 0, 0)
        offset_layout.addWidget(self.offset_spin, 0, 1)
        offset_layout.addWidget(QLabel("(0-65535)"), 0, 2)
        
        offset_group.setLayout(offset_layout)
        layout.addWidget(offset_group)
        
        # Phase
        phase_group = QGroupBox("Phase")
        phase_layout = QGridLayout()
        self.phase_spin = QSpinBox()
        self.phase_spin.setRange(0, 65535)
        self.phase_spin.setValue(0)
        self.phase_spin.valueChanged.connect(self.on_phase_changed)
        
        phase_layout.addWidget(QLabel("Valeur:"), 0, 0)
        phase_layout.addWidget(self.phase_spin, 0, 1)
        phase_layout.addWidget(QLabel("(0-65535)"), 0, 2)
        
        # Ajouter un label pour les degrés
        self.phase_deg_label = QLabel("0°")
        phase_layout.addWidget(self.phase_deg_label, 1, 1)
        
        phase_group.setLayout(phase_layout)
        layout.addWidget(phase_group)
        
        # Constante DC
        const_group = QGroupBox("Constante DC")
        const_layout = QGridLayout()
        self.const_spin = QSpinBox()
        self.const_spin.setRange(0, 65535)
        self.const_spin.setValue(0)
        self.const_spin.valueChanged.connect(self.on_const_changed)
        
        const_layout.addWidget(QLabel("Valeur:"), 0, 0)
        const_layout.addWidget(self.const_spin, 0, 1)
        const_layout.addWidget(QLabel("(0-65535)"), 0, 2)
        
        const_group.setLayout(const_layout)
        layout.addWidget(const_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        # Bouton d'application
        self.apply_button = QPushButton("Appliquer Configuration")
        self.apply_button.clicked.connect(self.apply_configuration)
        buttons_layout.addWidget(self.apply_button)
        
        # Bouton de mise à zéro
        self.zero_button = QPushButton("Mettre à Zéro")
        self.zero_button.clicked.connect(self.zero_all)
        buttons_layout.addWidget(self.zero_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def on_mode_changed(self, mode):
        """Appelé quand le mode change"""
        self.mode = mode
        
        # Activer/désactiver les contrôles appropriés selon le mode
        is_ac_mode = (mode == "AC")
        self.gain_spin.setEnabled(is_ac_mode)
        self.phase_spin.setEnabled(is_ac_mode)
        self.const_spin.setEnabled(not is_ac_mode)
        self.offset_spin.setEnabled(is_ac_mode)
    
    def on_gain_changed(self, value):
        """Appelé quand le gain change"""
        pass  # Pas besoin de mettre à jour un label
    
    def on_offset_changed(self, value):
        """Appelé quand l'offset change"""
        pass  # Pas besoin de mettre à jour un label
    
    def on_phase_changed(self, value):
        """Appelé quand la phase change"""
        degrees = round(value / 65535 * 360)
        self.phase_deg_label.setText(f"{degrees}°")
    
    def on_const_changed(self, value):
        """Appelé quand la constante DC change"""
        pass  # Pas besoin de mettre à jour un label
    
    def zero_all(self):
        """Met tous les paramètres à zéro"""
        # Mettre les spinboxes à zéro
        self.gain_spin.setValue(0)
        self.offset_spin.setValue(0)
        self.phase_spin.setValue(0)
        self.const_spin.setValue(0)
        
        # Appliquer la configuration
        self.apply_configuration()
        
        QMessageBox.information(self, "Succès", f"Tous les paramètres de DDS{self.dds_number} mis à zéro")
    
    def apply_configuration(self):
        """Applique la configuration au DDS spécifique"""
        # Ces valeurs sont appliquées individuellement
        
        # Gain (seulement si en mode AC)
        if self.mode == "AC":
            gain_value = self.gain_spin.value()
            gain_address = DDS_ADDRESSES["Gain"][self.dds_number]
            print(f"DDS{self.dds_number} - Configuration du gain:")
            print(f"  Adresse: {gain_address}")
            print(f"  Valeur: {gain_value}")
            success, response = self.communicator.configure_parameter(gain_address, gain_value)
            if not success:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la configuration du gain: {response}")
            else:
                print(f"  Réponse: {response}")
            
            # Phase (seulement si en mode AC)
            phase_value = self.phase_spin.value()
            phase_address = DDS_ADDRESSES["Phase"][self.dds_number]
            success, response = self.communicator.configure_parameter(phase_address, phase_value)
            if not success:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la configuration de la phase: {response}")
        
        # Offset (seulement si en mode AC)
        if self.mode == "AC":
            offset_value = self.offset_spin.value()
            offset_address = DDS_ADDRESSES["Offset"][self.dds_number]
            success, response = self.communicator.configure_parameter(offset_address, offset_value)
            if not success:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la configuration de l'offset: {response}")
        
        # Constante (seulement si en mode DC)
        if self.mode == "DC":
            const_value = self.const_spin.value()
            const_address = DDS_ADDRESSES["Const"][self.dds_number]
            success, response = self.communicator.configure_parameter(const_address, const_value)
            if not success:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la configuration de la constante: {response}")
        
        QMessageBox.information(self, "Succès", f"Configuration appliquée pour DDS{self.dds_number}")
    
    def get_mode_value(self):
        """Retourne la valeur numérique du mode actuel"""
        return DDS_MODES[self.dds_number][self.mode]

class MainApp(QMainWindow):
    """Application principale"""
    
    def __init__(self):
        super().__init__()
        
        self.communicator = SerialCommunicator()
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur principale"""
        self.setWindowTitle("Contrôle DDS")
        self.setGeometry(100, 100, 800, 700)
        
        # Widget central
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Section connexion
        connection_group = QGroupBox("Connexion")
        connection_layout = QHBoxLayout()
        
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM10"])
        self.port_combo.setCurrentText("COM10")  # Port par défaut
        
        self.connect_button = QPushButton("Connecter")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        self.status_label = QLabel("Non connecté")
        
        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.status_label)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # Section fréquence
        freq_group = QGroupBox("Fréquence (commune aux deux DDS)")
        freq_layout = QHBoxLayout()
        
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 1000000)
        self.freq_spin.setValue(1000)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.setDecimals(2)
        
        self.set_freq_button = QPushButton("Définir Fréquence")
        self.set_freq_button.clicked.connect(self.set_frequency)
        
        freq_layout.addWidget(QLabel("Fréquence:"))
        freq_layout.addWidget(self.freq_spin)
        freq_layout.addWidget(self.set_freq_button)
        
        freq_group.setLayout(freq_layout)
        main_layout.addWidget(freq_group)
        
        # Section DDS
        dds_group = QGroupBox("Configuration DDS")
        dds_layout = QGridLayout()
        
        # Créer les contrôles pour chaque DDS
        self.dds1_control = DDSControl(1, self.communicator)
        self.dds2_control = DDSControl(2, self.communicator)
        
        # Forcer le mode AC pour les deux DDS
        self.dds1_control.mode_combo.setCurrentText("AC")
        self.dds2_control.mode_combo.setCurrentText("AC")
        
        # Ajouter les contrôles DDS1 dans la première colonne
        dds_layout.addWidget(QLabel("DDS 1"), 0, 0)
        dds_layout.addWidget(self.dds1_control, 1, 0)
        
        # Ajouter les contrôles DDS2 dans la deuxième colonne
        dds_layout.addWidget(QLabel("DDS 2"), 0, 1)
        dds_layout.addWidget(self.dds2_control, 1, 1)
        
        dds_group.setLayout(dds_layout)
        main_layout.addWidget(dds_group)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def toggle_connection(self):
        """Connecte ou déconnecte le port série"""
        if not self.communicator.connected:
            # Connecter
            self.communicator.port = self.port_combo.currentText()
            success, message = self.communicator.connect()
            
            if success:
                self.status_label.setText("Connecté")
                self.connect_button.setText("Déconnecter")
                self.port_combo.setEnabled(False)
                self.enable_controls(True)
                
                # Configurer les deux DDS en mode AC
                mode_value = DDS_MODES[1]["AC"] + DDS_MODES[2]["AC"]
                self.communicator.configure_parameter(39, mode_value)
            else:
                QMessageBox.warning(self, "Erreur de connexion", message)
        else:
            # Déconnecter
            success, message = self.communicator.disconnect()
            
            if success:
                self.status_label.setText("Déconnecté")
                self.connect_button.setText("Connecter")
                self.port_combo.setEnabled(True)
                self.enable_controls(False)
            else:
                QMessageBox.warning(self, "Erreur de déconnexion", message)
    
    def enable_controls(self, enabled):
        """Active ou désactive les contrôles qui nécessitent une connexion"""
        self.set_freq_button.setEnabled(enabled)
        self.dds1_control.setEnabled(enabled)
        self.dds2_control.setEnabled(enabled)
    
    def set_frequency(self):
        """Configure la fréquence commune des DDS"""
        if not self.communicator.connected:
            QMessageBox.warning(self, "Erreur", "Non connecté")
            return
        
        freq_hz = self.freq_spin.value()
        
        # Calcul de la valeur 32 bits pour la fréquence
        freq_value = int(freq_hz * (2**32) / 16_000_000)
        msb = (freq_value >> 16) & 0xFFFF
        lsb = freq_value & 0xFFFF
        
        # Configurer MSB (adresse 62)
        success, response = self.communicator.configure_parameter(62, msb)
        if not success:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la configuration MSB: {response}")
            return
        
        # Configurer LSB (adresse 63)
        success, response = self.communicator.configure_parameter(63, lsb)
        if not success:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la configuration LSB: {response}")
            return
        
        QMessageBox.information(self, "Succès", f"Fréquence configurée à {freq_hz} Hz")

def main():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 