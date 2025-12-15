#!/usr/bin/env python3
"""
Script de Test pour l'Analyseur Spectral
========================================

Ce script génère des données d'exemple pour tester l'analyseur spectral
sans avoir besoin de données réelles du capteur LSM9D.

Usage:
    python test_spectral_analysis.py
"""

import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

# Utiliser la configuration centralisée
from config_paths import DATA_DIRECTORY, RESULTS_DIRECTORY

def generate_test_data(experiment_type='noise', duration=10, sampling_rate=20):
    """
    Génère des données de test pour simuler différents types d'expériences.
    
    :param experiment_type: Type d'expérience ('noise' ou 'movement')
    :param duration: Durée en secondes
    :param sampling_rate: Fréquence d'échantillonnage en Hz
    :return: DataFrame avec les données simulées
    """
    n_samples = int(duration * sampling_rate)
    time_rel = np.linspace(0, duration, n_samples)
    timestamps = time_rel + 1640000000  # Timestamp fictif
    
    # Bruit de base pour tous les axes
    base_noise_level = 0.001  # m/s²
    
    if experiment_type == 'noise':
        # Données statiques avec bruit blanc + quelques composantes fréquentielles
        
        # Bruit blanc
        noise_x = np.random.normal(0, base_noise_level, n_samples)
        noise_y = np.random.normal(0, base_noise_level, n_samples)
        noise_z = np.random.normal(0, base_noise_level, n_samples)
        
        # Ajouter quelques fréquences caractéristiques (vibrations environnement)
        freq_1 = 1.5  # Hz - vibrations basse fréquence
        freq_2 = 5.2  # Hz - vibrations moyennes
        
        acc_x = noise_x + 0.0005 * np.sin(2 * np.pi * freq_1 * time_rel)
        acc_y = noise_y + 0.0003 * np.sin(2 * np.pi * freq_2 * time_rel)
        acc_z = noise_z + 0.0002 * np.sin(2 * np.pi * freq_1 * time_rel) + 0.0001 * np.sin(2 * np.pi * freq_2 * time_rel)
        
    elif experiment_type == 'movement':
        # Données avec mouvement : bruit + signal de mouvement
        
        # Bruit de base plus élevé pendant le mouvement
        movement_noise_factor = 3.0
        noise_x = np.random.normal(0, base_noise_level * movement_noise_factor, n_samples)
        noise_y = np.random.normal(0, base_noise_level * movement_noise_factor, n_samples)
        noise_z = np.random.normal(0, base_noise_level * movement_noise_factor, n_samples)
        
        # Signal de mouvement (accélération/décélération)
        movement_freq = 0.8  # Hz - fréquence de mouvement
        movement_amplitude = 0.02  # m/s²
        
        # Profil d'accélération trapézoïdal
        acc_profile = np.zeros(n_samples)
        accel_phase = int(0.2 * n_samples)  # 20% accélération
        const_phase = int(0.6 * n_samples)  # 60% vitesse constante
        decel_phase = int(0.2 * n_samples)  # 20% décélération
        
        # Phase d'accélération
        acc_profile[:accel_phase] = movement_amplitude * np.linspace(0, 1, accel_phase)
        # Phase de vitesse constante (accélération nulle)
        acc_profile[accel_phase:accel_phase+const_phase] = 0
        # Phase de décélération
        acc_profile[accel_phase+const_phase:] = -movement_amplitude * np.linspace(0, 1, decel_phase)
        
        # Vibrations induites par le mouvement
        vib_freq_1 = 3.5  # Hz
        vib_freq_2 = 7.8  # Hz
        vibrations = (0.003 * np.sin(2 * np.pi * vib_freq_1 * time_rel) + 
                     0.001 * np.sin(2 * np.pi * vib_freq_2 * time_rel))
        
        acc_x = noise_x + acc_profile + vibrations
        acc_y = noise_y + 0.3 * acc_profile + 0.5 * vibrations
        acc_z = noise_z + 0.1 * acc_profile + 0.2 * vibrations
    
    else:
        raise ValueError(f"Type d'expérience non supporté: {experiment_type}")
    
    # Générer des données fictives pour les autres capteurs
    mag_x = np.random.normal(100, 5, n_samples)  # µT
    mag_y = np.random.normal(-50, 3, n_samples)
    mag_z = np.random.normal(200, 8, n_samples)
    
    gyr_x = np.random.normal(0, 0.5, n_samples)  # °/s
    gyr_y = np.random.normal(0, 0.3, n_samples)
    gyr_z = np.random.normal(0, 0.4, n_samples)
    
    lidar = np.random.normal(1500, 10, n_samples)  # mm
    
    # Créer le DataFrame
    data = {
        'timestamp': timestamps,
        'time_relative': time_rel,
        'acc_x': acc_x,
        'acc_y': acc_y,
        'acc_z': acc_z,
        'mag_x': mag_x,
        'mag_y': mag_y,
        'mag_z': mag_z,
        'gyr_x': gyr_x,
        'gyr_y': gyr_y,
        'gyr_z': gyr_z,
        'lidar': lidar
    }
    
    return pd.DataFrame(data)

