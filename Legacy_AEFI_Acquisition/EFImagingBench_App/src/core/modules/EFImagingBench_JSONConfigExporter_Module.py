#!/usr/bin/env python3
"""
Module d'export JSON des métadonnées de configuration pour EFImagingBench.

Génère un fichier JSON contenant tous les paramètres de configuration
utilisés pendant l'acquisition (scan, hardware, post-processing).

Logique d'usage :
1. Collecte des paramètres depuis tous les managers
2. Export JSON au début du scan
3. Export CSV ensuite avec même nom de base

Auteur: Luis Saluden
Date: 2025-01-27
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class JSONExportConfig:
    """Configuration pour l'export JSON"""
    output_dir: str  # Injecté par le MetaManager
    filename_base: str  # Injecté par le MetaManager (avec timestamp intégré)


class ConfigurationCollector:
    """
    Interface pour la collecte de configuration.
    Respect du principe S (Single Responsibility) : ne fait que collecter.
    """
    
    def collect_scan_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration de scan"""
        raise NotImplementedError
    
    def collect_hardware_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration hardware"""
        raise NotImplementedError
    
    def collect_postprocessing_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration de post-processing"""
        raise NotImplementedError


class LabviewConfigurationCollector(ConfigurationCollector):
    """
    Collecteur de configuration pour compatibilité LabVIEW.
    
    Utilise les mêmes sources de données que PythonConfigurationCollector
    mais applique le formatage spécifique LabVIEW.
    """
    
    def collect_scan_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration de scan - Format LabVIEW"""
        return meta_manager.get_scan_config()
    
    def collect_hardware_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration hardware - Format LabVIEW"""
        return meta_manager.get_hardware_config()
    
    def collect_postprocessing_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration post-processing - Format LabVIEW"""
        return meta_manager.get_postprocessing_config()


