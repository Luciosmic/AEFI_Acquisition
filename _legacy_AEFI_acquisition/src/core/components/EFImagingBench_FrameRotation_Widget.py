#!/usr/bin/env python3
"""
Widget de contrôle de rotation de référentiel pour l'interface utilisateur.

Permet de :
- Choisir le référentiel d'affichage (sensor/bench)
- Ajuster les angles de rotation (θx, θy, θz)
- Visualiser l'état actuel de la rotation

Auteur: Luis Saluden  
Date: 2025-01-27
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QDoubleSpinBox, QComboBox, QPushButton, 
                             QGroupBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
import math


class FrameRotationWidget(QGroupBox):
    """
    Widget de contrôle de rotation de référentiel.
    
    Signaux émis :
    - frame_changed(str) : Quand le référentiel d'affichage change
    - angles_changed(float, float, float) : Quand les angles de rotation changent
    """
    
    # Signaux PyQt5
    frame_changed = pyqtSignal(str)  # 'sensor' ou 'bench'
    angles_changed = pyqtSignal(float, float, float)  # theta_x, theta_y, theta_z
    
    def __init__(self, parent=None):
        super().__init__("🔄 Rotation Référentiel", parent)
        self.setFixedWidth(280)  # Widget compact pour s'intégrer à côté du NumericDisplay
        self._setup_ui()
        self._setup_connections()
        
        # Valeurs par défaut (angles théoriques)
        self._set_default_angles()
        
    def _setup_ui(self):
        """Configure l'interface utilisateur du widget."""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # === SÉLECTION RÉFÉRENTIEL D'AFFICHAGE ===
        frame_group = QFrame()
        frame_layout = QHBoxLayout(frame_group)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        
        frame_label = QLabel("Affichage:")
        frame_label.setMinimumWidth(60)
        
        self.frame_combo = QComboBox()
        self.frame_combo.addItems(["bench", "sensor"])
        self.frame_combo.setCurrentText("bench")  # Par défaut : référentiel banc
        self.frame_combo.setToolTip("Référentiel d'affichage des données:\n• bench: Référentiel banc de test\n• sensor: Référentiel capteur brut")
        
        frame_layout.addWidget(frame_label)
        frame_layout.addWidget(self.frame_combo)
        layout.addWidget(frame_group)
        
        # === ANGLES DE ROTATION ===
        angles_group = QGroupBox("Angles de rotation (°)")
        angles_layout = QGridLayout(angles_group)
        angles_layout.setSpacing(5)
        
        # Labels et spinboxes pour les trois angles
        self.angle_spinboxes = {}
        angle_labels = {
            'theta_x': 'θₓ (X):',
            'theta_y': 'θᵧ (Y):',  
            'theta_z': 'θᵤ (Z):'
        }
        
        for i, (key, label_text) in enumerate(angle_labels.items()):
            label = QLabel(label_text)
            label.setMinimumWidth(50)
            
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-360.0, 360.0)
            spinbox.setDecimals(2)
            spinbox.setSuffix("°")
            spinbox.setMinimumWidth(80)
            
            self.angle_spinboxes[key] = spinbox
            
            angles_layout.addWidget(label, i, 0)
            angles_layout.addWidget(spinbox, i, 1)
        
        layout.addWidget(angles_group)
        
        # === BOUTONS D'ACTION ===
        buttons_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setToolTip("Remet les angles aux valeurs théoriques par défaut")
        self.reset_btn.setMaximumWidth(60)
        
        self.apply_btn = QPushButton("Appliquer")
        self.apply_btn.setToolTip("Applique les nouveaux angles de rotation")
        self.apply_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addWidget(self.apply_btn)
        layout.addLayout(buttons_layout)
        
        # === INFORMATIONS STATUS ===
        self.status_label = QLabel("📍 Référentiel: bench")
        self.status_label.setStyleSheet("color: #2E86AB; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Espacement final
        layout.addStretch()
        self.setLayout(layout)
    
    def _setup_connections(self):
        """Configure les connexions de signaux."""
        # Changement de référentiel d'affichage
        self.frame_combo.currentTextChanged.connect(self._on_frame_changed)
        
        # Boutons d'action
        self.reset_btn.clicked.connect(self._on_reset_angles)
        self.apply_btn.clicked.connect(self._on_apply_angles)
        
        # Connexion des spinboxes pour changement auto
        for spinbox in self.angle_spinboxes.values():
            spinbox.valueChanged.connect(self._on_angle_value_changed)
    
    def _set_default_angles(self):
        """Définit les angles théoriques par défaut."""
        default_angles = {
            'theta_x': -45.0,
            'theta_y': math.degrees(math.atan(1 / math.sqrt(2))),  # ≈ 35.26°
            'theta_z': 0.0
        }
        
        for key, value in default_angles.items():
            self.angle_spinboxes[key].setValue(value)
    
    def _on_frame_changed(self, frame: str):
        """Gère le changement de référentiel d'affichage."""
        print(f"[DEBUG FrameRotationWidget] Référentiel changé: {frame}")
        
        # Mise à jour du status
        emoji = "🏭" if frame == "bench" else "📡"
        self.status_label.setText(f"{emoji} Référentiel: {frame}")
        
        # Émission du signal
        self.frame_changed.emit(frame)
    
    def _on_angle_value_changed(self):
        """Réaction au changement d'angle (optionnel : application auto)."""
        # Pour l'instant, on attend l'appui sur "Appliquer"
        # Mais on pourrait activer l'application automatique ici
        pass
    
    def _on_apply_angles(self):
        """Applique les nouveaux angles de rotation."""
        theta_x = self.angle_spinboxes['theta_x'].value()
        theta_y = self.angle_spinboxes['theta_y'].value()
        theta_z = self.angle_spinboxes['theta_z'].value()
        
        print(f"[DEBUG FrameRotationWidget] Application angles: θx={theta_x:.2f}°, θy={theta_y:.2f}°, θz={theta_z:.2f}°")
        
        # Émission du signal
        self.angles_changed.emit(theta_x, theta_y, theta_z)
    
    def _on_reset_angles(self):
        """Remet les angles aux valeurs par défaut."""
        print("[DEBUG FrameRotationWidget] Reset angles vers valeurs théoriques")
        self._set_default_angles()
        # Application automatique après reset
        self._on_apply_angles()
    
    # === API PUBLIQUE ===
    
    def get_current_frame(self) -> str:
        """Retourne le référentiel d'affichage actuel."""
        return self.frame_combo.currentText()
    
    def set_current_frame(self, frame: str):
        """Définit le référentiel d'affichage."""
        if frame in ["sensor", "bench"]:
            self.frame_combo.setCurrentText(frame)
    
    def get_rotation_angles(self) -> dict:
        """Retourne les angles de rotation actuels."""
        return {
            'theta_x': self.angle_spinboxes['theta_x'].value(),
            'theta_y': self.angle_spinboxes['theta_y'].value(),
            'theta_z': self.angle_spinboxes['theta_z'].value()
        }
    
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """Définit les angles de rotation."""
        self.angle_spinboxes['theta_x'].setValue(theta_x)
        self.angle_spinboxes['theta_y'].setValue(theta_y)
        self.angle_spinboxes['theta_z'].setValue(theta_z)
    
    def update_status_from_manager(self, frame: str, angles: dict = None):
        """Met à jour le widget depuis l'état du manager."""
        # Mise à jour référentiel sans émettre de signal
        self.frame_combo.blockSignals(True)
        self.frame_combo.setCurrentText(frame)
        self.frame_combo.blockSignals(False)
        
        # Mise à jour du status
        emoji = "🏭" if frame == "bench" else "📡"
        self.status_label.setText(f"{emoji} Référentiel: {frame}")
        
        # Mise à jour des angles si fournis
        if angles:
            for key in ['theta_x', 'theta_y', 'theta_z']:
                if key in angles:
                    self.angle_spinboxes[key].blockSignals(True)
                    self.angle_spinboxes[key].setValue(angles[key])
                    self.angle_spinboxes[key].blockSignals(False)


# Test du widget si exécuté directement
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Test FrameRotationWidget")
            
            # Widget principal
            central_widget = QWidget()
            layout = QHBoxLayout(central_widget)
            
            # Widget de rotation
            self.rotation_widget = FrameRotationWidget()
            self.rotation_widget.frame_changed.connect(self.on_frame_changed)
            self.rotation_widget.angles_changed.connect(self.on_angles_changed)
            
            layout.addWidget(self.rotation_widget)
            layout.addStretch()
            
            self.setCentralWidget(central_widget)
            self.resize(400, 300)
        
        def on_frame_changed(self, frame):
            print(f"[TEST] Référentiel changé: {frame}")
        
        def on_angles_changed(self, theta_x, theta_y, theta_z):
            print(f"[TEST] Angles changés: θx={theta_x:.2f}°, θy={theta_y:.2f}°, θz={theta_z:.2f}°")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_()) 