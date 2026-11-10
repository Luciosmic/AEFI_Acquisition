#!/usr/bin/env python3
"""
Widget de contrôle de la rotation de référentiel
- Activation/désactivation de la rotation
- Choix du référentiel d'affichage
- Configuration des angles de rotation
"""

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class FrameRotationWidget(QGroupBox):
    """
    Widget de contrôle de la rotation de référentiel
    """
    # Signaux
    frame_changed = pyqtSignal(str)  # Émis quand le référentiel change
    angles_changed = pyqtSignal(float, float, float)  # Émis quand les angles changent
    rotation_toggled = pyqtSignal(bool)  # Émis quand la rotation est activée/désactivée
    
    def __init__(self, parent=None):
        super().__init__("🔄 Rotation de Référentiel", parent)
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # === Activation/Désactivation ===
        self.rotation_btn = QPushButton("Rotation Active")
        self.rotation_btn.setCheckable(True)
        self.rotation_btn.setChecked(True)  # Activé par défaut
        layout.addWidget(self.rotation_btn)
        
        # === Choix du référentiel ===
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Référentiel :"))
        self.frame_combo = QComboBox()
        self.frame_combo.addItems(['bench', 'sensor'])
        frame_layout.addWidget(self.frame_combo)
        layout.addLayout(frame_layout)
        
        # === Angles de rotation ===
        angles_group = QGroupBox("Angles de Rotation")
        angles_layout = QVBoxLayout(angles_group)
        
        # Theta X
        theta_x_layout = QHBoxLayout()
        theta_x_layout.addWidget(QLabel("θx (°) :"))
        self.theta_x_spin = QDoubleSpinBox()
        self.theta_x_spin.setRange(-180, 180)
        self.theta_x_spin.setDecimals(1)
        theta_x_layout.addWidget(self.theta_x_spin)
        angles_layout.addLayout(theta_x_layout)
        
        # Theta Y
        theta_y_layout = QHBoxLayout()
        theta_y_layout.addWidget(QLabel("θy (°) :"))
        self.theta_y_spin = QDoubleSpinBox()
        self.theta_y_spin.setRange(-180, 180)
        self.theta_y_spin.setDecimals(1)
        theta_y_layout.addWidget(self.theta_y_spin)
        angles_layout.addLayout(theta_y_layout)
        
        # Theta Z
        theta_z_layout = QHBoxLayout()
        theta_z_layout.addWidget(QLabel("θz (°) :"))
        self.theta_z_spin = QDoubleSpinBox()
        self.theta_z_spin.setRange(-180, 180)
        self.theta_z_spin.setDecimals(1)
        theta_z_layout.addWidget(self.theta_z_spin)
        angles_layout.addLayout(theta_z_layout)
        
        layout.addWidget(angles_group)
        
    def _setup_connections(self):
        """Configure les connexions internes du widget"""
        # Émission des signaux sur changement
        self.frame_combo.currentTextChanged.connect(self.frame_changed)
        self.rotation_btn.toggled.connect(self.rotation_toggled)
        
        # Émission du signal angles_changed quand un angle change
        def emit_angles():
            self.angles_changed.emit(
                self.theta_x_spin.value(),
                self.theta_y_spin.value(),
                self.theta_z_spin.value()
            )
        self.theta_x_spin.valueChanged.connect(emit_angles)
        self.theta_y_spin.valueChanged.connect(emit_angles)
        self.theta_z_spin.valueChanged.connect(emit_angles)
        
    def connect_to_manager(self, manager):
        """
        Connecte le widget au MetaManager
        """
        # Activation/désactivation rotation
        self.rotation_btn.clicked.connect(lambda checked: manager.toggle_frame_rotation(checked))
        
        # Changement de référentiel
        self.frame_combo.currentTextChanged.connect(manager.set_display_frame)
        
        # Mise à jour angles
        def update_angles():
            manager.set_rotation_angles(
                self.theta_x_spin.value(),
                self.theta_y_spin.value(),
                self.theta_z_spin.value()
            )
        self.theta_x_spin.valueChanged.connect(update_angles)
        self.theta_y_spin.valueChanged.connect(update_angles)
        self.theta_z_spin.valueChanged.connect(update_angles)
        
        # Synchronisation initiale
        current_frame = manager.get_display_frame()
        self.frame_combo.setCurrentText(current_frame)
        
        angles = manager.get_rotation_angles()
        self.theta_x_spin.setValue(angles['theta_x'])
        self.theta_y_spin.setValue(angles['theta_y'])
        self.theta_z_spin.setValue(angles['theta_z'])
        
        rotation_enabled = manager.toggle_frame_rotation()  # Récupère l'état actuel
        self.rotation_btn.setChecked(rotation_enabled)
        
    def update_status_from_manager(self, frame: str, angles: dict = None):
        """
        Met à jour l'état du widget depuis le manager
        
        Args:
            frame: Référentiel ('bench'/'sensor')
            angles: Dict optionnel avec theta_x/y/z
        """
        # Mise à jour référentiel
        self.frame_combo.setCurrentText(frame)
        
        # Mise à jour angles si fournis
        if angles is not None:
            self.theta_x_spin.setValue(angles['theta_x'])
            self.theta_y_spin.setValue(angles['theta_y'])
            self.theta_z_spin.setValue(angles['theta_z'])
            
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """
        Met à jour les angles de rotation
        
        Args:
            theta_x, theta_y, theta_z: Angles en degrés
        """
        self.theta_x_spin.setValue(theta_x)
        self.theta_y_spin.setValue(theta_y)
        self.theta_z_spin.setValue(theta_z) 