def save_test_experiment(data, params, base_filename, output_dir=None):
    """
    Sauvegarde une expérience de test au format attendu par l'analyseur.
    
    :param data: DataFrame avec les données
    :param params: Paramètres de l'expérience
    :param base_filename: Nom de base des fichiers
    :param output_dir: Répertoire de sortie (utilise DATA_DIRECTORY par défaut)
    """
    output_path = Path(output_dir) if output_dir else DATA_DIRECTORY
    output_path.mkdir(exist_ok=True)
    
    # Sauvegarder le CSV
    csv_file = output_path / f"{base_filename}.csv"
    data.to_csv(csv_file, index=False)
    
    # Sauvegarder les paramètres JSON
    json_file = output_path / f"{base_filename}_params.json"
    with open(json_file, 'w') as f:
        json.dump(params, f, indent=2)
    
    print(f"✅ Expérience sauvegardée: {base_filename}")
    print(f"   📄 CSV: {csv_file}")
    print(f"   ⚙️  JSON: {json_file}")
    
    return str(csv_file)

def create_test_dataset():
    """
    Crée un jeu de données de test complet avec plusieurs expériences.
    """
    print("🧪 Génération du jeu de données de test...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Expérience 1: Mesure de bruit statique
    print("\n📊 Génération de l'expérience statique...")
    static_data = generate_test_data('noise', duration=30, sampling_rate=20)
    static_params = {
        'type': 'noise_measurement',
        'description': 'Mesure de bruit - système au repos (SIMULATION)',
        'duration': 30.0,
        'stage_movement': None,
        'stage_parameters': None,
        'timestamp_start': datetime.now().isoformat(),
        'lsm9d_mode': 'ALL_SENSORS',
        'target_sampling_rate': 20,
        'actual_sampling_rate': 20.0,
        'actual_data_points': len(static_data),
        'simulation': True
    }
    
    static_file = save_test_experiment(
        static_data, static_params, 
        f"noise_measurement_{timestamp}_001"
    )
    
    # Expérience 2: Mouvement lent
    print("\n🐌 Génération de l'expérience mouvement lent...")
    slow_data = generate_test_data('movement', duration=15, sampling_rate=20)
    slow_params = {
        'type': 'movement_analysis',
        'description': 'Mouvement lent pour analyse fréquentielle (SIMULATION)',
        'stage_movement': {
            'axis': 'x',
            'initial_position': 0,
            'target_position': 5000,
            'distance': 5000
        },
        'stage_parameters': {"ls": 10, "hs": 200, "acc": 100, "dec": 100},
        'timestamp_start': datetime.now().isoformat(),
        'lsm9d_mode': 'ALL_SENSORS',
        'target_sampling_rate': 20,
        'actual_sampling_rate': 20.0,
        'actual_data_points': len(slow_data),
        'estimated_duration': 15.0,
        'simulation': True
    }
    
    slow_file = save_test_experiment(
        slow_data, slow_params,
        f"movement_analysis_{timestamp}_002"
    )
    
    # Expérience 3: Mouvement rapide
    print("\n🏃 Génération de l'expérience mouvement rapide...")
    fast_data = generate_test_data('movement', duration=8, sampling_rate=20)
    fast_params = {
        'type': 'movement_analysis',
        'description': 'Mouvement rapide pour analyse fréquentielle (SIMULATION)',
        'stage_movement': {
            'axis': 'x',
            'initial_position': 0,
            'target_position': 5000,
            'distance': 5000
        },
        'stage_parameters': {"ls": 10, "hs": 1000, "acc": 500, "dec": 500},
        'timestamp_start': datetime.now().isoformat(),
        'lsm9d_mode': 'ALL_SENSORS',
        'target_sampling_rate': 20,
        'actual_sampling_rate': 20.0,
        'actual_data_points': len(fast_data),
        'estimated_duration': 8.0,
        'simulation': True
    }
    
    fast_file = save_test_experiment(
        fast_data, fast_params,
        f"movement_analysis_{timestamp}_003"
    )
    
    print(f"\n✅ Jeu de données de test créé avec succès!")
    print(f"📂 Répertoire: accelerometer_data/")
    print(f"📊 3 expériences générées:")
    print(f"   1. Statique (30s)")
    print(f"   2. Mouvement lent (15s)")
    print(f"   3. Mouvement rapide (8s)")
    
    return [static_file, slow_file, fast_file]

def run_analysis_demo():
    """
    Lance une démonstration complète de l'analyse spectrale.
    """
    print("🚀 Démonstration de l'analyse spectrale")
    print("=" * 50)
    
    # Créer les données de test
    test_files = create_test_dataset()
    
    # Importer et lancer l'analyseur
    try:
        # Import local dans le même répertoire
        from accelerometer_spectral_analysis import AccelerometerSpectralAnalyzer
        
        print("\n🔬 Lancement de l'analyse spectrale...")
        analyzer = AccelerometerSpectralAnalyzer('accelerometer_data')
        
        # Analyser un fichier spécifique pour démonstration
        print(f"\n🔍 Analyse du fichier statique: {test_files[0]}")
        results = analyzer.analyze_single_experiment(test_files[0])
        
        # Lancer l'analyse complète
        print(f"\n📈 Analyse complète de tous les fichiers...")
        analyzer.run_batch_analysis()
        
        print(f"\n🎉 Démonstration terminée!")
        print(f"📊 Consultez le répertoire '{RESULTS_DIRECTORY}' pour voir les résultats")
        
        # Vérifier les résultats
        preview_results()
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Assurez-vous que accelerometer_spectral_analysis.py est dans le même répertoire")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

def plot_test_signals():
    """
    Affiche un aperçu des signaux de test générés.
    """
    print("\n📊 Génération d'un aperçu des signaux de test...")
    
    # Générer des échantillons courts pour visualisation
    static_data = generate_test_data('noise', duration=5, sampling_rate=50)
    movement_data = generate_test_data('movement', duration=5, sampling_rate=50)
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('Aperçu des Signaux de Test Générés', fontsize=16)
    
    time_static = static_data['time_relative']
    time_movement = movement_data['time_relative']
    
    colors = ['red', 'green', 'blue']
    axes_names = ['X', 'Y', 'Z']
    
    for i, axis in enumerate(['x', 'y', 'z']):
        # Signal statique
        ax1 = axes[0, i]
        ax1.plot(time_static, static_data[f'acc_{axis}'], color=colors[i], linewidth=1)
        ax1.set_title(f'Statique - Axe {axes_names[i]}')
        ax1.set_xlabel('Temps (s)')
        ax1.set_ylabel('Accélération (m/s²)')
        ax1.grid(True, alpha=0.3)
        
        # Signal avec mouvement
        ax2 = axes[1, i]
        ax2.plot(time_movement, movement_data[f'acc_{axis}'], color=colors[i], linewidth=1)
        ax2.set_title(f'Mouvement - Axe {axes_names[i]}')
        ax2.set_xlabel('Temps (s)')
        ax2.set_ylabel('Accélération (m/s²)')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Sauvegarder l'aperçu
    preview_path = Path('analysis_results')
    preview_path.mkdir(exist_ok=True)
    preview_file = preview_path / 'test_signals_preview.png'
    plt.savefig(preview_file, dpi=150, bbox_inches='tight')
    
    print(f"📊 Aperçu sauvegardé: {preview_file}")
    plt.show()

def preview_results():
    """Affiche un aperçu des résultats générés."""
    print("\n📈 Aperçu des résultats générés:")
    
    preview_path = RESULTS_DIRECTORY
    if preview_path.exists():
        files = list(preview_path.glob('*'))
        if files:
            for file in sorted(files)[:5]:  # Afficher les 5 premiers fichiers
                print(f"   📄 {file.name}")
            if len(files) > 5:
                print(f"   ... et {len(files) - 5} autres fichiers")
        else:
            print("   ⚠️  Aucun fichier de résultat trouvé")
    else:
        print("   ⚠️  Répertoire de résultats non trouvé")

if __name__ == "__main__":
    print("🧪 SCRIPT DE TEST - ANALYSEUR SPECTRAL LSM9D")
    print("=" * 50)
    
    # Demander à l'utilisateur ce qu'il veut faire
    print("\nOptions disponibles:")
    print("1. Créer seulement les données de test")
    print("2. Afficher un aperçu des signaux")
    print("3. Démonstration complète (données + analyse)")
    
    choice = input("\nChoisissez une option (1-3): ").strip()
    
    try:
        if choice == '1':
            create_test_dataset()
        elif choice == '2':
            plot_test_signals()
        elif choice == '3':
            run_analysis_demo()
        else:
            print("❌ Choix invalide. Exécution de la démonstration complète...")
            run_analysis_demo()
            
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc() 