#!/usr/bin/env python3
"""
Widget de contrôle de la correction de phase pour l'interface utilisateur.

Permet de :
- Activer/désactiver la correction de phase
- Afficher les angles de correction actuels
- Lancer une calibration automatique
- Ajuster manuellement les corrections

Auteur: Luis Saluden  
Date: 2025-01-27
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QDoubleSpinBox, QPushButton, QCheckBox,
                             QGroupBox, QFrame, QProgressBar, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont
import math


class PhaseCorrectionWidget(QGroupBox):
    """
    Widget de contrôle de la correction de phase.
    
    Signaux émis :
    - correction_enabled(bool) : Quand la correction est activée/désactivée
    - corrections_changed(dict) : Quand les corrections changent
    - calibration_requested(float) : Demande de calibration avec durée
    """
    
    # Signaux PyQt5
    correction_enabled = pyqtSignal(bool)
    corrections_changed = pyqtSignal(dict)  # {'Ex': radians, 'Ey': radians, 'Ez': radians}
    calibration_requested = pyqtSignal(float)  # durée en secondes
    
    def __init__(self, parent=None):
        super().__init__("📐 Correction de Phase", parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        self._setup_ui()
        self._setup_connections()
        self._set_default_values()
    
    def _setup_ui(self):
        """Construit l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # === Activation ===
        self.enable_checkbox = QCheckBox("Activer la correction de phase")
        self.enable_checkbox.setStyleSheet("QCheckBox { font-weight: normal; }")
        layout.addWidget(self.enable_checkbox)
        
        # === État actuel ===
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("État: Désactivé")
        self.status_label.setStyleSheet("QLabel { font-weight: normal; padding: 5px; }")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_frame)
        
        # === Corrections actuelles ===
        corrections_group = QGroupBox("Angles de correction")
        corrections_group.setStyleSheet("QGroupBox { font-weight: normal; }")
        corrections_layout = QGridLayout(corrections_group)
        
        # Labels et spinboxes pour Ex, Ey, Ez
        self.correction_spinboxes = {}
        axes = ['Ex', 'Ey', 'Ez']
        colors = ['#E63946', '#2A9D8F', '#F77F00']
        
        for i, (axis, color) in enumerate(zip(axes, colors)):
            # Label avec couleur
            label = QLabel(f"{axis}:")
            label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
            corrections_layout.addWidget(label, i, 0)
            
            # Spinbox pour l'angle en degrés
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-180.0, 180.0)
            spinbox.setDecimals(2)
            spinbox.setSingleStep(1.0)
            spinbox.setSuffix("°")
            spinbox.setToolTip(f"Angle de correction pour {axis}")
            self.correction_spinboxes[axis] = spinbox
            corrections_layout.addWidget(spinbox, i, 1)
            
            # Label pour afficher en radians
            rad_label = QLabel("0.000 rad")
            rad_label.setStyleSheet("QLabel { color: #888; font-size: 10px; }")
            self.correction_spinboxes[f"{axis}_rad"] = rad_label
            corrections_layout.addWidget(rad_label, i, 2)
        
        layout.addWidget(corrections_group)
        
        # === Boutons de contrôle ===
        button_layout = QHBoxLayout()
        
        # Bouton de calibration
        self.calibrate_btn = QPushButton("🎯 Calibrer")
        self.calibrate_btn.setToolTip("Lance une calibration automatique (5s)")
        self.calibrate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A9D8F;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #238075;
            }
            QPushButton:pressed {
                background-color: #1a5a53;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        button_layout.addWidget(self.calibrate_btn)
        
        # Bouton reset
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setToolTip("Remet toutes les corrections à zéro")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # === Barre de progression (cachée par défaut) ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
    
    def _setup_connections(self):
        """Configure les connexions des signaux"""
        # Activation/désactivation
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        
        # Changement des valeurs
        for axis in ['Ex', 'Ey', 'Ez']:
            self.correction_spinboxes[axis].valueChanged.connect(
                lambda v, a=axis: self._on_angle_changed(a, v)
            )
        
        # Boutons
        self.calibrate_btn.clicked.connect(self._on_calibrate_clicked)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
    
    def _set_default_values(self):
        """Initialise les valeurs par défaut"""
        for axis in ['Ex', 'Ey', 'Ez']:
            self.correction_spinboxes[axis].setValue(0.0)
        self._update_status()
    
    def _on_enable_changed(self, state):
        """Gestion du changement d'état d'activation"""
        enabled = state == Qt.Checked
        
        # Activer/désactiver les contrôles
        for widget in self.correction_spinboxes.values():
            if isinstance(widget, QDoubleSpinBox):
                widget.setEnabled(enabled)
        
        self.calibrate_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        
        # Émettre le signal
        self.correction_enabled.emit(enabled)
        
        # Mettre à jour l'affichage
        self._update_status()
    
    def _on_angle_changed(self, axis, value_deg):
        """Gestion du changement d'angle"""
        # Conversion en radians
        value_rad = math.radians(value_deg)
        
        # Mise à jour du label radians
        self.correction_spinboxes[f"{axis}_rad"].setText(f"{value_rad:.3f} rad")
        
        # Émettre le signal avec toutes les corrections
        corrections = self.get_corrections()
        self.corrections_changed.emit(corrections)
    
    def _on_calibrate_clicked(self):
        """Lance la calibration"""
        # Confirmation
        reply = QMessageBox.question(
            self, 
            "Calibration de phase",
            "La calibration va acquérir des données pendant 5 secondes.\n"
            "Assurez-vous que le système est dans l'environnement de référence.\n\n"
            "Continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Désactiver les contrôles pendant la calibration
            self.setEnabled(False)
            
            # Afficher la barre de progression
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Timer pour la progression
            self.calibration_timer = QTimer()
            self.calibration_timer.timeout.connect(self._update_calibration_progress)
            self.calibration_steps = 0
            self.calibration_timer.start(100)  # Update toutes les 100ms
            
            # Émettre le signal de calibration
            self.calibration_requested.emit(5.0)  # 5 secondes
    
    def _update_calibration_progress(self):
        """Met à jour la barre de progression pendant la calibration"""
        self.calibration_steps += 1
        progress = min(100, self.calibration_steps * 2)  # 50 steps = 100%
        self.progress_bar.setValue(progress)
        
        if progress >= 100:
            self.calibration_timer.stop()
            QTimer.singleShot(500, self._calibration_complete)
    
    def _calibration_complete(self):
        """Finalise la calibration"""
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        self._update_status()
        
        QMessageBox.information(
            self,
            "Calibration terminée",
            "La calibration de phase a été effectuée avec succès.\n"
            "Les nouvelles corrections ont été appliquées."
        )
    
    def _on_reset_clicked(self):
        """Remet les corrections à zéro"""
        for axis in ['Ex', 'Ey', 'Ez']:
            self.correction_spinboxes[axis].setValue(0.0)
    
    def _update_status(self):
        """Met à jour l'affichage du statut"""
        if self.enable_checkbox.isChecked():
            corrections = self.get_corrections()
            # Vérifier si des corrections sont appliquées
            has_corrections = any(abs(v) > 0.001 for v in corrections.values())
            
            if has_corrections:
                self.status_label.setText("État: ✅ Actif avec corrections")
                self.status_label.setStyleSheet("QLabel { color: #2A9D8F; font-weight: normal; padding: 5px; }")
            else:
                self.status_label.setText("État: ✅ Actif (pas de correction)")
                self.status_label.setStyleSheet("QLabel { color: #F77F00; font-weight: normal; padding: 5px; }")
        else:
            self.status_label.setText("État: ❌ Désactivé")
            self.status_label.setStyleSheet("QLabel { color: #888; font-weight: normal; padding: 5px; }")
    
    # === API Publique ===
    
    def get_corrections(self) -> dict:
        """
        Retourne les corrections actuelles en radians
        
        Returns:
            Dict avec clés 'Ex', 'Ey', 'Ez' et valeurs en radians
        """
        corrections = {}
        for axis in ['Ex', 'Ey', 'Ez']:
            value_deg = self.correction_spinboxes[axis].value()
            corrections[axis] = math.radians(value_deg)
        return corrections
    
    def set_corrections(self, corrections: dict):
        """
        Définit les corrections
        
        Args:
            corrections: Dict avec clés 'Ex', 'Ey', 'Ez' et valeurs en radians
        """
        for axis in ['Ex', 'Ey', 'Ez']:
            if axis in corrections:
                value_rad = corrections[axis]
                value_deg = math.degrees(value_rad)
                self.correction_spinboxes[axis].blockSignals(True)
                self.correction_spinboxes[axis].setValue(value_deg)
                self.correction_spinboxes[axis].blockSignals(False)
                self._on_angle_changed(axis, value_deg)
        
        self._update_status()
    
    def set_enabled_state(self, enabled: bool):
        """Active/désactive la correction"""
        self.enable_checkbox.setChecked(enabled)
    
    def update_from_manager(self, processing_info: dict):
        """
        Met à jour le widget depuis l'état du manager
        
        Args:
            processing_info: Dict retourné par get_post_processing_info()
        """
        if 'phase_correction' in processing_info:
            pc_info = processing_info['phase_correction']
            self.set_enabled_state(pc_info.get('enabled', False))
            self.set_corrections(pc_info.get('corrections', {}))


# === Test standalone ===
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Test Phase Correction Widget")
            self.setGeometry(100, 100, 400, 500)
            
            # Widget central
            self.phase_widget = PhaseCorrectionWidget()
            self.setCentralWidget(self.phase_widget)
            
            # Connexions pour debug
            self.phase_widget.correction_enabled.connect(self.on_correction_enabled)
            self.phase_widget.corrections_changed.connect(self.on_corrections_changed)
            self.phase_widget.calibration_requested.connect(self.on_calibration_requested)
            
            # Activer par défaut pour le test
            self.phase_widget.set_enabled_state(True)
            
            # Définir des valeurs de test
            test_corrections = {
                'Ex': math.radians(45.0),
                'Ey': math.radians(-30.0),
                'Ez': math.radians(15.0)
            }
            self.phase_widget.set_corrections(test_corrections)
        
        def on_correction_enabled(self, enabled):
            print(f"[TEST] Correction enabled: {enabled}")
        
        def on_corrections_changed(self, corrections):
            print(f"[TEST] Corrections changed:")
            for axis, value_rad in corrections.items():
                print(f"  {axis}: {math.degrees(value_rad):.2f}° ({value_rad:.3f} rad)")
        
        def on_calibration_requested(self, duration):
            print(f"[TEST] Calibration requested for {duration} seconds")
            # Simuler la fin de calibration après 5.5s
            QTimer.singleShot(5500, lambda: self.phase_widget.set_corrections({
                'Ex': math.radians(2.5),
                'Ey': math.radians(-1.8),
                'Ez': math.radians(0.7)
            }))
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_()) 