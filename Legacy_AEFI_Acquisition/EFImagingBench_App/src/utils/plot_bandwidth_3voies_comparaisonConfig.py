#!/usr/bin/env python3
"""
Script pour tracer les données de bande passante 3 voies au format IEEE
Pour publication dans IEEE Sensors Journal
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# Chemins vers les fichiers de données des deux configurations
current_dir = os.path.dirname(os.path.abspath(__file__))

# Fichiers pour les configurations X et Y (à modifier selon vos fichiers)
data_file_X = os.path.join(current_dir, "data", "20250926_151001_bandePassante_freq100-1000000Hz_40pts.csv")
data_file_Y = os.path.join(current_dir, "data", "20250926_141357_bandePassante_configX_freq100-1000000Hz_40pts.csv")

# Nom de base pour les fichiers de sortie
output_basename = "comparison_X_Y"

# Définir les paramètres pour les figures IEEE
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "font.size": 8,
    "figure.figsize": (3.5, 2.5),  # Largeur de colonne IEEE
    "figure.dpi": 600,
    "text.usetex": False,  # Changer à True si LaTeX est installé
    "axes.linewidth": 0.5,
    "lines.linewidth": 0.8,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.minor.width": 0.5,
    "ytick.minor.width": 0.5,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.minor.size": 1.5,
    "ytick.minor.size": 1.5,
    "xtick.direction": "in",
    "ytick.direction": "in"
})

def main():
    # Vérifier si les fichiers existent
    if not os.path.exists(data_file_X):
        print(f"Error: File {data_file_X} not found.")
        return
    
    if not os.path.exists(data_file_Y):
        print(f"Error: File {data_file_Y} not found.")
        return
    
    # Charger les données des deux configurations
    print(f"Loading data from {data_file_X} (Config X)...")
    df_X = pd.read_csv(data_file_X)
    
    print(f"Loading data from {data_file_Y} (Config Y)...")
    df_Y = pd.read_csv(data_file_Y)
    
    # Extraire les colonnes
    freq_X = df_X['frequence_Hz']
    freq_Y = df_Y['frequence_Hz']
    channels = [f'VPP_CH{i}' for i in range(1, 4)]
    colors_X = ['b', 'r', 'g']  # Couleurs pour config X
    colors_Y = ['c', 'm', 'y']  # Couleurs pour config Y (différentes pour distinguer)
    
    # Créer le dossier de sortie au même endroit que le script
    output_dir = os.path.join(current_dir, "figures")
    os.makedirs(output_dir, exist_ok=True)
    
    # Formatter pour les étiquettes d'axes
    formatter = ScalarFormatter()
    formatter.set_scientific(False)
    
    # Figure 1: Comparaison des configurations X et Y pour chaque canal (échelle linéaire)
    fig1, axes = plt.subplots(3, 1, figsize=(3.5, 7), sharex=True)
    
    for i, channel in enumerate(channels):
        # Tracer les données de la configuration X
        axes[i].plot(freq_X, df_X[channel], f'{colors_X[i]}-', marker='o', markersize=2, label=f'Config X')
        
        # Tracer les données de la configuration Y
        axes[i].plot(freq_Y, df_Y[channel], f'{colors_Y[i]}--', marker='s', markersize=2, label=f'Config Y')
        
        axes[i].set_ylabel(f"CH{i+1} (V$_{{pp}}$)")
        axes[i].grid(True, linestyle='--', alpha=0.7)
        axes[i].legend(loc='best', frameon=False)
        axes[i].xaxis.set_major_formatter(formatter)
        axes[i].set_xscale('log')
        
        if i == 0:
            axes[i].set_title("Frequency Response Comparison")
        if i == 2:
            axes[i].set_xlabel("Frequency (Hz)")
    
    plt.tight_layout()
    output_file1 = os.path.join(output_dir, f"{output_basename}_linear.pdf")
    plt.savefig(output_file1, format="pdf", dpi=600)
    print(f"Figure saved to {output_file1}")
    
    # Figure 2: Comparaison des configurations X et Y pour chaque canal (échelle dB)
    fig2, axes = plt.subplots(3, 1, figsize=(3.5, 7), sharex=True)
    cutoff_freqs_X = []
    cutoff_freqs_Y = []
    
    for i, channel in enumerate(channels):
        # Configuration X
        vpp_X = df_X[channel]
        vpp_max_X = vpp_X.max()
        vpp_norm_X = vpp_X / vpp_max_X
        vpp_db_X = 20 * np.log10(vpp_norm_X)
        
        # Configuration Y
        vpp_Y = df_Y[channel]
        vpp_max_Y = vpp_Y.max()
        vpp_norm_Y = vpp_Y / vpp_max_Y
        vpp_db_Y = 20 * np.log10(vpp_norm_Y)
        
        # Tracer les courbes
        axes[i].plot(freq_X, vpp_db_X, f'{colors_X[i]}-', marker='o', markersize=2, label=f'Config X')
        axes[i].plot(freq_Y, vpp_db_Y, f'{colors_Y[i]}--', marker='s', markersize=2, label=f'Config Y')
        
        # Calculer les fréquences de coupure
        cutoff_freq_X = find_cutoff_frequency(freq_X, vpp_db_X)
        if cutoff_freq_X:
            cutoff_freqs_X.append((i+1, cutoff_freq_X))
            
        cutoff_freq_Y = find_cutoff_frequency(freq_Y, vpp_db_Y)
        if cutoff_freq_Y:
            cutoff_freqs_Y.append((i+1, cutoff_freq_Y))
        
        # Configurer l'axe
        axes[i].set_ylabel(f"CH{i+1} (dB)")
        axes[i].grid(True, linestyle='--', alpha=0.7)
        axes[i].set_ylim([-40, 5])
        axes[i].axhline(y=-3, color='k', linestyle='--', alpha=0.7)
        axes[i].text(freq_X.iloc[0]*2, -2.5, "-3 dB", color='k')
        axes[i].legend(loc='best', frameon=False)
        axes[i].xaxis.set_major_formatter(formatter)
        axes[i].set_xscale('log')
        
        if i == 0:
            axes[i].set_title("Normalized Frequency Response Comparison")
        if i == 2:
            axes[i].set_xlabel("Frequency (Hz)")
    
    plt.tight_layout()
    output_file2 = os.path.join(output_dir, f"{output_basename}_db.pdf")
    plt.savefig(output_file2, format="pdf", dpi=600)
    print(f"Figure saved to {output_file2}")
    
    # Afficher les fréquences de coupure pour les deux configurations
    print("\nCutoff frequencies (-3 dB) for Config X:")
    for ch, freq in cutoff_freqs_X:
        print(f"  Channel {ch}: {freq:.2f} Hz")
    
    print("\nCutoff frequencies (-3 dB) for Config Y:")
    for ch, freq in cutoff_freqs_Y:
        print(f"  Channel {ch}: {freq:.2f} Hz")

def find_cutoff_frequency(freq, vpp_db):
    """
    Trouve la fréquence de coupure à -3dB par interpolation
    """
    # Trouver l'index où vpp_db devient inférieur à -3dB
    for i in range(len(vpp_db) - 1):
        if vpp_db.iloc[i] >= -3 and vpp_db.iloc[i+1] < -3:
            # Interpolation linéaire
            f1, f2 = freq.iloc[i], freq.iloc[i+1]
            db1, db2 = vpp_db.iloc[i], vpp_db.iloc[i+1]
            
            # Formule d'interpolation
            cutoff = f1 + (f2 - f1) * (-3 - db1) / (db2 - db1)
            return cutoff
    
    # Si aucun point de coupure n'est trouvé
    return None

if __name__ == "__main__":
    main() 