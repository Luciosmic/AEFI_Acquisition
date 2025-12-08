#!/usr/bin/env python3
"""
Widget unifié de contrôle du post-processing pour l'UI.
Gère le workflow : offset sans exc → phase avec exc → offset avec exc.
"""

from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QCheckBox, QFrame, QMessageBox, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
import math
import os
import sys
from typing import Dict, Any, List
import numpy as np

# Ajout de l'import pour la connexion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class PostProcessControlWidget(QGroupBox):
    """
    Widget de contrôle unifié du post-processing.
    """
    
    calibration_completed = pyqtSignal(str, dict)  # step, result
    
    # =========================
    # SECTION 1: INITIALISATION
    # =========================
    def __init__(self, parent=None):
        super().__init__("🛠️ Post-Processing", parent)
        self.setStyleSheet("""
            QGroupBox { border: 2px solid #555; border-radius: 5px; margin-top: 1ex; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        self.manager = None  # Référence au MetaManager
        self.compensation_controls = {}
        self._setup_ui()
        self._setup_connections()
        self._reset_values()
    
    # =========================
    # SECTION 2: UI CONSTRUCTION
    # =========================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['RAW', 'PROCESSED'])
        self.mode_combo.setCurrentText('PROCESSED')
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # Compensations
        compensations = [
            ("Offset sans excitation", "offset_exc_off"),
            ("Correction de phase", "phase"),
            ("Offset avec excitation", "offset_exc_on"),
            ("Rotation de référentiel", "frame_rotation")
        ]
        
        for label, comp_type in compensations:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            
            set_btn = QPushButton("SET")
            set_btn.setFixedWidth(50)
            on_checkbox = QCheckBox("ON")
            
            row.addWidget(set_btn)
            row.addWidget(on_checkbox)
            row.addStretch()
            
            layout.addLayout(row)
            
            self.compensation_controls[comp_type] = {
                'set_btn': set_btn,
                'on_checkbox': on_checkbox
            }
            
        # Dans __init__, après création des contrôles existants (ajouter autour ligne ~100-120)
        auto_calib_layout = QHBoxLayout()
        
        auto_calib_x_btn = QPushButton("AutoCalib X")
        auto_calib_x_btn.clicked.connect(lambda: self.manager.start_auto_compensation_cycle('xdir'))
        auto_calib_layout.addWidget(auto_calib_x_btn)
        
        auto_calib_y_btn = QPushButton("AutoCalib Y")
        auto_calib_y_btn.clicked.connect(lambda: self.manager.start_auto_compensation_cycle('ydir'))
        auto_calib_layout.addWidget(auto_calib_y_btn)
        
        # Ajouter au layout principal
        layout.addLayout(auto_calib_layout)
            
        # Info display
        self.info_display = QLabel("Aucune information")
        self.info_display.setWordWrap(True)
        layout.addWidget(self.info_display)
        
        layout.addStretch()

    # =========================
    # SECTION 3: CONNEXIONS
    # =========================
    def _setup_connections(self):
        """Connexion des signaux"""

        if hasattr(self, 'mode_combo'):
            self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

    def connect_to_manager(self, manager):
        """Connexion au MetaManager avec gestion des signaux de calibration"""
        self.manager = manager
        
        # Connect calibration completion signals séparés
        if hasattr(self.manager, 'offset_exc_off_calibration_completed'):
            self.manager.offset_exc_off_calibration_completed.connect(
                lambda result: self._on_specific_calibration_completed('offset_exc_off', result)
            )
        if hasattr(self.manager, 'phase_calibration_completed'):
            self.manager.phase_calibration_completed.connect(
                lambda result: self._on_specific_calibration_completed('phase', result)
            )
        if hasattr(self.manager, 'offset_exc_on_calibration_completed'):
            self.manager.offset_exc_on_calibration_completed.connect(
                lambda result: self._on_specific_calibration_completed('offset_exc_on', result)
            )
        if hasattr(self.manager, 'frame_rotation_calibration_completed'):
            self.manager.frame_rotation_calibration_completed.connect(
                lambda result: self._on_specific_calibration_completed('frame_rotation', result)
            )
        
        # Signal générique pour compatibilité (à supprimer plus tard)
        if hasattr(self.manager, 'calibration_completed'):
            self.manager.calibration_completed.connect(self._on_calibration_completed)
        else:
            print("[WARNING] Signal 'calibration_completed' manquant - Saut de connexion")
        
        # Connexion des boutons SET
        for comp_type, controls in self.compensation_controls.items():
            controls['set_btn'].clicked.connect(
                lambda checked, ct=comp_type: self._start_calculation_compensation(ct)
            )
        
        # Connexion des checkboxes ON
        for comp_type, controls in self.compensation_controls.items():
            controls['on_checkbox'].stateChanged.connect(
                lambda state, ct=comp_type: self._toggle_compensation(ct, state == Qt.Checked)
            )
        
        # Connexion au progress signal pour UI feedback
        if hasattr(self.manager, 'auto_compensation_progress'):
            self.manager.auto_compensation_progress.connect(self._on_auto_compensation_progress)
        
        # Connexion du mode
        if hasattr(self, 'mode_combo'):
            self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # Mise à jour initiale
        self._update_info_display()

        if hasattr(self.manager, 'post_processing_changed'):
            self.manager.post_processing_changed.connect(self.update_compensation_states)
    
    # =========================
    # SECTION 4: LOGIQUE MÉTIER
    # =========================

    
    def _on_mode_changed(self, mode):
        """Gère le changement de mode d'affichage"""
        print(f"[PostProcessWidget] Mode changé à: {mode}")
        
        if self.manager:
            # Convertir en booléen pour le post-processing
            enabled = (mode.upper() == 'PROCESSED')
            print(f"[PostProcessWidget] Post-processing {'activé' if enabled else 'désactivé'}")
            
            # Utiliser la méthode appropriée du MetaManager
            if hasattr(self.manager, 'set_post_processing_enabled'):
                self.manager.set_post_processing_enabled(enabled)
                print(f"[PostProcessWidget] set_post_processing_enabled appelé avec {enabled}")
            else:
                print(f"[PostProcessWidget] ERREUR: set_post_processing_enabled non trouvé!")
                # Fallback: utiliser set_display_mode directement
                self.manager.set_display_mode(mode.lower())
        else:
            print(f"[PostProcessWidget] ERREUR: Manager non connecté!")
    
    # =========================
    # SECTION 5: MISE À JOUR UI
    # =========================
    def _update_compensation_display(self):
        """Mise à jour de l'affichage des états des compensations"""
        if self.manager:
            status = self.manager.get_compensation_status()
            # Logique d'affichage existante
    
    def _reset_values(self):
        """Réinitialise les affichages"""
        if hasattr(self, 'info_display'):
            self.info_display.setText("Aucune information")
        
        # Réinitialiser les checkboxes
        for controls in self.compensation_controls.values():
            if hasattr(controls, 'on_checkbox'):
                controls['on_checkbox'].setChecked(False)
    
    # =========================
    # SECTION 6: UTILITAIRES
    # =========================
    def _get_calibration_samples(self):
        """Récupère les échantillons pour la calibration"""
        if self.manager:
            return self.manager.get_latest_samples(100)
        return []

    def _start_calculation_compensation(self, compensation_type):
        """Lance une calibration asynchrone via le MetaManager"""
        print(f"[UI] Demande calibration: {compensation_type}")
        
        if self.manager:
            # Disable SET button during calibration
            self.compensation_controls[compensation_type]['set_btn'].setEnabled(False)
            self.compensation_controls[compensation_type]['set_btn'].setText("...")
            
            # Send request to MetaManager
            self.manager.request_calibration(compensation_type)
            
            # Info message
            QMessageBox.information(self, "Calibration", 
                                  f"Calibration {compensation_type} en cours...\n"
                                  "Veuillez patienter pendant le remplissage du buffer.")

    def _on_specific_calibration_completed(self, comp_type: str, result: dict):
        """Gère la fin d'une calibration spécifique"""
        print(f"[UI] Calibration spécifique terminée: {comp_type}")
        
        # Re-enable SET button
        if comp_type in self.compensation_controls:
            self.compensation_controls[comp_type]['set_btn'].setEnabled(True)
            self.compensation_controls[comp_type]['set_btn'].setText("SET")
            
            # Update ON checkbox if successful
            if result:
                self.compensation_controls[comp_type]['on_checkbox'].setChecked(True)
        
        # Update display
        self._update_info_display()
        
        # Success message
        if result:
            QMessageBox.information(self, "Calibration terminée", 
                                  f"Calibration {comp_type} terminée avec succès!")
        else:
            QMessageBox.warning(self, "Calibration échouée", 
                               f"La calibration {comp_type} a échoué.")

    def _on_calibration_completed(self, comp_type: str, result: dict):
        """Gère la fin d'une calibration (méthode générique pour compatibilité)"""
        print(f"[UI] Calibration générique terminée: {comp_type}")
        self._on_specific_calibration_completed(comp_type, result)

    def _toggle_compensation(self, compensation_type, enabled):
        """Active/désactive une compensation"""
        if self.manager:
            self.manager.toggle_compensation(compensation_type, enabled)
            self._update_info_display()

    def _update_info_display(self):
        """Met à jour l'affichage des informations"""
        if self.manager and hasattr(self, 'info_display'):
            try:
                info = self.manager.get_post_processing_info()
                
                info_text = []
                for comp_type, data in info.items():
                    if comp_type != 'buffer_size':
                        status = "✓" if data.get('active', False) else "✗"
                        values = data.get('values', {})
                        if values:
                            formatted = ", ".join([f"{k}: {v:.2f}" for k, v in values.items() if abs(v) > 0.001])
                            info_text.append(f"{comp_type}: {status} {formatted}")
                
                self.info_display.setText("\n".join(info_text) if info_text else "Aucune compensation active")
                
            except Exception as e:
                self.info_display.setText(f"Erreur: {e}")

    def _on_auto_compensation_progress(self, phase: str, status: str):
        """Gère progression du cycle auto"""
        print(f"[UI] Cycle auto: {phase} - {status}")
        # Ajoute UI feedback, ex. label.setText(f"{phase}: {status}")
        if status == 'completed' and phase == 'cycle_complete':
            QMessageBox.information(self, "Succès", "Cycle auto-calibration terminé!")

    def update_compensation_states(self, compensation_states):
        """Met à jour TOUTES les checkboxes à partir de l'état global"""
        print(f"[UI DEBUG] Réception états compensations: {compensation_states}")
        
        for comp_type, is_active in compensation_states.items():
            if comp_type in self.compensation_controls:
                checkbox = self.compensation_controls[comp_type]['on_checkbox']
                # Déconnecter temporairement pour éviter boucles
                checkbox.blockSignals(True)
                checkbox.setChecked(is_active)
                checkbox.blockSignals(False)
                print(f"[UI DEBUG] Checkbox {comp_type} mise à jour: {is_active}")