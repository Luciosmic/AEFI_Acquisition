#!/usr/bin/env python3
"""
Script d'analyse de l'accéléromètre LSM9D avec contrôleur Arcus Performax 4EX
==============================================================================

Ce script permet de :
- Mesurer le niveau de bruit de l'accéléromètre
- Enregistrer le signal pour une vitesse donnée et étudier l'amplitude en fréquentiel
- Étudier l'influence de l'accélération sur le signal

Auteur: Script d'analyse pour banc d'imagerie EF
Date: 2024
"""

import sys
import os
import json
import csv
import time
import datetime
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional, Tuple

# Configuration centralisée des chemins
from config_paths import setup_paths, get_config, ARCUS_DLL_PATH

# Configurer les chemins d'import
if not setup_paths():
    print("❌ Erreur de configuration des chemins. Vérifiez l'organisation du projet.")
    sys.exit(1)

# Imports des classes principales (après configuration des chemins)
from LSM9D_Backend import LSM9D_Backend
from EFImagingBench_Controller_ArcusPerformax4EXStage import EFImagingStageController

class AccelerometerAnalyzer:
    """
    Analyseur pour l'étude du comportement de l'accéléromètre LSM9D
    en fonction des paramètres de mouvement du contrôleur Arcus Performax.
    """
    
    def __init__(self, lsm9d_port='COM5', arcus_dll_path=None):
        """
        Initialise l'analyseur avec les connexions aux deux systèmes.
        
        :param lsm9d_port: Port série pour le capteur LSM9D
        :param arcus_dll_path: Chemin vers les DLLs Arcus (utilise la config par défaut si None)
        """
        # Utiliser la configuration centralisée
        config = get_config()
        
        self.lsm9d_port = lsm9d_port
        self.arcus_dll_path = arcus_dll_path or str(ARCUS_DLL_PATH)
        
        # Instances des contrôleurs
        self.lsm9d = None
        self.stage_controller = None
        
        # Configuration par défaut pour les expériences
        self.default_config = {
            'acquisition_duration': 10.0,  # secondes
            'sampling_frequency_target': 20,  # Hz (mode ALL_SENSORS)
            'stage_axis': 'x',  # Axe utilisé pour les mouvements
            'data_directory': 'accelerometer_data',
            'experiment_name': 'accelerometer_analysis'
        }
        
        # Historique des expériences
        self.experiment_counter = 0
        self.current_experiment_params = {}
        
        # Créer le répertoire de données si nécessaire
        Path(self.default_config['data_directory']).mkdir(exist_ok=True)
        
    def initialize_systems(self) -> bool:
        """
        Initialise les connexions avec le capteur LSM9D et le contrôleur Arcus.
        
        :return: True si l'initialisation réussit, False sinon
        """
        print("🔧 Initialisation des systèmes...")
        
        try:
            # Initialisation du capteur LSM9D
            print(f"📡 Connexion au capteur LSM9D sur {self.lsm9d_port}...")
            self.lsm9d = LSM9D_Backend(port=self.lsm9d_port, max_data_points=5000)
            
            if not self.lsm9d.connect():
                print("❌ Échec de connexion au capteur LSM9D")
                return False
            
            # Configuration en mode ALL_SENSORS pour avoir tous les capteurs
            if not self.lsm9d.initialize_sensor_mode('ALL_SENSORS'):
                print("❌ Échec d'initialisation du mode ALL_SENSORS")
                return False
            
            print("✅ Capteur LSM9D connecté et configuré en mode ALL_SENSORS")
            
            # Initialisation du contrôleur Arcus
            print(f"🎮 Initialisation du contrôleur Arcus (DLLs: {self.arcus_dll_path})...")
            self.stage_controller = EFImagingStageController(self.arcus_dll_path)
            
            print("✅ Contrôleur Arcus initialisé")
            
            # Affichage des états initiaux
            self._display_initial_status()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def _display_initial_status(self):
        """Affiche l'état initial des systèmes."""
        print("\n📊 État initial des systèmes:")
        
        # État LSM9D
        lsm9d_status = self.lsm9d.get_status()
        print(f"   LSM9D - Connecté: {lsm9d_status['connected']}")
        print(f"   LSM9D - Mode: {lsm9d_status['mode']}")
        print(f"   LSM9D - Port: {lsm9d_status['port']}")
        
        # État Arcus
        try:
            x_pos = self.stage_controller.get_position('x')
            y_pos = self.stage_controller.get_position('y')
            homing_status = self.stage_controller.get_homing_status()
            
            print(f"   Arcus - Position X: {x_pos}")
            print(f"   Arcus - Position Y: {y_pos}")
            print(f"   Arcus - Homing [X,Y,Z,U]: {homing_status}")
            
        except Exception as e:
            print(f"   Arcus - Erreur lecture état: {e}")
    
    def perform_noise_measurement(self, duration: float = 30.0, description: str = "Mesure de bruit statique") -> str:
        """
        Effectue une mesure de bruit de l'accéléromètre avec le système au repos.
        
        :param duration: Durée de la mesure en secondes
        :param description: Description de l'expérience
        :return: Chemin du fichier de données créé
        """
        print(f"\n🔇 Début de la mesure de bruit - {description}")
        print(f"   Durée: {duration}s")
        
        # Paramètres de l'expérience
        experiment_params = {
            'type': 'noise_measurement',
            'description': description,
            'duration': duration,
            'stage_movement': None,
            'stage_parameters': None,
            'timestamp_start': datetime.datetime.now().isoformat(),
            'lsm9d_mode': 'ALL_SENSORS',
            'target_sampling_rate': 20
        }
        
        return self._acquire_data(experiment_params)
    
    def perform_movement_analysis(self, 
                                axis: str = 'x',
                                distance: float = 10000,
                                speed_params: Dict = None,
                                description: str = "Analyse avec mouvement") -> str:
        """
        Effectue une acquisition pendant un mouvement contrôlé du stage.
        
        :param axis: Axe de mouvement ('x' ou 'y')
        :param distance: Distance de mouvement (en steps)
        :param speed_params: Paramètres de vitesse {ls, hs, acc, dec}
        :param description: Description de l'expérience
        :return: Chemin du fichier de données créé
        """
        print(f"\n🏃 Début de l'analyse avec mouvement - {description}")
        print(f"   Axe: {axis.upper()}")
        print(f"   Distance: {distance} steps")
        
        # Paramètres de vitesse par défaut
        if speed_params is None:
            speed_params = {"ls": 10, "hs": 800, "acc": 300, "dec": 300}
        
        # Vérifier que l'axe est homé
        if not self.stage_controller.is_axis_homed(axis):
            print(f"⚠️  L'axe {axis.upper()} n'est pas homé. Lancement du homing...")
            self.stage_controller.home(axis)
        
        # Appliquer les paramètres de vitesse
        applied_params = self.stage_controller.set_axis_params(axis, **speed_params)
        print(f"   Paramètres appliqués: {applied_params}")
        
        # Position initiale
        initial_pos = self.stage_controller.get_position(axis)
        target_pos = initial_pos + distance
        
        print(f"   Position initiale: {initial_pos}")
        print(f"   Position cible: {target_pos}")
        
        # Paramètres de l'expérience
        experiment_params = {
            'type': 'movement_analysis',
            'description': description,
            'stage_movement': {
                'axis': axis,
                'initial_position': initial_pos,
                'target_position': target_pos,
                'distance': distance
            },
            'stage_parameters': applied_params,
            'timestamp_start': datetime.datetime.now().isoformat(),
            'lsm9d_mode': 'ALL_SENSORS',
            'target_sampling_rate': 20
        }
        
        # Estimer la durée basée sur la vitesse
        estimated_duration = abs(distance) / applied_params['hs'] + 2  # +2s de marge
        experiment_params['estimated_duration'] = estimated_duration
        
        # Démarrer l'acquisition en arrière-plan
        acquisition_filename = self._start_data_acquisition(experiment_params)
        
        # Attendre un peu pour s'assurer que l'acquisition a démarré
        time.sleep(1)
        
        # Lancer le mouvement
        print(f"🚀 Lancement du mouvement vers {target_pos}")
        movement_start_time = time.time()
        self.stage_controller.move_to(axis, target_pos)
        
        # Attendre la fin du mouvement
        print("⏳ Attente de la fin du mouvement...")
        self.stage_controller.wait_move(axis, timeout=estimated_duration + 5)
        movement_end_time = time.time()
        
        actual_duration = movement_end_time - movement_start_time
        final_pos = self.stage_controller.get_position(axis)
        
        print(f"✅ Mouvement terminé en {actual_duration:.1f}s")
        print(f"   Position finale: {final_pos}")
        
        # Continuer l'acquisition encore 2 secondes
        time.sleep(2)
        
        # Arrêter l'acquisition
        return self._stop_data_acquisition(acquisition_filename, {
            'movement_start_time': movement_start_time,
            'movement_end_time': movement_end_time,
            'actual_movement_duration': actual_duration,
            'final_position': final_pos
        })
    
    def _acquire_data(self, experiment_params: Dict) -> str:
        """
        Méthode générique d'acquisition de données.
        
        :param experiment_params: Paramètres de l'expérience
        :return: Chemin du fichier de données créé
        """
        # Démarrer l'acquisition
        acquisition_filename = self._start_data_acquisition(experiment_params)
        
        # Attendre la durée spécifiée
        duration = experiment_params.get('duration', 10.0)
        print(f"⏳ Acquisition en cours ({duration}s)...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(0.1)
            # Affichage du progrès
            elapsed = time.time() - start_time
            if elapsed % 5 < 0.1:  # Afficher toutes les 5 secondes
                remaining = duration - elapsed
                print(f"   📊 Temps restant: {remaining:.1f}s")
        
        # Arrêter l'acquisition
        return self._stop_data_acquisition(acquisition_filename)
    
    def _start_data_acquisition(self, experiment_params: Dict) -> str:
        """
        Démarre l'acquisition de données et retourne le nom du fichier.
        
        :param experiment_params: Paramètres de l'expérience
        :return: Nom de base du fichier (sans extension)
        """
        # Générer un nom de fichier unique
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_counter += 1
        
        base_filename = f"{experiment_params['type']}_{timestamp}_{self.experiment_counter:03d}"
        
        # Sauvegarder les paramètres
        self.current_experiment_params = experiment_params.copy()
        self.current_experiment_params['base_filename'] = base_filename
        
        # Effacer les données précédentes et démarrer l'acquisition
        self.lsm9d.clear_data()
        
        if not self.lsm9d.start_streaming():
            raise Exception("Impossible de démarrer le streaming LSM9D")
        
        print(f"📊 Acquisition démarrée - Fichier: {base_filename}")
        return base_filename
    
    def _stop_data_acquisition(self, base_filename: str, additional_data: Dict = None) -> str:
        """
        Arrête l'acquisition et sauvegarde les données.
        
        :param base_filename: Nom de base du fichier
        :param additional_data: Données supplémentaires à ajouter aux paramètres
        :return: Chemin complet du fichier CSV créé
        """
        # Arrêter l'acquisition
        self.lsm9d.stop_streaming()
        
        # Récupérer toutes les données
        all_data = self.lsm9d.get_historical_data()
        timestamps = all_data['timestamps']
        accelerometer_data = all_data['accelerometer']
        magnetometer_data = all_data['magnetometer']
        gyroscope_data = all_data['gyroscope']
        lidar_data = all_data['lidar']
        
        print(f"📊 Acquisition terminée - {len(timestamps)} points collectés")
        
        # Mettre à jour les paramètres avec les résultats
        self.current_experiment_params['timestamp_end'] = datetime.datetime.now().isoformat()
        self.current_experiment_params['actual_data_points'] = len(timestamps)
        
        if timestamps:
            actual_duration = timestamps[-1] - timestamps[0]
            actual_sampling_rate = len(timestamps) / actual_duration if actual_duration > 0 else 0
            self.current_experiment_params['actual_duration'] = actual_duration
            self.current_experiment_params['actual_sampling_rate'] = actual_sampling_rate
        
        if additional_data:
            self.current_experiment_params.update(additional_data)
        
        # Sauvegarder les fichiers
        csv_path = self._save_csv_data(base_filename, timestamps, accelerometer_data, 
                                     magnetometer_data, gyroscope_data, lidar_data)
        json_path = self._save_experiment_parameters(base_filename)
        
        print(f"💾 Données sauvegardées:")
        print(f"   📄 CSV: {csv_path}")
        print(f"   ⚙️  JSON: {json_path}")
        
        return csv_path
    
    def _save_csv_data(self, base_filename: str, timestamps: List, 
                      accelerometer_data: List, magnetometer_data: List,
                      gyroscope_data: List, lidar_data: List) -> str:
        """
        Sauvegarde les données dans un fichier CSV.
        
        :param base_filename: Nom de base du fichier
        :param timestamps: Liste des timestamps
        :param accelerometer_data: Données de l'accéléromètre
        :param magnetometer_data: Données du magnétomètre
        :param gyroscope_data: Données du gyroscope
        :param lidar_data: Données du LIDAR
        :return: Chemin du fichier CSV créé
        """
        csv_filename = f"{self.default_config['data_directory']}/{base_filename}.csv"
        
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'time_relative',
                'acc_x', 'acc_y', 'acc_z',
                'mag_x', 'mag_y', 'mag_z',
                'gyr_x', 'gyr_y', 'gyr_z',
                'lidar'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Calculer le temps relatif
            start_time = timestamps[0] if timestamps else 0
            
            for i in range(len(timestamps)):
                # Vérifier que nous avons des données pour cet index
                acc = accelerometer_data[i] if i < len(accelerometer_data) else {'x': 0, 'y': 0, 'z': 0}
                mag = magnetometer_data[i] if i < len(magnetometer_data) else {'x': 0, 'y': 0, 'z': 0}
                gyr = gyroscope_data[i] if i < len(gyroscope_data) else {'x': 0, 'y': 0, 'z': 0}
                lidar = lidar_data[i] if i < len(lidar_data) else 0
                
                row = {
                    'timestamp': timestamps[i],
                    'time_relative': timestamps[i] - start_time,
                    'acc_x': acc['x'],
                    'acc_y': acc['y'],
                    'acc_z': acc['z'],
                    'mag_x': mag['x'],
                    'mag_y': mag['y'],
                    'mag_z': mag['z'],
                    'gyr_x': gyr['x'],
                    'gyr_y': gyr['y'],
                    'gyr_z': gyr['z'],
                    'lidar': lidar
                }
                writer.writerow(row)
        
        return csv_filename
    
    def _save_experiment_parameters(self, base_filename: str) -> str:
        """
        Sauvegarde les paramètres de l'expérience dans un fichier JSON.
        
        :param base_filename: Nom de base du fichier
        :return: Chemin du fichier JSON créé
        """
        json_filename = f"{self.default_config['data_directory']}/{base_filename}_params.json"
        
        with open(json_filename, 'w') as jsonfile:
            json.dump(self.current_experiment_params, jsonfile, indent=2, ensure_ascii=False)
        
        return json_filename
    
    def cleanup(self):
        """Nettoie les connexions et ferme les systèmes."""
        print("\n🧹 Nettoyage des connexions...")
        
        if self.lsm9d:
            self.lsm9d.stop_streaming()
            self.lsm9d.disconnect()
            print("✅ LSM9D déconnecté")
        
        if self.stage_controller:
            self.stage_controller.close()
            print("✅ Contrôleur Arcus fermé")
        
        print("✅ Nettoyage terminé")

def main():
    """Fonction principale pour tester le script."""
    print("=" * 80)
    print("🔬 ANALYSEUR D'ACCÉLÉROMÈTRE LSM9D - BANC D'IMAGERIE EF")
    print("=" * 80)
    
    # Créer l'analyseur
    analyzer = AccelerometerAnalyzer()
    
    try:
        # Initialiser les systèmes
        if not analyzer.initialize_systems():
            print("❌ Échec de l'initialisation. Arrêt du programme.")
            return
        
        print("\n🎯 Menu des expériences disponibles:")
        print("1. Mesure de bruit statique (30s)")
        print("2. Analyse avec mouvement lent")
        print("3. Analyse avec mouvement rapide")
        print("4. Quitter")
        
        while True:
            choice = input("\nChoisissez une expérience (1-4): ").strip()
            
            if choice == '1':
                analyzer.perform_noise_measurement(
                    duration=30.0, 
                    description="Mesure de bruit - système au repos"
                )
            
            elif choice == '2':
                analyzer.perform_movement_analysis(
                    axis='x',
                    distance=5000,
                    speed_params={"ls": 10, "hs": 200, "acc": 100, "dec": 100},
                    description="Mouvement lent pour analyse fréquentielle"
                )
            
            elif choice == '3':
                analyzer.perform_movement_analysis(
                    axis='x',
                    distance=5000,
                    speed_params={"ls": 10, "hs": 1000, "acc": 500, "dec": 500},
                    description="Mouvement rapide pour analyse fréquentielle"
                )
            
            elif choice == '4':
                break
            
            else:
                print("❌ Choix invalide. Utilisez 1, 2, 3 ou 4.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    finally:
        analyzer.cleanup()
        print("\n👋 Programme terminé")

if __name__ == "__main__":
    main() 