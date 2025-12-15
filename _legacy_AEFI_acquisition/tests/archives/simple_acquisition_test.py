#!/usr/bin/env python3
"""
Script simple pour tester l'acquisition de données de l'accéléromètre LSM9D
===========================================================================

Ce script basique permet de :
- Se connecter au capteur LSM9D
- Acquérir des données de l'accéléromètre en mode ALL_SENSORS  
- Sauvegarder les données dans un fichier CSV avec les paramètres en JSON

Usage : python simple_acquisition_test.py
"""

import sys
import json
import csv
import time
import datetime
from pathlib import Path

# Ajouter le chemin vers le module LSM9D
sys.path.append('LSM9D')

from LSM9D_Backend import LSM9D_Backend

def simple_acquisition_test(duration=10.0, port='COM5'):
    """
    Test simple d'acquisition de données de l'accéléromètre.
    
    :param duration: Durée de l'acquisition en secondes
    :param port: Port série du capteur LSM9D
    """
    print("=" * 60)
    print("🔬 TEST SIMPLE D'ACQUISITION LSM9D")
    print("=" * 60)
    
    # Créer le répertoire de données
    data_dir = Path('accelerometer_data')
    data_dir.mkdir(exist_ok=True)
    
    # Initialiser le backend LSM9D
    print(f"📡 Connexion au capteur LSM9D sur {port}...")
    lsm9d = LSM9D_Backend(port=port, max_data_points=2000)
    
    try:
        # Connexion
        if not lsm9d.connect():
            print("❌ Échec de connexion au capteur")
            return False
        
        print("✅ Capteur connecté")
        
        # Configuration en mode ALL_SENSORS
        if not lsm9d.initialize_sensor_mode('ALL_SENSORS'):
            print("❌ Échec d'initialisation du mode ALL_SENSORS")
            return False
        
        print("✅ Mode ALL_SENSORS initialisé")
        
        # Afficher l'état
        status = lsm9d.get_status()
        print(f"📊 État: {status}")
        
        # Préparer les paramètres de l'expérience
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"simple_test_{timestamp}"
        
        experiment_params = {
            'type': 'simple_acquisition_test',
            'description': 'Test basique d\'acquisition de l\'accéléromètre',
            'duration': duration,
            'port': port,
            'mode': 'ALL_SENSORS',
            'timestamp_start': datetime.datetime.now().isoformat(),
            'target_sampling_rate': 20
        }
        
        # Effacer les données précédentes et démarrer l'acquisition
        lsm9d.clear_data()
        
        if not lsm9d.start_streaming():
            print("❌ Impossible de démarrer le streaming")
            return False
        
        print(f"📊 Acquisition démarrée pour {duration}s...")
        
        # Attendre et afficher le progrès
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            
            # Affichage du progrès toutes les 2 secondes
            if elapsed % 2 < 0.1:
                current_data = lsm9d.get_current_data()
                acc = current_data['accelerometer']
                print(f"   ⏱️  {remaining:.1f}s - Acc[X={acc['x']:.2f}, Y={acc['y']:.2f}, Z={acc['z']:.2f}]")
            
            time.sleep(0.1)
        
        # Arrêter l'acquisition
        lsm9d.stop_streaming()
        
        # Récupérer les données
        all_data = lsm9d.get_historical_data()
        timestamps = all_data['timestamps']
        accelerometer_data = all_data['accelerometer']
        magnetometer_data = all_data['magnetometer']
        gyroscope_data = all_data['gyroscope']
        lidar_data = all_data['lidar']
        
        print(f"📊 Acquisition terminée - {len(timestamps)} points collectés")
        
        # Calculer les statistiques
        if timestamps:
            actual_duration = timestamps[-1] - timestamps[0]
            actual_sampling_rate = len(timestamps) / actual_duration if actual_duration > 0 else 0
            experiment_params['actual_duration'] = actual_duration
            experiment_params['actual_sampling_rate'] = actual_sampling_rate
            experiment_params['actual_data_points'] = len(timestamps)
            
            print(f"📈 Durée réelle: {actual_duration:.2f}s")
            print(f"📈 Fréquence réelle: {actual_sampling_rate:.1f} Hz")
        
        experiment_params['timestamp_end'] = datetime.datetime.now().isoformat()
        
        # Sauvegarder les données CSV
        csv_filename = data_dir / f"{base_filename}.csv"
        print(f"💾 Sauvegarde CSV: {csv_filename}")
        
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
            
            start_time_ref = timestamps[0] if timestamps else 0
            
            for i in range(len(timestamps)):
                acc = accelerometer_data[i] if i < len(accelerometer_data) else {'x': 0, 'y': 0, 'z': 0}
                mag = magnetometer_data[i] if i < len(magnetometer_data) else {'x': 0, 'y': 0, 'z': 0}
                gyr = gyroscope_data[i] if i < len(gyroscope_data) else {'x': 0, 'y': 0, 'z': 0}
                lidar = lidar_data[i] if i < len(lidar_data) else 0
                
                writer.writerow({
                    'timestamp': timestamps[i],
                    'time_relative': timestamps[i] - start_time_ref,
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
                })
        
        # Sauvegarder les paramètres JSON
        json_filename = data_dir / f"{base_filename}_params.json"
        print(f"💾 Sauvegarde JSON: {json_filename}")
        
        with open(json_filename, 'w') as jsonfile:
            json.dump(experiment_params, jsonfile, indent=2, ensure_ascii=False)
        
        # Afficher quelques statistiques des données de l'accéléromètre
        if accelerometer_data:
            acc_x_values = [d['x'] for d in accelerometer_data]
            acc_y_values = [d['y'] for d in accelerometer_data]
            acc_z_values = [d['z'] for d in accelerometer_data]
            
            print(f"\n📊 Statistiques de l'accéléromètre:")
            print(f"   Acc X - Min: {min(acc_x_values):.3f}, Max: {max(acc_x_values):.3f}, Moy: {sum(acc_x_values)/len(acc_x_values):.3f}")
            print(f"   Acc Y - Min: {min(acc_y_values):.3f}, Max: {max(acc_y_values):.3f}, Moy: {sum(acc_y_values)/len(acc_y_values):.3f}")
            print(f"   Acc Z - Min: {min(acc_z_values):.3f}, Max: {max(acc_z_values):.3f}, Moy: {sum(acc_z_values)/len(acc_z_values):.3f}")
        
        print("✅ Test terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
        
    finally:
        # Nettoyer
        lsm9d.stop_streaming()
        lsm9d.disconnect()
        print("🧹 Capteur déconnecté")

def main():
    """Fonction principale."""
    print("Test simple d'acquisition de l'accéléromètre LSM9D")
    print("Appuyez sur Ctrl+C pour arrêter à tout moment")
    
    try:
        # Demander les paramètres
        duration = input("Durée d'acquisition (défaut: 10s): ").strip()
        if not duration:
            duration = 10.0
        else:
            duration = float(duration)
        
        port = input("Port série (défaut: COM5): ").strip()
        if not port:
            port = 'COM5'
        
        # Lancer le test
        success = simple_acquisition_test(duration=duration, port=port)
        
        if success:
            print("\n🎉 Le test s'est déroulé correctement!")
            print("   Les fichiers de données sont dans le dossier 'accelerometer_data'")
        else:
            print("\n❌ Le test a échoué")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrompu par l'utilisateur")
    except ValueError as e:
        print(f"❌ Erreur de saisie: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main() 