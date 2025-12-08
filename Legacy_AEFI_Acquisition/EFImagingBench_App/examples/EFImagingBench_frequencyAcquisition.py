#!/usr/bin/env python3
"""
Script d'acquisition en fréquence pour le banc EFImagingBench
- Initialise les connexions
- Configure les paramètres moteur (vitesse à 2000)
- Effectue homing sur les deux axes
- Pour chaque fréquence :
  * Configure la fréquence
  * Va à position X=0, Y=70cm
  * Lance autocalibration sur X
  * Va à position X=70, Y=70cm
  * Acquisition moyennée à 127 échantillons
"""

import sys
import os
import time
import numpy as np
from datetime import datetime

# Ajout des chemins pour importer les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

from EFImagingBench_metaManager import MetaManager
from core.components.EFImagingBench_ExcitationDirection_Module import ExcitationConfig

class FrequencyAcquisition:
    """Classe pour l'acquisition multi-fréquence automatisée"""
    
    def __init__(self):
        """Initialisation du MetaManager"""
        print("🔧 Initialisation du MetaManager...")
        self.mm = MetaManager()
        self.frequencies = []  # Liste des fréquences à tester
        self.results = []      # Résultats des acquisitions
        
    def initialize_connections(self):
        """Initialise les connexions hardware"""
        print("🔗 Initialisation des connexions...")
        
        # Démarrer l'acquisition en mode exploration pour les tests
        initial_config = {
            'freq_hz': 1000,
            'gain_dds': 5000,
            'n_avg': 10
        }
        
        self.mm.set_mode("exploration")
        self.mm.update_configuration(initial_config)
        success = self.mm.start_acquisition('exploration', initial_config)
        
        if success:
            print("✅ Connexions établies avec succès")
            time.sleep(1)  # Temps pour stabilisation
        else:
            print("❌ Erreur lors de l'initialisation des connexions")
            return False
        return True
    
    def configure_motor_speed(self, speed=3000):
        """Configure la vitesse des moteurs (normalement 800 → 2000)"""
        print(f"⚙️ Configuration vitesse moteur à {speed}...")
        
        # Configuration des paramètres pour les deux axes
        # ls = low speed, hs = high speed, acc = acceleration, dec = deceleration
        try:
            # Axe X
            result_x = self.mm.set_axis_params('x', hs=speed, acc=300, dec=300)
            print(f"✅ Axe X configuré (vitesse: {speed})")
            
            # Axe Y  
            result_y = self.mm.set_axis_params('y', hs=speed, acc=300, dec=300)
            print(f"✅ Axe Y configuré (vitesse: {speed})")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur configuration moteur: {e}")
            return False
    
    def perform_homing(self):
        """Effectue le homing sur les deux axes"""
        print("🏠 Démarrage homing des deux axes...")
        
        try:
            # Variable pour capturer le résultat du homing
            self.homing_result = None
            self.homing_completed = False
            
            # Callback pour capturer le résultat
            def on_homing_complete(result):
                self.homing_result = result
                self.homing_completed = True
                print(f"[CALLBACK] Homing terminé avec résultat: {result}")
            
            # Lancer le homing avec callback
            self.mm.managers['stage'].home_both_lock(callback=on_homing_complete)
            
            # Attendre la fin du homing (timeout de 2 minutes)
            timeout = 120  # secondes
            elapsed = 0
            while not self.homing_completed and elapsed < timeout:
                time.sleep(0.5)
                elapsed += 0.5
                if elapsed % 10 == 0:  # Message toutes les 10 secondes
                    print(f"⏳ Homing en cours... ({elapsed}s/{timeout}s)")
            
            if self.homing_completed:
                # Le homing est terminé, vérifier l'état réel des axes
                def check_homing_status(status):
                    self.final_homing_status = status
                    
                self.final_homing_status = None
                self.mm.managers['stage'].get_all_homed_status(callback=check_homing_status)
                
                # Attendre le résultat du status
                status_timeout = 5
                status_elapsed = 0
                while self.final_homing_status is None and status_elapsed < status_timeout:
                    time.sleep(0.1)
                    status_elapsed += 0.1
                
                if self.final_homing_status and len(self.final_homing_status) >= 2:
                    x_homed = self.final_homing_status[0]  # X axis
                    y_homed = self.final_homing_status[1]  # Y axis
                    
                    if x_homed and y_homed:
                        print("✅ Homing terminé avec succès (axes X et Y homed)")
                        time.sleep(1)  # Temps pour stabilisation
                        return True
                    else:
                        print(f"❌ Homing incomplet - X: {x_homed}, Y: {y_homed}")
                        return False
                else:
                    print("✅ Homing terminé (callback reçu, statut non vérifié)")
                    time.sleep(1)  # Temps pour stabilisation  
                    return True
            elif not self.homing_completed:
                print("❌ Timeout du homing (120s)")
                return False
            else:
                print("❌ Échec du homing")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du homing: {e}")
            return False
    
    def configure_frequency(self, frequency_hz):
        """Configure la fréquence d'excitation"""
        print(f"📡 Configuration fréquence: {frequency_hz} Hz")
        
        config = {
            'freq_hz': frequency_hz,
            'gain_dds': 5000,  # Gain standard pour excitation
            'n_avg': 127       # Nombre d'échantillons pour moyennage
        }
        
        self.mm.update_configuration(config)
        time.sleep(0.5)  # Temps pour stabilisation
        print(f"✅ Fréquence configurée: {frequency_hz} Hz")
    
    def move_to_position(self, x_cm, y_cm):
        """Déplace le banc à la position spécifiée (en cm)"""
        print(f"🎯 Déplacement vers position X={x_cm}cm, Y={y_cm}cm")
        
        try:
            # Vérifier les limites du banc
            x_max, y_max = self.mm.get_bench_limits_cm()
            
            if x_cm > x_max or y_cm > y_max or x_cm < 0 or y_cm < 0:
                print(f"❌ Position hors limites (max: {x_max:.1f}cm x {y_max:.1f}cm)")
                return False
            
            # Conversion cm vers incréments (cm_to_inc retourne un tuple)
            x_inc, _ = self.mm.cm_to_inc(x_cm)  # Extraire seulement la valeur entière
            y_inc, _ = self.mm.cm_to_inc(y_cm)  # Extraire seulement la valeur entière
            print(f"   Conversion: X={x_cm}cm → {x_inc}inc, Y={y_cm}cm → {y_inc}inc")
            
            # Déplacement vers la position (en incréments)
            self.mm.move_to('x', x_inc)
            self.mm.move_to('y', y_inc)
            
            # Attendre la fin du déplacement avec wait_move_manager
            print("⏳ Attente fin de déplacement...")
            
            # Attendre l'axe X (en incréments)
            success_x = self.mm.managers['stage'].wait_move_manager('x', x_inc, tol=2, timeout=30)
            if not success_x:
                print("❌ Timeout déplacement axe X")
                return False
            
            # Attendre l'axe Y (en incréments)  
            success_y = self.mm.managers['stage'].wait_move_manager('y', y_inc, tol=2, timeout=30)
            if not success_y:
                print("❌ Timeout déplacement axe Y")
                return False
            
            print(f"✅ Position atteinte: X={x_cm}cm, Y={y_cm}cm")
            time.sleep(0.5)  # Temps de stabilisation supplémentaire
            return True
            
        except Exception as e:
            print(f"❌ Erreur déplacement: {e}")
            return False
    
    def perform_auto_calibration_x(self):
        """Lance l'auto-calibration sur l'axe X"""
        print("🔄 Démarrage auto-calibration direction X...")
        
        try:
            # Lancer le cycle d'auto-calibration pour direction X
            self.mm.start_auto_compensation_cycle('xdir')
            
            # Attendre la fin de la calibration (environ 10-15 secondes)
            print("⏳ Calibration en cours... (patientez ~15s)")
            time.sleep(15)
            
            print("✅ Auto-calibration X terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur auto-calibration: {e}")
            return False
    
    def acquire_averaged_measurement(self, frequency_hz):
        """Effectue l'acquisition moyennée (127 échantillons)"""
        print(f"📊 Acquisition moyennée à {frequency_hz} Hz (n_avg=127)...")
        
        try:
            # Configuration finale avec 127 échantillons de moyenne
            config = {
                'freq_hz': frequency_hz,
                'gain_dds': 5000,
                'n_avg': 127
            }
            
            # Appliquer la configuration d'excitation X
            excitation_config = ExcitationConfig.get_config('xdir')
            config.update(excitation_config)
            
            self.mm.update_configuration(config)
            time.sleep(1)  # Stabilisation
            
            # Prendre plusieurs échantillons pour moyenner
            print("⏳ Acquisition en cours...")
            samples = []
            for i in range(10):  # 10 acquisitions de 127 moyennes chacune
                sample_batch = self.mm.get_latest_samples(1)
                if sample_batch:
                    samples.extend(sample_batch)
                time.sleep(0.1)
            
            if samples:
                # Calculer les moyennes
                result = {
                    'frequency_hz': frequency_hz,
                    'timestamp': datetime.now(),
                    'n_samples': len(samples),
                    'Ex_mean': np.mean([s.adc1_ch1 for s in samples]),
                    'Ey_mean': np.mean([s.adc1_ch3 for s in samples]),
                    'Ez_mean': np.mean([s.adc2_ch1 for s in samples]),
                    'Ex_std': np.std([s.adc1_ch1 for s in samples]),
                    'Ey_std': np.std([s.adc1_ch3 for s in samples]),
                    'Ez_std': np.std([s.adc2_ch1 for s in samples])
                }
                
                print(f"✅ Acquisition terminée:")
                print(f"   Ex: {result['Ex_mean']:.1f} ± {result['Ex_std']:.1f}")
                print(f"   Ey: {result['Ey_mean']:.1f} ± {result['Ey_std']:.1f}")
                print(f"   Ez: {result['Ez_mean']:.1f} ± {result['Ez_std']:.1f}")
                
                return result
            else:
                print("❌ Aucun échantillon acquis")
                return None
                
        except Exception as e:
            print(f"❌ Erreur acquisition: {e}")
            return None
    
    def run_frequency_cycle(self, frequency_hz):
        """Effectue un cycle complet pour une fréquence donnée"""
        print(f"\n🔄 === CYCLE FRÉQUENCE {frequency_hz} Hz ===")
        
        # 1. Configurer la fréquence
        self.configure_frequency(frequency_hz)
        
        # 2. Aller à position X=0, Y=70cm
        if not self.move_to_position(0, 70):
            return None
        
        # 3. Auto-calibration sur X
        if not self.perform_auto_calibration_x():
            return None
        
        # 4. Aller à position X=70, Y=70cm
        if not self.move_to_position(70, 70):
            return None
        
        # 5. Acquisition moyennée à 127
        result = self.acquire_averaged_measurement(frequency_hz)
        
        if result:
            self.results.append(result)
            print(f"✅ Cycle {frequency_hz} Hz terminé avec succès\n")
        else:
            print(f"❌ Échec du cycle {frequency_hz} Hz\n")
        
        return result
    
    def run_acquisition_sequence(self, frequencies):
        """Lance la séquence d'acquisition complète"""
        print("🚀 === DÉMARRAGE ACQUISITION MULTI-FRÉQUENCE ===\n")
        
        self.frequencies = frequencies
        
        # 1. Initialisation des connexions
        if not self.initialize_connections():
            print("❌ Échec initialisation, arrêt du script")
            return False
        
        # 2. Configuration vitesse moteur
        if not self.configure_motor_speed(2000):
            print("❌ Échec configuration moteur, arrêt du script")
            return False
        
        # 3. Homing
        if not self.perform_homing():
            print("❌ Échec homing, arrêt du script")
            return False
        
        # 4. Cycles pour chaque fréquence
        print(f"📋 Début des cycles pour {len(frequencies)} fréquences")
        
        for freq in frequencies:
            try:
                self.run_frequency_cycle(freq)
            except Exception as e:
                print(f"❌ Erreur critique dans cycle {freq} Hz: {e}")
                continue
        
        # 5. Résumé final
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Affiche un résumé des résultats"""
        print("\n📊 === RÉSUMÉ DES ACQUISITIONS ===")
        print(f"Nombre de fréquences testées: {len(self.frequencies)}")
        print(f"Nombre de mesures réussies: {len(self.results)}")
        
        if self.results:
            print("\nRésultats (Ex moyen):")
            for result in self.results:
                print(f"  {result['frequency_hz']:6.0f} Hz: {result['Ex_mean']:8.1f} ± {result['Ex_std']:6.1f}")
        
        print("\n✅ Script terminé")
    
    def close(self):
        """Fermeture propre du système"""
        print("🔚 Fermeture du système...")
        self.mm.stop_acquisition()
        self.mm.close()

def main():
    """Fonction principale"""
    
    # Liste des fréquences à tester (en Hz)
    frequencies_to_test = [
        1000,   # 1 kHz
        2000,   # 2 kHz  
        5000,   # 5 kHz
        10000,  # 10 kHz
        20000,  # 20 kHz
        50000   # 50 kHz
    ]
    
    # Créer et lancer l'acquisition
    acquisition = FrequencyAcquisition()
    
    try:
        acquisition.run_acquisition_sequence(frequencies_to_test)
    except KeyboardInterrupt:
        print("\n⚠️ Interruption utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
    finally:
        acquisition.close()

if __name__ == "__main__":
    main()