class PythonConfigurationCollector(ConfigurationCollector):
    """
    Collecteur de configuration pour la nouvelle version Python.
    
    Format simplifié sans les sections obsolètes LabVIEW.
    Respect du principe O (Open/Closed) : nouvelle implémentation
    sans modifier l'existant.
    """
    
    def collect_scan_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration de scan - Version Python simplifiée"""
        return meta_manager.get_scan_config()
    
    def collect_hardware_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration hardware - Version Python (dds_adc_v2 uniquement)"""
        return meta_manager.get_hardware_config()
    
    def collect_postprocessing_config(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration de post-processing - Version Python simplifiée"""
        return meta_manager.get_postprocessing_config()


class JSONFileWriter:
    """
    Interface pour l'écriture de fichiers JSON.
    Respect du principe I (Interface Segregation) : interface spécialisée.
    """
    
    def write_json(self, data: Dict[str, Any], filepath: str) -> bool:
        """Écrit les données JSON dans un fichier"""
        raise NotImplementedError


class StandardJSONFileWriter(JSONFileWriter):
    """
    Implémentation standard de l'écriture JSON.
    Respect du principe D (Dependency Inversion) : dépend de l'abstraction.
    """
    
    def write_json(self, data: Dict[str, Any], filepath: str) -> bool:
        """Écrit les données JSON avec formatage standard"""
        try:
            # Création du répertoire si nécessaire
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Export JSON avec indentation
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"[JSONFileWriter] Erreur écriture: {e}")
            return False


class EFImagingBenchJSONConfigExporter:
    """
    Orchestrateur principal pour l'export JSON de configuration.
    
    Par défaut utilise LabviewConfigurationCollector pour assurer la 
    rétrocompatibilité avec les exports LabVIEW existants.
    
    Respect de tous les principes SOLID :
    - S: Responsabilité unique = orchestrer l'export
    - O: Extensible via injection de dépendances
    - L: Substitution via interfaces
    - I: Interfaces ségrégées (collector, writer)
    - D: Dépend des abstractions, pas des implémentations
    """
    
    def __init__(self, 
                 collector: ConfigurationCollector = None,
                 writer: JSONFileWriter = None):
        """
        Injection de dépendances pour respecter le principe D.
        
        Args:
            collector: Collecteur de configuration (LabviewConfigurationCollector par défaut)
            writer: Écrivain JSON (StandardJSONFileWriter par défaut)
        """
        self.collector = collector or LabviewConfigurationCollector()
        self.writer = writer or StandardJSONFileWriter()
        self.last_export_filepath = None
        self._last_config_data = {}
    
    def export_config(self, config: JSONExportConfig, meta_manager) -> Optional[str]:
        """
        Exporte la configuration complète en JSON.
        
        Args:
            config: Configuration d'export (immutable)
            meta_manager: MetaManager pour collecte des données
            
        Returns:
            Chemin du fichier exporté ou None si erreur
        """
        try:
            # Collecte de la configuration via le collector injecté
            config_data = self._collect_all_configuration(meta_manager)
            
            
            # Génération du nom de fichier
            filepath = self._generate_filepath(config)
            
            # Écriture via le writer injecté
            success = self.writer.write_json(config_data, str(filepath))
            
            if success:
                self.last_export_filepath = str(filepath)
                self._last_config_data = config_data
                print(f"[JSONConfigExporter] Configuration exportée: {filepath}")
                return str(filepath)
            else:
                return None
                
        except Exception as e:
            print(f"[JSONConfigExporter] Erreur export: {e}")
            return None
    
    def get_last_export_filepath(self) -> Optional[str]:
        """Retourne le chemin du dernier fichier exporté"""
        return self.last_export_filepath
    
    def get_last_config_data(self) -> Dict[str, Any]:
        """Retourne la dernière configuration collectée (copie immutable)"""
        return self._last_config_data.copy()
    
    def _collect_all_configuration(self, meta_manager) -> Dict[str, Any]:
        """Collecte toute la configuration via le collector dans l'ordre LabVIEW exact"""
        
        # Récupération des sections du collector
        postprocessing_config = self.collector.collect_postprocessing_config(meta_manager)
        
        # Construction dans l'ordre exact LabVIEW
        config = {
            "scan_xy": self.collector.collect_scan_config(meta_manager),
            "speeds": self._get_speeds_template(),
            "adc_dds_mux": self.collector.collect_hardware_config(meta_manager),
            "data_fmt": self._get_data_format_template(),
            "offset": postprocessing_config.get("offset", {}),
            "calib": postprocessing_config.get("calib", {}),
            "phase": postprocessing_config.get("phase", {}),
            "bg": postprocessing_config.get("bg", {}),
            "angProj": postprocessing_config.get("angProj", {}),
            "eVer": 1,
            "dds_adc_v2": self._get_dds_adc_v2_template(),
            "VtoVpm": 63600.0,
            "Vpp": 0.0,
            "Vpp0": 0.0,
            "Gexc": 408.6
        }
        
        return config
    
    def _get_speeds_template(self) -> Dict[str, Any]:
        """Template pour les vitesses moteurs"""
        return {
            "x_low": 10,
            "x_high": 800,
            "y_low": 10,
            "y_high": 800
        }
    
    def _get_data_format_template(self) -> List[Dict[str, Any]]:
        """Template pour le format des données - Compatible LabVIEW hardcodé"""
        return [
            {
                "field": "B",
                "unit": "[T]",
                "comp": "XYZ",
                "time": [12, 12, 12],
                "ids": [2, 3, 4],
                "sensor": "B"
            },
            {
                "field": "Acc",
                "unit": "[g]",
                "comp": "XYZ",
                "time": [12, 12, 12],
                "ids": [5, 6, 7],
                "sensor": "B"
            },
            {
                "field": "Gyro",
                "unit": "[dps]",
                "comp": "XYZ",
                "time": [12, 12, 12],
                "ids": [8, 9, 10],
                "sensor": "B"
            },
            {
                "field": "Lidar",
                "unit": "[mm]",
                "comp": " ",
                "time": [12],
                "ids": [11],
                "sensor": "B"
            },
            {
                "field": "Ere",
                "unit": "[V/m]",
                "comp": "123",
                "time": [0, 5, 10],
                "ids": [4, 9, 14],
                "sensor": "E"
            },
            {
                "field": "Eim",
                "unit": "[V/m]",
                "comp": "123",
                "time": [0, 5, 10],
                "ids": [3, 8, 13],
                "sensor": "E"
            }
        ]
    
    def _get_dds_adc_v2_template(self) -> Dict[str, Any]:
        """
        Template pour la configuration DDS/ADC v2 (ACTIVE).
        
        Cette section remplace adc_dds_mux et contient la configuration
        hardware réellement utilisée.
        """
        return {
            "dds1": {
                "gain": 5000,
                "offset": 0,
                "const": 0,
                "phase": 0
            },
            "dds2": {
                "gain": 5000,
                "offset": 0,
                "const": 0,
                "phase": 0
            },
            "dds3": {
                "gain": 10000,
                "offset": 0,
                "const": 0,
                "phase": 16384
            },
            "dds4": {
                "gain": 10000,
                "offset": 0,
                "const": 0,
                "phase": 0
            },
            "type": {
                "dds_1": 49,
                "dds_2": 12544,
                "dds_3": 49,
                "dds_4": 12544
            },
            "dds_freq_hz": 10000.0,
            "clkin": 1,
            "iclk": 1,
            "oversampling_ratio": 0,
            "adc_gain": {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0
            },
            "averaging": 10,
            "graph": {
                "on?": False,
                "adc-1": "135",
                "adc-2": "246"
            }
        }
    
    def _generate_filepath(self, config: JSONExportConfig) -> Path:
        """Génère le chemin de fichier selon la configuration"""
        filename = f"{config.filename_base}_config.json"
        return Path(config.output_dir) / filename


class PythonJSONConfigExporter(EFImagingBenchJSONConfigExporter):
    """
    Exporteur JSON pour la nouvelle version Python.
    
    Génère un JSON simplifié sans les sections obsolètes LabVIEW.
    Hérite de EFImagingBenchJSONConfigExporter pour réutiliser la logique
    mais override _collect_all_configuration pour un format différent.
    
    Respect du principe L (Liskov Substitution) : peut remplacer la classe parent.
    """
    
    def __init__(self, writer: JSONFileWriter = None):
        """
        Initialise avec PythonConfigurationCollector par défaut.
        
        Args:
            writer: Écrivain JSON (StandardJSONFileWriter par défaut)
        """
        super().__init__(
            collector=PythonConfigurationCollector(),
            writer=writer
        )
    
    def _collect_all_configuration(self, meta_manager) -> Dict[str, Any]:
        """Collecte la configuration - Version Python simplifiée"""
        
        # Récupération des sections du collector
        postprocessing_config = self.collector.collect_postprocessing_config(meta_manager)
        
        # Construction JSON Python - remplace adc_dds_mux par dds_adc_v2 en position 3
        config = {
            "scan_xy": self.collector.collect_scan_config(meta_manager),
            "speeds": self._get_speeds_template(),
            "dds_adc_v2": self.collector.collect_hardware_config(meta_manager),  # Position 3, remplace adc_dds_mux
            "data_fmt": self._get_simplified_data_format(),
            "offset": postprocessing_config.get("offset", {}),
            "calib": postprocessing_config.get("calib", {}),
            "phase": postprocessing_config.get("phase", {}),
            "bg": postprocessing_config.get("bg", {}),
            "angProj": postprocessing_config.get("angProj", {}),
            "eVer": 1,
            "VtoVpm": 63600.0,
            "Vpp": 0.0,
            "Vpp0": 0.0,
            "Gexc": 408.6
        }
        
        return config
    
    def _get_simplified_data_format(self) -> List[Dict[str, Any]]:
        """Format de données simplifié pour Python - Uniquement champ E"""
        return [
            {
                "field": "Ere",
                "unit": "[V/m]",
                "comp": "XYZ",
                "time": [0, 5, 10],
                "ids": [1, 2, 3],
                "sensor": "E"
            },
            {
                "field": "Eim",
                "unit": "[V/m]",
                "comp": "XYZ", 
                "time": [0, 5, 10],
                "ids": [4, 5, 6],
                "sensor": "E"
            }
        ]
