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

# Chemin vers le fichier de données
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_dir, "data", "20251001_112946_bandePassante_freq100-1000000Hz_40pts.csv")

# Extraire le nom de base du fichier (sans extension) pour les noms de sortie
data_basename = os.path.splitext(os.path.basename(data_file))[0]

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
    # Vérifier si un argument de ligne de commande est fourni
    import sys
    if len(sys.argv) > 1:
        global data_file, data_basename
        data_file = sys.argv[1]
        # Mettre à jour le nom de base du fichier
        data_basename = os.path.splitext(os.path.basename(data_file))[0]
        print(f"Using data file from command line: {data_file}")
    
    # Vérifier si le fichier existe
    if not os.path.exists(data_file):
        print(f"Error: File {data_file} not found.")
        return
    
    # Charger les données
    print(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    
    # Extraire les colonnes
    freq = df['frequence_Hz']
    channels = [f'VPP_CH{i}' for i in range(1, 4)]
    colors = ['b', 'y', 'r']
    labels = ['CH1-VoieX', 'CH2-VoieY', 'CH3-VoieZ']
    
    # Créer le dossier de sortie au même endroit que le script
    output_dir = os.path.join(current_dir, "figures")
    os.makedirs(output_dir, exist_ok=True)
    
    # Formatter pour les étiquettes d'axes
    formatter = ScalarFormatter()
    formatter.set_scientific(False)
    
    # Figure 1: Amplitude vs Frequency (3 voies, échelle linéaire)
    fig1, ax1 = plt.subplots(figsize=(3.5, 2.5))
    for i, channel in enumerate(channels):
        ax1.plot(freq, df[channel], f'{colors[i]}-', marker='o', markersize=2, label=labels[i])
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Amplitude (V$_{pp}$)")
    ax1.set_xscale('log')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='best', frameon=False)
    ax1.xaxis.set_major_formatter(formatter)
    plt.tight_layout()
    output_file1 = os.path.join(output_dir, f"{data_basename}_linear.pdf")
    plt.savefig(output_file1, format="pdf", dpi=600)
    print(f"Figure saved to {output_file1}")
    
    # Figure 2: Amplitude vs Frequency (3 voies, dB scale)
    fig2, ax2 = plt.subplots(figsize=(3.5, 2.5))
    cutoff_freqs = []
    
    for i, channel in enumerate(channels):
        vpp = df[channel]
        vpp_max = vpp.max()
        vpp_norm = vpp / vpp_max
        vpp_db = 20 * np.log10(vpp_norm)
        
        ax2.plot(freq, vpp_db, f'{colors[i]}-', marker='o', markersize=2, label=labels[i])
        
        # Calculer la fréquence de coupure
        cutoff_freq = find_cutoff_frequency(freq, vpp_db)
        if cutoff_freq:
            cutoff_freqs.append((i+1, cutoff_freq))
    
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Normalized Amplitude (dB)")
    ax2.set_xscale('log')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.set_ylim([-40, 5])
    ax2.axhline(y=-3, color='k', linestyle='--', alpha=0.7)
    ax2.text(freq.iloc[0]*2, -2.5, "-3 dB", color='k')
    ax2.legend(loc='best', frameon=False)
    ax2.xaxis.set_major_formatter(formatter)
    plt.tight_layout()
    output_file2 = os.path.join(output_dir, f"{data_basename}_db.pdf")
    plt.savefig(output_file2, format="pdf", dpi=600)
    print(f"Figure saved to {output_file2}")
    
    # Figure 3: Subplots pour chaque voie (échelle dB)
    fig3, axs = plt.subplots(3, 1, figsize=(3.5, 7), sharex=True)
    
    for i, channel in enumerate(channels):
        vpp = df[channel]
        vpp_max = vpp.max()
        vpp_norm = vpp / vpp_max
        vpp_db = 20 * np.log10(vpp_norm)
        
        axs[i].plot(freq, vpp_db, f'{colors[i]}-', marker='o', markersize=2)
        axs[i].set_ylabel(f"{labels[i]} Amplitude (dB)")
        axs[i].grid(True, linestyle='--', alpha=0.7)
        axs[i].set_ylim([-40, 5])
        axs[i].axhline(y=-3, color='k', linestyle='--', alpha=0.7)
        
        if i == 0:
            axs[i].set_title("Frequency Response")
        if i == 2:
            axs[i].set_xlabel("Frequency (Hz)")
        
        axs[i].xaxis.set_major_formatter(formatter)
        axs[i].set_xscale('log')
    
    plt.tight_layout()
    output_file3 = os.path.join(output_dir, f"{data_basename}_subplots.pdf")
    plt.savefig(output_file3, format="pdf", dpi=600)
    print(f"Figure saved to {output_file3}")
    
    # Afficher les fréquences de coupure
    print("Cutoff frequencies (-3 dB):")
    for ch, freq in cutoff_freqs:
        print(f"  {labels[ch-1]}: {freq:.2f} Hz")

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