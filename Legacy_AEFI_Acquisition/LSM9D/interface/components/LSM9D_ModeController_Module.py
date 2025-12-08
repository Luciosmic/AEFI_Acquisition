#!/usr/bin/env python3
"""
Mode Controller - Gestion des 2 modes d'acquisition

Classe principale pour gérer les transitions entre :
- Mode EXPLORATION (Temps Réel) : Interface réactive
- Mode EXPORT (Mesures) : Interface verrouillée
"""

from enum import Enum
from typing import Dict, Any, Tuple, Optional
import hashlib
import json
from PyQt5.QtCore import QObject, pyqtSignal


class AcquisitionMode(Enum):
    """Modes d'acquisition supportés"""
    EXPLORATION = "exploration"
    EXPORT = "export"


class ModeController(QObject):
    """
    Contrôleur principal pour la gestion des modes d'acquisition
    
    Responsabilités :
    - Transitions EXPLORATION ↔ EXPORT
    - Validation configuration
    - Sauvegarde/restauration état
    - Émission signaux PyQt5
    """
    
    # Signaux PyQt5
    mode_changed = pyqtSignal(AcquisitionMode)
    configuration_changed = pyqtSignal(dict)
    transition_failed = pyqtSignal(str)
    
    def __init__(self, serial_communicator=None):
        """
        Initialisation du contrôleur
        
        Args:
            serial_communicator: Instance de communication série
        """
        super().__init__()
        
        # État interne
        self.current_mode = AcquisitionMode.EXPLORATION
        self._serial_communicator = serial_communicator
        self._current_configuration = {
            'gain_dds': 5000,
            'freq_hz': 1000.0,
            'n_avg': 10
        }
        self._saved_configuration = None
        
        # Chargement configuration initiale si communicateur disponible
        if self._serial_communicator and hasattr(self._serial_communicator, 'memory_state'):
            try:
                stored_config = self._serial_communicator.memory_state.get('config', {})
                self._current_configuration.update(stored_config)
            except Exception:
                pass  # Utiliser config par défaut
    
    def get_current_configuration(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle"""
        return self._current_configuration.copy()
    
    def validate_configuration(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valide une configuration
        
        Args:
            config: Configuration à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            # Validation gain_dds (0-16376)
            gain_dds = config.get('gain_dds', 0)
            if not (0 <= gain_dds <= 16376):
                return False, f"gain_dds doit être entre 0 et 16376, reçu : {gain_dds}"
            
            # Validation freq_hz (0.1-1MHz)
            freq_hz = config.get('freq_hz', 0)
            if not (0.1 <= freq_hz <= 1000000.0):
                return False, f"freq_hz doit être entre 0.1 et 1000000 Hz, reçu : {freq_hz}"
            
            # Validation n_avg (> 0)
            n_avg = config.get('n_avg', 0)
            if n_avg <= 0:
                return False, f"n_avg doit être > 0, reçu : {n_avg}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Erreur validation : {e}"
    
    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration (mode EXPLORATION uniquement)
        
        Args:
            config: Nouvelle configuration
            
        Returns:
            True si succès
        """
        if self.current_mode != AcquisitionMode.EXPLORATION:
            return False
        
        # Validation
        is_valid, error_msg = self.validate_configuration(config)
        if not is_valid:
            return False
        
        try:
            # Mise à jour
            self._current_configuration.update(config)
            
            # Signal changement
            self.configuration_changed.emit(self._current_configuration.copy())
            
            return True
            
        except Exception:
            return False
    
    def request_export_mode(self, export_config: Dict[str, Any]) -> bool:
        """
        Demande transition vers mode EXPORT
        
        Args:
            export_config: Configuration export
            
        Returns:
            True si transition réussie
        """
        if self.current_mode == AcquisitionMode.EXPORT:
            return True
        
        try:
            # Sauvegarde configuration actuelle
            self._saved_configuration = self._current_configuration.copy()
            
            # Application configuration export
            success = self._apply_export_configuration(export_config)
            if not success:
                # Rollback
                self._saved_configuration = None
                return False
            
            # Transition
            self.current_mode = AcquisitionMode.EXPORT
            self.mode_changed.emit(AcquisitionMode.EXPORT)
            
            return True
            
        except Exception as e:
            # Rollback
            self._saved_configuration = None
            self.transition_failed.emit(str(e))
            return False
    
    def return_to_exploration(self) -> bool:
        """
        Retour vers mode EXPLORATION
        
        Returns:
            True si succès
        """
        if self.current_mode == AcquisitionMode.EXPLORATION:
            return True
        
        try:
            # Restauration configuration
            if self._saved_configuration:
                self._current_configuration = self._saved_configuration.copy()
                self._saved_configuration = None
            
            # Transition
            self.current_mode = AcquisitionMode.EXPLORATION
            self.mode_changed.emit(AcquisitionMode.EXPLORATION)
            
            return True
            
        except Exception as e:
            self.transition_failed.emit(str(e))
            return False
    
    def get_configuration_hash(self, config: Dict[str, Any]) -> str:
        """
        Génère un hash MD5 de la configuration pour traçabilité
        
        Args:
            config: Configuration à hasher
            
        Returns:
            Hash MD5 en hexadécimal
        """
        # Tri des clés pour hash reproductible
        sorted_config = {k: config[k] for k in sorted(config.keys())}
        config_str = json.dumps(sorted_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _apply_export_configuration(self, export_config: Dict[str, Any]) -> bool:
        """
        Applique la configuration export (stub)
        
        Args:
            export_config: Configuration export
            
        Returns:
            True si succès
        """
        # Validation basique
        required_keys = ['export_dir', 'export_filename', 'duration_seconds']
        for key in required_keys:
            if key not in export_config:
                return False
        
        # Simulation application
        return True 