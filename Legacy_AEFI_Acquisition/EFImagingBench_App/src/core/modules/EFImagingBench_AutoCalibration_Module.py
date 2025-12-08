#!/usr/bin/env python3
"""
Module d'auto-calibration pour EFImagingBench.

Gère les cycles automatiques de calibration des compensations
(offset sans excitation → phase → offset avec excitation).

Auteur: Luis Saluden
Date: 2025-01-27
"""

from PyQt5.QtCore import QThread, pyqtSignal
import sys
import os

# Ajout des chemins pour imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from .EFImagingBench_ExcitationDirection_Module import ExcitationConfig


class AutoCalibrationThread(QThread):
    """
    Thread pour l'auto-calibration complète des compensations.
    
    Séquence :
    1. Désactivation de toutes les compensations
    2. Configuration OFF → calcul offset_exc_off
    3. Configuration ON → calcul phase puis offset_exc_on
    4. Activation des compensations calculées
    """
    
    calibration_progress = pyqtSignal(str)
    calibration_completed = pyqtSignal(dict)
    config_request = pyqtSignal(dict)  # Signal pour demander changement config
    
    def __init__(self, meta_manager, direction):
        super().__init__()
        self.meta_manager = meta_manager
        self.direction = direction
        
    def run(self):
        try:
            # 1. Désactiver toutes les compensations
            self.calibration_progress.emit("Désactivation compensations")
            self.meta_manager.post_processor.config.compensation_active.update({
                'offset_exc_off': False,
                'offset_exc_on': False,
                'phase': False
            })
            
            # 2. Configuration OFF
            self.calibration_progress.emit("Configuration OFF")
            off_config = ExcitationConfig.get_config('off')
            self.config_request.emit(off_config)
            QThread.msleep(2000)
            
            # 3. Calcul et activation offset_exc_off
            self.calibration_progress.emit("Calcul offset_exc_off")
            QThread.msleep(2000)
            result = self.meta_manager.request_buffer_calibration('offset_exc_off')
            self.meta_manager.post_processor.config.compensation_active['offset_exc_off'] = True  # Activer immédiatement
            
            # 4. Configuration ON
            self.calibration_progress.emit("Configuration ON")
            # Vider le buffer pour forcer régénération
            self.meta_manager.post_processor.processed_data_buffer.clear_buffer()

            dir_config = ExcitationConfig.get_config(self.direction)
            self.config_request.emit(dir_config)
            QThread.msleep(3000)
            
            # 5. Calcul et activation phase
            self.calibration_progress.emit("Calcul phase")
            result = self.meta_manager.request_buffer_calibration('phase')
            self.meta_manager.post_processor.config.compensation_active['phase'] = True  # Activer immédiatement

            # 6. Calcul et activation offset_exc_on
            self.calibration_progress.emit("Calcul offset_exc_on")
            # Vider le buffer pour forcer régénération avec phase active
            self.meta_manager.post_processor.processed_data_buffer.clear_buffer()
            QThread.msleep(3000)  # Temps pour remplissage avec compensation phase
            result = self.meta_manager.request_buffer_calibration('offset_exc_on')
            self.meta_manager.post_processor.config.compensation_active['offset_exc_on'] = True
            # 7. Signal final pour synchroniser l'UI
            final_state = {
                'offset_exc_off': True,
                'phase': True,
                'offset_exc_on': True
            }
            self.calibration_completed.emit(final_state)
            
        except Exception as e:
            print(f"[CALIB ERROR] {e}")
