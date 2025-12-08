#!/usr/bin/env python3
"""
Script pour tracer les données de bande passante au format IEEE
Pour publication dans IEEE Sensors Journal
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# Chemin vers le fichier de données
# Chemin vers le fichier de données (chemin absolu pour éviter les problèmes)
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_dir, "data", "20250821_161806_bandePassante_freq10-1000000Hz_100pts.csv")

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
    # Vérifier si le fichier existe
    if not os.path.exists(data_file):
        print(f"Error: File {data_file} not found.")
        return
    
    # Charger les données
    print(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    
    # Extraire les colonnes
    freq = df['frequence_Hz']
    vpp = df['VPP_CH1']
    
    # Normaliser l'amplitude (par rapport à la valeur maximale)
    vpp_max = vpp.max()
    vpp_norm = vpp / vpp_max
    
    # Convertir en dB
    vpp_db = 20 * np.log10(vpp_norm)
    
    # Créer le dossier de sortie s'il n'existe pas
    output_dir = "figures"
    os.makedirs(output_dir, exist_ok=True)
    
    # Figure 1: Amplitude vs Frequency (linear scale)
    fig1, ax1 = plt.subplots()
    ax1.plot(freq, vpp, 'b-', marker='o', markersize=2)
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Amplitude (V$_{pp}$)")
    ax1.set_xscale('log')
    ax1.grid(True, linestyle='--', alpha=0.7)

    
    # Formatter pour les étiquettes d'axes
    formatter = ScalarFormatter()
    formatter.set_scientific(False)
    ax1.xaxis.set_major_formatter(formatter)
    
    # Ajuster les marges
    plt.tight_layout()
    
    # Sauvegarder la figure
    output_file1 = os.path.join(output_dir, "frequency_response_linear.eps")
    plt.savefig(output_file1, format="eps", dpi=600)
    print(f"Figure saved to {output_file1}")
    
    # Figure 2: Amplitude vs Frequency (dB scale)
    fig2, ax2 = plt.subplots()
    ax2.plot(freq, vpp_db, 'r-', marker='o', markersize=2)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Normalized Amplitude (dB)")
    ax2.set_xscale('log')
    ax2.grid(True, linestyle='--', alpha=0.7)

    
    # Formatter pour les étiquettes d'axes
    ax2.xaxis.set_major_formatter(formatter)
    
    # Définir les limites de l'axe Y pour montrer clairement la bande passante
    ax2.set_ylim([-40, 5])
    
    # Ajouter une ligne horizontale à -3 dB pour indiquer la bande passante
    ax2.axhline(y=-3, color='g', linestyle='--', alpha=0.7)
    ax2.text(freq.iloc[0]*2, -2.5, "-3 dB", color='g')
    
    # Ajuster les marges
    plt.tight_layout()
    
    # Sauvegarder la figure
    output_file2 = os.path.join(output_dir, "frequency_response_db.eps")
    plt.savefig(output_file2, format="eps", dpi=600)
    print(f"Figure saved to {output_file2}")
    
    # Figure 3: Amplitude vs Frequency (combined)
    fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(3.5, 5), sharex=True)
    
    # Sous-figure supérieure: échelle linéaire
    ax3a.plot(freq, vpp, 'b-', marker='o', markersize=2)
    ax3a.set_ylabel("Amplitude (V$_{pp}$)")
    ax3a.grid(True, linestyle='--', alpha=0.7)
    ax3a.set_title("Frequency Response")
    
    # Sous-figure inférieure: échelle dB
    ax3b.plot(freq, vpp_db, 'r-', marker='o', markersize=2)
    ax3b.set_xlabel("Frequency (Hz)")
    ax3b.set_ylabel("Normalized Amplitude (dB)")
    ax3b.set_xscale('log')
    ax3b.grid(True, linestyle='--', alpha=0.7)
    ax3b.set_ylim([-40, 5])
    ax3b.axhline(y=-3, color='g', linestyle='--', alpha=0.7)
    ax3b.text(freq.iloc[0]*2, -2.5, "-3 dB", color='g')
    
    # Formatter pour les étiquettes d'axes
    ax3b.xaxis.set_major_formatter(formatter)
    
    # Ajuster les marges
    plt.tight_layout()
    
    # Sauvegarder la figure
    output_file3 = os.path.join(output_dir, "frequency_response_combined.eps")
    plt.savefig(output_file3, format="eps", dpi=600)
    print(f"Figure saved to {output_file3}")
    
    # Calculer et afficher la fréquence de coupure à -3dB
    cutoff_freq = find_cutoff_frequency(freq, vpp_db)
    print(f"Cutoff frequency (-3 dB): {cutoff_freq:.2f} Hz")
    
    # Sauvegarder les figures en PDF également
    plt.figure(fig1.number)
    plt.savefig(os.path.join(output_dir, "frequency_response_linear.pdf"), format="pdf")
    
    plt.figure(fig2.number)
    plt.savefig(os.path.join(output_dir, "frequency_response_db.pdf"), format="pdf")
    
    plt.figure(fig3.number)
    plt.savefig(os.path.join(output_dir, "frequency_response_combined.pdf"), format="pdf")
    
    print("All figures saved in PDF format as well.")

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