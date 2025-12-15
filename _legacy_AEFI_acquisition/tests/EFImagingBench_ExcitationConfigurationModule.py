#!/usr/bin/env python3
"""
Module de configuration des excitations pour le banc EFImaging
Gère les configurations prédéfinies et personnalisées pour les différents axes
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from ..getE3D.instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator

class ExcitationConfiguration:
    """Classe de base pour les configurations d'excitation"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.parameters = {
            "frequency": 1000,  # Hz
            "dds1_phase": 0,    # 0-65535
            "dds2_phase": 0,    # 0-65535
            "dds1_gain": 2500,  # 0-32768
            "dds2_gain": 2500,  # 0-32768
            "dds1_offset": 0,   # 0-65535
            "dds2_offset": 0,   # 0-65535
            "dds1_mode": True,  # True = AC, False = DC
            "dds2_mode": True   # True = AC, False = DC
        }
    
    def to_dict(self) -> Dict:
        """Convertit la configuration en dictionnaire"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExcitationConfiguration':
        """Crée une configuration à partir d'un dictionnaire"""
        config = cls(data["name"], data["description"])
        config.parameters = data["parameters"]
        return config

class ExcitationConfigManager:
    """Gestionnaire des configurations d'excitation"""
    
    def __init__(self, communicator: SerialCommunicator, config_file: str = "excitation_configurations.json"):
        self.communicator = communicator
        self.config_file = config_file
        self.configurations: Dict[str, ExcitationConfiguration] = {}
        self.load_configurations()
        
        # Configurations prédéfinies
        self._init_default_configurations()
    
    def _init_default_configurations(self):
        """Initialise les configurations prédéfinies"""
        # Configuration axe X
        x_config = ExcitationConfiguration("Axe X", "Excitation le long de l'axe X")
        x_config.parameters.update({
            "dds1_phase": 0,
            "dds2_phase": 16384,  # 90 degrés
            "dds1_gain": 2500,
            "dds2_gain": 2500
        })
        self.configurations["axe_x"] = x_config
        
        # Configuration axe Y
        y_config = ExcitationConfiguration("Axe Y", "Excitation le long de l'axe Y")
        y_config.parameters.update({
            "dds1_phase": 0,
            "dds2_phase": 32768,  # 180 degrés
            "dds1_gain": 2500,
            "dds2_gain": 2500
        })
        self.configurations["axe_y"] = y_config
        
        # Configuration axe Z
        z_config = ExcitationConfiguration("Axe Z", "Excitation le long de l'axe Z")
        z_config.parameters.update({
            "dds1_phase": 0,
            "dds2_phase": 49152,  # 270 degrés
            "dds1_gain": 2500,
            "dds2_gain": 2500
        })
        self.configurations["axe_z"] = z_config
    
    def load_configurations(self):
        """Charge les configurations depuis le fichier JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for key, config_data in data.items():
                        self.configurations[key] = ExcitationConfiguration.from_dict(config_data)
            except Exception as e:
                print(f"Erreur lors du chargement des configurations: {str(e)}")
    
    def save_configurations(self):
        """Sauvegarde les configurations dans le fichier JSON"""
        try:
            data = {key: config.to_dict() for key, config in self.configurations.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True, "Configurations sauvegardées avec succès"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {str(e)}"
    
    def apply_configuration(self, config_key: str) -> Tuple[bool, str]:
        """Applique une configuration spécifique"""
        if config_key not in self.configurations:
            return False, f"Configuration '{config_key}' non trouvée"
        
        config = self.configurations[config_key]
        params = config.parameters
        
        try:
            # Configuration de la fréquence
            self.communicator.set_dds_frequency(params["frequency"])
            
            # Configuration des phases
            self.communicator.set_dds_phase(1, params["dds1_phase"])
            self.communicator.set_dds_phase(2, params["dds2_phase"])
            
            # Configuration des gains
            self.communicator.set_dds_gain(1, params["dds1_gain"])
            self.communicator.set_dds_gain(2, params["dds2_gain"])
            
            # Configuration des offsets
            self.communicator.set_dds_offset(1, params["dds1_offset"])
            self.communicator.set_dds_offset(2, params["dds2_offset"])
            
            # Configuration des modes
            self.communicator.set_dds_modes(
                params["dds1_mode"],
                params["dds2_mode"],
                True,  # DDS3 et DDS4 en mode AC par défaut
                True
            )
            
            return True, f"Configuration '{config_key}' appliquée avec succès"
        except Exception as e:
            return False, f"Erreur lors de l'application de la configuration: {str(e)}"
    
    def create_custom_configuration(self, name: str, description: str, parameters: Dict) -> Tuple[bool, str]:
        """Crée une nouvelle configuration personnalisée"""
        if name in self.configurations:
            return False, f"Une configuration avec le nom '{name}' existe déjà"
        
        config = ExcitationConfiguration(name, description)
        config.parameters.update(parameters)
        self.configurations[name] = config
        
        # Sauvegarder les configurations
        success, message = self.save_configurations()
        if not success:
            return False, message
        
        return True, f"Configuration '{name}' créée avec succès"
    
    def get_configuration(self, config_key: str) -> Optional[ExcitationConfiguration]:
        """Récupère une configuration spécifique"""
        return self.configurations.get(config_key)
    
    def list_configurations(self) -> List[str]:
        """Liste toutes les configurations disponibles"""
        return list(self.configurations.keys())

# Test du module si exécuté directement
if __name__ == "__main__":
    # Exemple d'utilisation
    communicator = SerialCommunicator()
    if communicator.connect("COM10"):  # À adapter
        config_manager = ExcitationConfigManager(communicator)
        
        # Appliquer une configuration prédéfinie
        success, message = config_manager.apply_configuration("axe_x")
        print(message)
        
        # Créer une configuration personnalisée
        custom_params = {
            "frequency": 2000,
            "dds1_phase": 8192,  # 45 degrés
            "dds2_phase": 24576,  # 135 degrés
            "dds1_gain": 3000,
            "dds2_gain": 3000
        }
        success, message = config_manager.create_custom_configuration(
            "custom_45_135",
            "Configuration personnalisée avec déphasage de 90 degrés",
            custom_params
        )
        print(message)
        
        # Lister les configurations disponibles
        print("Configurations disponibles:", config_manager.list_configurations())
        
        communicator.disconnect()
    else:
        print("Erreur de connexion") 