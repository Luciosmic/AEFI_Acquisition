#!/usr/bin/env python3
"""
Calibration ultra-simple des angles de rotation
Recherche itérative minimisant les composantes parasites
"""

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from EFImagingBench_metaManager import MetaManager

class SimpleAngleCalibration:
    def __init__(self):
        self.mm = MetaManager()
        self.offset = None
        
    def init_system(self):
        print("🔧 Initialisation...")
        self.mm.set_mode("exploration")
        config = {'freq_hz': 1000, 'gain_dds': 500, 'n_avg': 50}
        self.mm.update_configuration(config)
        self.mm.start_acquisition('exploration', {})
        time.sleep(1)  # Temps pour stabilisation
        
    def set_excitation_x(self):
        """Configure l'excitation selon l'axe X (DDS1 et DDS2 en phase)"""
        config = {
            'gain_dds1': 5000,
            'gain_dds2': 5000,
            'gain_dds': 5000,
            'phase_dds1': 0,
            'phase_dds2': 0
        }
        self.mm.update_configuration(config)
        print("✅ Excitation X configurée")
        
    def set_excitation_y(self):
        """Configure l'excitation selon l'axe Y (DDS1 et DDS2 en opposition)"""
        config = {
            'gain_dds1': 5000,
            'gain_dds2': 5000,
            'gain_dds': 5000,
            'phase_dds1': 0,
            'phase_dds2': 32768  # 180° = 32768
        }
        self.mm.update_configuration(config)
        print("✅ Excitation Y configurée")
        
    def set_excitation_off(self):
        """Désactive l'excitation"""
        config = {
            'gain_dds1': 0,
            'gain_dds2': 0,
            'gain_dds': 0
        }
        self.mm.update_configuration(config)
        print("✅ Excitation désactivée")
        
    def collect_offset(self):
        print("📊 Collecte offset (3s)...")
        self.set_excitation_off()
        time.sleep(0.5)  # Temps pour stabilisation
        samples = self.mm.get_latest_samples(100)
        
        if samples:
            self.offset = {
                'Ex': np.mean([s.adc1_ch1 for s in samples]),
                'Ey': np.mean([s.adc1_ch3 for s in samples]), 
                'Ez': np.mean([s.adc2_ch1 for s in samples])
            }
            print(f"✅ Offset: Ex={self.offset['Ex']:.0f}, Ey={self.offset['Ey']:.0f}, Ez={self.offset['Ez']:.0f}")
        
    def measure_field(self):
        print("📡 Mesure champ (3s)...")
        time.sleep(0.5)  # Temps pour stabilisation
        samples = self.mm.get_latest_samples(100)
        
        if samples and self.offset:
            field = {
                'Ex': np.mean([s.adc1_ch1 for s in samples]) - self.offset['Ex'],
                'Ey': np.mean([s.adc1_ch3 for s in samples]) - self.offset['Ey'],
                'Ez': np.mean([s.adc2_ch1 for s in samples]) - self.offset['Ez']
            }
            print(f"📊 Champ: Ex={field['Ex']:.0f}, Ey={field['Ey']:.0f}, Ez={field['Ez']:.0f}")
            return field
        return None
        
    def calculate_parasitic_error(self, angles, field_x, field_y):
        """Calcule erreur = somme des composantes parasites après rotation"""
        theta_x, theta_y, theta_z = np.radians(angles)
        
        # Matrices de rotation
        Rx = np.array([[1, 0, 0], [0, np.cos(theta_x), -np.sin(theta_x)], [0, np.sin(theta_x), np.cos(theta_x)]])
        Ry = np.array([[np.cos(theta_y), 0, np.sin(theta_y)], [0, 1, 0], [-np.sin(theta_y), 0, np.cos(theta_y)]])
        Rz = np.array([[np.cos(theta_z), -np.sin(theta_z), 0], [np.sin(theta_z), np.cos(theta_z), 0], [0, 0, 1]])
        
        R = Rz @ Ry @ Rx
        R_inv = R.T
        
        # Rotation vers référentiel banc
        E_bench_x = R_inv @ np.array([field_x['Ex'], field_x['Ey'], field_x['Ez']])
        E_bench_y = R_inv @ np.array([field_y['Ex'], field_y['Ey'], field_y['Ez']])
        
        # Config X doit donner [E0, 0, 0] → erreur = |Ey| + |Ez|
        # Config Y doit donner [0, E0, 0] → erreur = |Ex| + |Ez|
        error_x = abs(E_bench_x[1]) + abs(E_bench_x[2])  # |Ey| + |Ez|
        error_y = abs(E_bench_y[0]) + abs(E_bench_y[2])  # |Ex| + |Ez|
        
        return error_x + error_y
        
    def optimize_angles(self, field_x, field_y):
        print("🎯 Optimisation...")
        
        # Point de départ : angles parfaits
        best_angles = [-33.5, 33.7, 0]  # [theta_x, theta_y, theta_z]
        best_error = self.calculate_parasitic_error(best_angles, field_x, field_y)
        step = 0.2  # Pas en degrés
        
        print(f"Erreur initiale: {best_error:.2f}")
        
        for iteration in range(1000):
            improved = False
            
            # Test chaque angle
            for i in range(3):
                for delta in [-step, step]:
                    test_angles = best_angles.copy()
                    test_angles[i] += delta
                    
                    error = self.calculate_parasitic_error(test_angles, field_x, field_y)
                    
                    if error < best_error:
                        best_error = error
                        best_angles = test_angles
                        improved = True
                        angle_names = ['θx', 'θy', 'θz']
                        print(f"  Iter {iteration+1}: {angle_names[i]}={test_angles[i]:.1f}° → Erreur={error:.2f}")
            
            if not improved:
                step *= 0.8
                if step < 0.1:
                    break
                    
        print(f"✅ Angles finaux: θx={best_angles[0]:.2f}°, θy={best_angles[1]:.2f}°, θz={best_angles[2]:.2f}°")
        print(f"   Erreur finale: {best_error:.4f}")
        
        return best_angles
        
    def apply_angles(self, angles):
        print("⚙️ Application au système...")
        self.mm.set_rotation_angles(angles[0], angles[1], angles[2])
        self.mm.toggle_frame_rotation(True)
        self.mm.set_display_frame('bench')
        print("✅ Angles appliqués")
        
    def run(self):
        print("🎯 CALIBRATION ANGLES - VERSION ROBUSTE\n")
        
        try:
            self.init_system()
            self.collect_offset()
            
            if not self.offset:
                print("❌ Impossible de collecter l'offset")
                return
            
            # Configuration X
            print("\n=== CONFIGURATION ARMATURES X ===")
            input("Configurez armatures selon X, puis Entrée...")
            self.set_excitation_x()
            field_x = self.measure_field()
            if not field_x:
                print("❌ Échec mesure X")
                return
                
            # Configuration Y  
            print("\n=== CONFIGURATION ARMATURES Y ===")
            input("Configurez armatures selon Y, puis Entrée...")
            self.set_excitation_y()
            field_y = self.measure_field()
            if not field_y:
                print("❌ Échec mesure Y") 
                return
                
            print("\n✅ Mesures terminées")
            print(f"Champ X: Ex={field_x['Ex']:.0f}, Ey={field_x['Ey']:.0f}, Ez={field_x['Ez']:.0f}")
            print(f"Champ Y: Ex={field_y['Ex']:.0f}, Ey={field_y['Ey']:.0f}, Ez={field_y['Ez']:.0f}")
            
        except KeyboardInterrupt:
            print("\n⚠️ Calibration interrompue")
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
        finally:
            try:
                self.set_excitation_off()
                self.mm.stop_acquisition()
                self.mm.close()
                print("✅ Nettoyage terminé")
            except Exception as e:
                print(f"⚠️ Erreur nettoyage: {e}")

if __name__ == "__main__":
    SimpleAngleCalibration().run()