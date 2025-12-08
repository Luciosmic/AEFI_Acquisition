#!/usr/bin/env python3
"""
Caractérisation des signaux parasites
- Balayage en fréquence
- Acquisition des signaux parasites
- Génération des fonctions de compensation
"""

import time
import json
from datetime import datetime
from typing import List, Optional, Dict
import numpy as np
from pathlib import Path
import sys
import os

# Configuration des chemins d'import
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Remonte à la racine du projet (EFImagingBench_App)
src_dir = project_root / "src"

# Ajout des chemins au PYTHONPATH
paths_to_add = [
    str(project_root),
    str(src_dir),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"[DEBUG] Added to PYTHONPATH: {path}")

# Import du module de post-processing (import absolu)
from EFImagingBench_ParasiticsSignals_PostProcess import process_parasitic_signals

class ParasiticSignalsCharacterizer:
    """
    Caractérisation des signaux parasites pour compensation
    """
    def __init__(self, port="COM10"):
        """
        Initialisation du caractériseur
        
        Args:
            port: Port série du hardware
        """
        self.port = port
        self._acquisition_manager = None
        self._output_dir = None
        
    def connect_hardware(self) -> bool:
        """
        Connexion au hardware d'acquisition
        
        Returns:
            bool: True si connexion réussie
        """
        try:
            # Import avec chemin complet depuis src/
            from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager
            from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample
            from core.AD9106_ADS131A04_ElectricField_3D.controller.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
            
            self._acquisition_manager = AcquisitionManager(port=self.port)
            print("✅ Hardware connecté")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion hardware: {e}")
            import traceback
            print("Détails de l'erreur:")
            traceback.print_exc()
            return False
            
    def generate_frequency_list(self, f_min=10, f_max=500000, points_per_decade=20) -> List[float]:
        """
        Génère une liste de fréquences logarithmique
        
        Args:
            f_min: Fréquence minimale (Hz)
            f_max: Fréquence maximale (Hz)
            points_per_decade: Points par décade
            
        Returns:
            List[float]: Liste des fréquences
        """
        decades = np.log10(f_max) - np.log10(f_min)
        n_points = int(decades * points_per_decade)
        frequencies = np.logspace(np.log10(f_min), np.log10(f_max), n_points)
        return frequencies.tolist()
        
    def acquire_at_frequency(self, frequency_hz: float, buffer_size=5) -> Optional[Dict]:
        """
        Acquisition à une fréquence donnée en utilisant update_configuration
        
        Args:
            frequency_hz: Fréquence d'excitation (Hz)
            buffer_size: Nombre d'échantillons à moyenner
            
        Returns:
            Dict: Résultats de l'acquisition ou None si erreur
        """
        if not self._acquisition_manager:
            print("❌ Hardware non connecté")
            return None
            
        try:
            # Mise à jour de la configuration (l'AcquisitionManager gère la pause/reprise)
            config_update = {
                'freq_hz': frequency_hz
            }
            
            success = self._acquisition_manager.update_configuration(config_update)
            if not success:
                print(f"❌ Erreur mise à jour configuration pour {frequency_hz} Hz")
                return None
            
            # Attente que la nouvelle configuration soit appliquée et stabilisée
            # Le manager gère automatiquement la pause/reprise et les délais
            time.sleep(1.0)  # Délai de stabilisation après changement de fréquence
            
            # Vider le buffer pour avoir des données propres à cette fréquence
            self._acquisition_manager.clear_buffer()
            time.sleep(0.2)  # Petit délai pour accumulation de nouveaux échantillons
            
            # Acquisition des échantillons
            samples = []
            max_attempts = buffer_size * 2  # Sécurité pour éviter boucle infinie
            attempts = 0
            
            while len(samples) < buffer_size and attempts < max_attempts:
                latest_samples = self._acquisition_manager.get_latest_samples(1)
                if latest_samples:
                    samples.extend(latest_samples)
                else:
                    time.sleep(0.01)  # Petite pause si pas d'échantillon
                attempts += 1
            
            if len(samples) < buffer_size:
                print(f"⚠️ Seulement {len(samples)}/{buffer_size} échantillons acquis")
            
            # Calcul statistiques
            results = self._compute_statistics(samples, frequency_hz)
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur acquisition: {e}")
            return None
            
    def _compute_statistics(self, samples: List, frequency_hz: float) -> Dict:
        """
        Calcule les statistiques sur les échantillons
        
        Args:
            samples: Liste d'échantillons
            frequency_hz: Fréquence d'acquisition
            
        Returns:
            Dict: Statistiques par canal
        """
        # Extraction des valeurs par canal
        channels = {}
        for ch in ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                  'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4']:
            values = [getattr(s, ch) for s in samples]
            channels[ch] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values))
            }
            
        return {
            'frequency_hz': frequency_hz,
            'channels': channels,
            'n_samples': len(samples)
        }
        
    def run_characterization(self, f_min=10, f_max=500000, points_per_decade=20) -> bool:
        """
        Lance la caractérisation complète
        
        Args:
            f_min: Fréquence minimale (Hz)
            f_max: Fréquence maximale (Hz)
            points_per_decade: Points par décade
            
        Returns:
            bool: True si caractérisation réussie
        """
        if not self._acquisition_manager:
            print("❌ Hardware non connecté")
            return False
            
        try:
            # Création dossier de sortie
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            script_dir = Path(__file__).parent
            self._output_dir = script_dir / "data"
            self._output_dir.mkdir(exist_ok=True, parents=True)
            
            # Génération liste fréquences
            frequencies = self.generate_frequency_list(f_min, f_max, points_per_decade)
            print(f"📊 Caractérisation sur {len(frequencies)} fréquences")
            
            # Configuration initiale et démarrage acquisition unique
            initial_config = {
                'freq_hz': frequencies[0],
                'gain_dds': 0,  # Pas d'excitation pour signaux parasites
                'n_avg': 10  # Moyennage hardware maximal
            }
            
            print("🔄 Démarrage acquisition en mode exploration...")
            success = self._acquisition_manager.start_acquisition('exploration', initial_config)
            if not success:
                print("❌ Impossible de démarrer l'acquisition")
                return False
            
            print("✅ Acquisition démarrée - Caractérisation en cours...")
            
            # Acquisition à chaque fréquence (sans redémarrer l'acquisition)
            results = []
            for i, freq in enumerate(frequencies):
                print(f"\r🔄 Fréquence {i+1}/{len(frequencies)}: {freq:.1f} Hz", end="")
                result = self.acquire_at_frequency(freq)
                if result:
                    results.append(result)
                else:
                    print(f"\n❌ Erreur à {freq} Hz")
                    
            print("\n✅ Acquisition terminée")
            
            # Arrêt de l'acquisition
            self._acquisition_manager.stop_acquisition()
            
            # Sauvegarde données brutes
            output_file = self._output_dir / f"{timestamp}_parasitic_signals_characterization.json"
            data = {
                'metadata': {
                    'timestamp': timestamp,
                    'frequencies_hz': frequencies,
                    'f_min': f_min,
                    'f_max': f_max,
                    'points_per_decade': points_per_decade
                },
                'results': results
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Données sauvegardées: {output_file}")
            
            # Post-processing et génération des fonctions de compensation
            print("\n📈 Post-processing des données...")
            interpolation_functions = process_parasitic_signals(str(output_file))  # Conversion en str pour compatibilité
            print("✅ Post-processing terminé")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur caractérisation: {e}")
            # S'assurer que l'acquisition est arrêtée en cas d'erreur
            try:
                self._acquisition_manager.stop_acquisition()
            except:
                pass
            return False
            
    def disconnect(self):
        """Déconnexion propre du hardware"""
        if self._acquisition_manager:
            self._acquisition_manager.close()
            print("👋 Hardware déconnecté")
            
def main():
    """Point d'entrée pour caractérisation"""
    characterizer = ParasiticSignalsCharacterizer()
    if characterizer.connect_hardware():
        try:
            characterizer.run_characterization()
        finally:
            characterizer.disconnect()
            
if __name__ == '__main__':
    main() 