#!/usr/bin/env python3
"""
Script Simple d'Acquisition et d'Analyse Spectrale LSM9D
=======================================================

Script basique pour :
1. Acquérir des données du capteur LSM9D (MAGL)
2. Sauvegarder en CSV + JSON
3. Faire une analyse spectrale simple

"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
import json
import time
from datetime import datetime
from pathlib import Path

# Ajouter le chemin vers le backend LSM9D
sys.path.append('../LSM9D/instrument')
from LSM9D_SerialCommunication import LSM9D_Backend

def acquisition_simple(port='COM5', duration=10, mode='MAG_ACC_GYR'):
    """
    Acquisition simple des données du capteur LSM9D
    
    :param port: Port série du capteur
    :param duration: Durée d'acquisition en secondes
    :param mode: Mode de capteur ('MAG_ACC_GYR' par défaut)
    :return: Dictionnaire avec les données et paramètres
    """
    print(f"🎯 Acquisition {mode} sur {port} pendant {duration}s")
    
    # Initialiser le backend
    backend = LSM9D_Backend(port=port)
    
    # Se connecter
    if not backend.connect():
        raise Exception(f"Impossible de se connecter sur {port}")
    print(f"✅ Connecté sur {port}")
    
    # Initialiser le mode
    if not backend.initialize_sensor_mode(mode):
        backend.disconnect()
        raise Exception(f"Impossible d'initialiser le mode {mode}")
    print(f"✅ Mode {mode} initialisé")
    
    # Démarrer l'acquisition
    if not backend.start_streaming():
        backend.disconnect()
        raise Exception("Impossible de démarrer l'acquisition")
    print(f"✅ Acquisition démarrée")
    
    # Attendre la durée spécifiée
    print(f"⏱️  Acquisition en cours...")
    time.sleep(duration)
    
    # Arrêter et récupérer les données
    backend.stop_streaming()
    data = backend.get_historical_data()
    
    # Paramètres de l'expérience
    params = {
        'port': port,
        'mode': mode,
        'duration': duration,
        'timestamp': datetime.now().isoformat(),
        'data_points': len(data['timestamps']),
        'sampling_rate': len(data['timestamps']) / duration if duration > 0 else 0
    }
    
    print(f"✅ Acquisition terminée: {params['data_points']} points, {params['sampling_rate']:.1f} Hz")
    
    # Fermer la connexion
    backend.disconnect()
    
    return {
        'data': data,
        'params': params
    }

def sauvegarder_donnees(acquisition, base_filename=None):
    """
    Sauvegarde les données en CSV et les paramètres en JSON
    
    :param acquisition: Dictionnaire avec données et paramètres
    :param base_filename: Nom de base (généré automatiquement si None)
    :return: Chemins des fichiers créés
    """
    if base_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"acquisition_{timestamp}"
    
    # Créer le répertoire de données
    data_dir = Path("accelerometer_data")
    data_dir.mkdir(exist_ok=True)
    
    # Préparer les données pour le CSV
    data = acquisition['data']
    timestamps = data['timestamps']
    
    # Créer le DataFrame
    df_data = {
        'timestamp': timestamps,
        'time_relative': [t - timestamps[0] for t in timestamps] if timestamps else []
    }
    
    # Ajouter les données selon le mode
    if data['magnetometer']:
        for i, mag_data in enumerate(data['magnetometer']):
            if i < len(timestamps):
                for axis in ['x', 'y', 'z']:
                    col_name = f'mag_{axis}'
                    if col_name not in df_data:
                        df_data[col_name] = []
                    df_data[col_name].append(mag_data.get(axis, 0))
    
    if data['accelerometer']:
        for i, acc_data in enumerate(data['accelerometer']):
            if i < len(timestamps):
                for axis in ['x', 'y', 'z']:
                    col_name = f'acc_{axis}'
                    if col_name not in df_data:
                        df_data[col_name] = []
                    df_data[col_name].append(acc_data.get(axis, 0))
    
    if data['gyroscope']:
        for i, gyr_data in enumerate(data['gyroscope']):
            if i < len(timestamps):
                for axis in ['x', 'y', 'z']:
                    col_name = f'gyr_{axis}'
                    if col_name not in df_data:
                        df_data[col_name] = []
                    df_data[col_name].append(gyr_data.get(axis, 0))
    
    # Égaliser les longueurs des colonnes
    max_len = max(len(v) for v in df_data.values() if isinstance(v, list))
    for key in df_data:
        if isinstance(df_data[key], list) and len(df_data[key]) < max_len:
            df_data[key].extend([0] * (max_len - len(df_data[key])))
    
    df = pd.DataFrame(df_data)
    
    # Sauvegarder CSV
    csv_path = data_dir / f"{base_filename}.csv"
    df.to_csv(csv_path, index=False)
    
    # Sauvegarder JSON
    json_path = data_dir / f"{base_filename}_params.json"
    with open(json_path, 'w') as f:
        json.dump(acquisition['params'], f, indent=2)
    
    print(f"💾 Données sauvegardées:")
    print(f"   📄 {csv_path}")
    print(f"   📄 {json_path}")
    
    return {
        'csv': csv_path,
        'json': json_path,
        'dataframe': df
    }

def analyse_spectrale_simple(df, sampling_rate, signal_cols=['acc_x', 'acc_y', 'acc_z']):
    """
    Analyse spectrale simple des signaux
    
    :param df: DataFrame avec les données
    :param sampling_rate: Fréquence d'échantillonnage
    :param signal_cols: Colonnes à analyser
    :return: Résultats de l'analyse
    """
    print(f"🔍 Analyse spectrale des signaux: {signal_cols}")
    
    results = {}
    
    # Créer le répertoire de résultats
    results_dir = Path("analysis_results")
    results_dir.mkdir(exist_ok=True)
    
    # Analyser chaque signal
    for col in signal_cols:
        if col not in df.columns:
            print(f"⚠️  Colonne {col} non trouvée")
            continue
            
        signal = df[col].values
        
        # Calculer la FFT
        N = len(signal)
        fft_values = fft(signal)
        freqs = fftfreq(N, 1/sampling_rate)
        
        # Prendre seulement les fréquences positives
        positive_freqs = freqs[:N//2]
        magnitude = np.abs(fft_values[:N//2])
        
        # Normaliser
        magnitude = magnitude / N
        
        # Trouver la fréquence dominante (exclure DC)
        if len(magnitude) > 1:
            dominant_idx = np.argmax(magnitude[1:]) + 1
            dominant_freq = positive_freqs[dominant_idx]
            dominant_power = magnitude[dominant_idx]
        else:
            dominant_freq = 0
            dominant_power = 0
        
        # Statistiques du signal
        stats = {
            'mean': np.mean(signal),
            'std': np.std(signal),
            'rms': np.sqrt(np.mean(signal**2)),
            'peak_to_peak': np.max(signal) - np.min(signal),
            'dominant_frequency': dominant_freq,
            'dominant_power': dominant_power
        }
        
        results[col] = {
            'frequencies': positive_freqs,
            'magnitude': magnitude,
            'stats': stats
        }
        
        print(f"   {col}: f_dom={dominant_freq:.2f}Hz, RMS={stats['rms']:.4f}")
    
    return results

def plot_resultats(df, results, sampling_rate, save_path=None):
    """
    Crée des graphiques des résultats
    
    :param df: DataFrame avec les données
    :param results: Résultats de l'analyse spectrale
    :param sampling_rate: Fréquence d'échantillonnage
    :param save_path: Chemin de sauvegarde (optionnel)
    """
    print("📊 Génération des graphiques...")
    
    n_signals = len(results)
    if n_signals == 0:
        return
    
    fig, axes = plt.subplots(2, n_signals, figsize=(4*n_signals, 8))
    if n_signals == 1:
        axes = axes.reshape(2, 1)
    
    for i, (col, result) in enumerate(results.items()):
        # Signal temporel
        ax_time = axes[0, i]
        time_data = df['time_relative'] if 'time_relative' in df.columns else range(len(df))
        ax_time.plot(time_data, df[col])
        ax_time.set_title(f'{col} - Signal temporel')
        ax_time.set_xlabel('Temps (s)')
        ax_time.set_ylabel('Amplitude')
        ax_time.grid(True)
        
        # Spectre fréquentiel
        ax_freq = axes[1, i]
        freqs = result['frequencies']
        magnitude = result['magnitude']
        ax_freq.plot(freqs, magnitude)
        ax_freq.set_title(f'{col} - Spectre FFT')
        ax_freq.set_xlabel('Fréquence (Hz)')
        ax_freq.set_ylabel('Magnitude')
        ax_freq.grid(True)
        
        # Limiter l'affichage aux fréquences utiles
        max_freq = min(sampling_rate/2, 20)  # Limiter à 20 Hz max
        ax_freq.set_xlim(0, max_freq)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📈 Graphique sauvegardé: {save_path}")
    
    plt.show()

def main():
    """Fonction principale"""
    print("🚀 SCRIPT SIMPLE - ACQUISITION ET ANALYSE LSM9D")
    print("=" * 50)
    
    try:
        # 1. Acquisition des données
        print("\n1️⃣ ACQUISITION")
        acquisition = acquisition_simple(
            port='COM5',
            duration=5,  # 5 secondes pour commencer
            mode='MAG_ACC_GYR'
        )
        
        # 2. Sauvegarde
        print("\n2️⃣ SAUVEGARDE")
        fichiers = sauvegarder_donnees(acquisition)
        
        # 3. Analyse spectrale
        print("\n3️⃣ ANALYSE SPECTRALE")
        df = fichiers['dataframe']
        sampling_rate = acquisition['params']['sampling_rate']
        
        # Analyser les accéléromètres (MAGL = Magnétomètre + Accéléromètre + Gyroscope)
        cols_to_analyze = []
        for prefix in ['acc', 'mag', 'gyr']:
            for axis in ['x', 'y', 'z']:
                col_name = f'{prefix}_{axis}'
                if col_name in df.columns:
                    cols_to_analyze.append(col_name)
        
        if cols_to_analyze:
            results = analyse_spectrale_simple(df, sampling_rate, cols_to_analyze)
            
            # 4. Graphiques
            print("\n4️⃣ GRAPHIQUES")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_path = Path("analysis_results") / f"analyse_{timestamp}.png"
            plot_resultats(df, results, sampling_rate, plot_path)
        else:
            print("⚠️  Aucune colonne de données trouvée pour l'analyse")
        
        print("\n🎉 TERMINÉ!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 