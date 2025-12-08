#!/usr/bin/env python3
"""
Script d'analyse des résultats de calibration DDS
Lit les données CSV, génère des graphiques et identifie les problèmes
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime

# Configuration matplotlib pour un affichage propre
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# Paramètres par défaut
DEFAULT_CSV_PATH = "getE3D/calibration/mesures/balayage_20250626_195221_freq100-1000000Hz_1000pts.csv"
DEFAULT_OUTPUT_DIR = "getE3D/calibration/analyse"

# Seuils d'alerte
PHASE_THRESHOLD = 5.0  # degrés
TRANSFER_THRESHOLD_MIN = 0.9
TRANSFER_THRESHOLD_MAX = 1.1

def load_data(csv_path):
    """Charge et nettoie les données CSV"""
    print(f"Chargement des données depuis : {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"✗ Fichier introuvable : {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ {len(df)} mesures chargées")
        
        # Nettoyage des données
        df = df.dropna(subset=['frequence_Hz'])  # Supprimer les lignes sans fréquence
        df = df.sort_values('frequence_Hz')  # Trier par fréquence
        
        # Conversion en types appropriés
        df['frequence_Hz'] = pd.to_numeric(df['frequence_Hz'], errors='coerce')
        df['phase_deg'] = pd.to_numeric(df['phase_deg'], errors='coerce')
        df['transfer_function'] = pd.to_numeric(df['transfer_function'], errors='coerce')
        df['VPP_CH3'] = pd.to_numeric(df['VPP_CH3'], errors='coerce')
        df['VPP_CH4'] = pd.to_numeric(df['VPP_CH4'], errors='coerce')
        
        # Supprimer les lignes avec des valeurs aberrantes
        initial_count = len(df)
        df = df[df['frequence_Hz'] > 0]  # Fréquences positives
        df = df[df['transfer_function'] > 0]  # Fonction de transfert positive
        final_count = len(df)
        
        if initial_count != final_count:
            print(f"⚠️ {initial_count - final_count} lignes supprimées (valeurs aberrantes)")
        
        print(f"✓ {len(df)} mesures valides après nettoyage")
        return df
        
    except Exception as e:
        print(f"✗ Erreur lors du chargement : {e}")
        return None

def create_plots(df, output_dir):
    """Crée les graphiques d'analyse"""
    print(f"Génération des graphiques dans : {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Génération du nom de fichier avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    freq_min = df['frequence_Hz'].min()
    freq_max = df['frequence_Hz'].max()
    n_points = len(df)
    
    plot_filename = f"analyse_{timestamp}_freq{freq_min:.0f}-{freq_max:.0f}Hz_{n_points}pts.png"
    plot_path = os.path.join(output_dir, plot_filename)
    
    # Figure avec 4 sous-graphiques
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Analyse des résultats de calibration DDS', fontsize=16, fontweight='bold')
    
    # 1. Déphasage en fonction de la fréquence
    ax1 = axes[0, 0]
    ax1.semilogx(df['frequence_Hz'], df['phase_deg'], 'b-o', markersize=4, linewidth=1)
    ax1.axhline(y=PHASE_THRESHOLD, color='r', linestyle='--', alpha=0.7, label=f'Seuil ±{PHASE_THRESHOLD}°')
    ax1.axhline(y=-PHASE_THRESHOLD, color='r', linestyle='--', alpha=0.7)
    ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Fréquence (Hz)')
    ax1.set_ylabel('Déphasage (°)')
    ax1.set_title('Déphasage CH4 par rapport à CH3')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Fonction de transfert en fonction de la fréquence
    ax2 = axes[0, 1]
    ax2.semilogx(df['frequence_Hz'], df['transfer_function'], 'g-o', markersize=4, linewidth=1)
    ax2.axhline(y=TRANSFER_THRESHOLD_MIN, color='r', linestyle='--', alpha=0.7, 
                label=f'Seuils [{TRANSFER_THRESHOLD_MIN}, {TRANSFER_THRESHOLD_MAX}]')
    ax2.axhline(y=TRANSFER_THRESHOLD_MAX, color='r', linestyle='--', alpha=0.7)
    ax2.axhline(y=1.0, color='k', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Fréquence (Hz)')
    ax2.set_ylabel('Fonction de transfert (VPP_CH4/VPP_CH3)')
    ax2.set_title('Fonction de transfert')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Amplitudes en fonction de la fréquence
    ax3 = axes[1, 0]
    ax3.semilogx(df['frequence_Hz'], df['VPP_CH3'], 'b-o', markersize=4, linewidth=1, label='CH3 (DDS1)')
    ax3.semilogx(df['frequence_Hz'], df['VPP_CH4'], 'r-o', markersize=4, linewidth=1, label='CH4 (DDS2)')
    ax3.set_xlabel('Fréquence (Hz)')
    ax3.set_ylabel('Amplitude VPP (V)')
    ax3.set_title('Amplitudes des signaux')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Histogramme des déphasages
    ax4 = axes[1, 1]
    ax4.hist(df['phase_deg'].dropna(), bins=20, alpha=0.7, color='blue', edgecolor='black')
    ax4.axvline(x=PHASE_THRESHOLD, color='r', linestyle='--', alpha=0.7, label=f'Seuil ±{PHASE_THRESHOLD}°')
    ax4.axvline(x=-PHASE_THRESHOLD, color='r', linestyle='--', alpha=0.7)
    ax4.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    ax4.set_xlabel('Déphasage (°)')
    ax4.set_ylabel('Nombre de mesures')
    ax4.set_title('Distribution des déphasages')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Sauvegarde
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"✓ Graphique sauvegardé : {plot_path}")
    
    # Affichage
    plt.show()
    
    return plot_path

def identify_problems(df):
    """Identifie les fréquences problématiques"""
    print("\n=== Identification des problèmes ===")
    
    problems = {
        'phase_problems': [],
        'transfer_problems': [],
        'summary': {}
    }
    
    # Problèmes de déphasage
    phase_mask = (df['phase_deg'].abs() > PHASE_THRESHOLD) & (df['phase_deg'].notna())
    if phase_mask.any():
        phase_problems = df[phase_mask][['frequence_Hz', 'phase_deg']].copy()
        problems['phase_problems'] = phase_problems
        print(f"⚠️ {len(phase_problems)} problèmes de déphasage détectés")
        for _, row in phase_problems.iterrows():
            print(f"  - {row['frequence_Hz']:.1f} Hz : {row['phase_deg']:.2f}°")
    else:
        print("✓ Aucun problème de déphasage détecté")
    
    # Problèmes de fonction de transfert
    transfer_mask = ((df['transfer_function'] < TRANSFER_THRESHOLD_MIN) | 
                    (df['transfer_function'] > TRANSFER_THRESHOLD_MAX)) & (df['transfer_function'].notna())
    if transfer_mask.any():
        transfer_problems = df[transfer_mask][['frequence_Hz', 'transfer_function']].copy()
        problems['transfer_problems'] = transfer_problems
        print(f"⚠️ {len(transfer_problems)} problèmes de fonction de transfert détectés")
        for _, row in transfer_problems.iterrows():
            print(f"  - {row['frequence_Hz']:.1f} Hz : {row['transfer_function']:.4f}")
    else:
        print("✓ Aucun problème de fonction de transfert détecté")
    
    # Statistiques
    problems['summary'] = {
        'total_measurements': len(df),
        'phase_problems_count': len(problems['phase_problems']),
        'transfer_problems_count': len(problems['transfer_problems']),
        'phase_mean': df['phase_deg'].mean(),
        'phase_std': df['phase_deg'].std(),
        'phase_min': df['phase_deg'].min(),
        'phase_max': df['phase_deg'].max(),
        'transfer_mean': df['transfer_function'].mean(),
        'transfer_std': df['transfer_function'].std(),
        'transfer_min': df['transfer_function'].min(),
        'transfer_max': df['transfer_function'].max()
    }
    
    print(f"\n📊 Statistiques :")
    print(f"  Déphasage : {problems['summary']['phase_mean']:.2f}° ± {problems['summary']['phase_std']:.2f}°")
    print(f"  Fonction de transfert : {problems['summary']['transfer_mean']:.4f} ± {problems['summary']['transfer_std']:.4f}")
    
    return problems

def generate_report(df, problems, output_dir):
    """Génère un rapport d'analyse"""
    print(f"\nGénération du rapport dans : {output_dir}")
    
    # Génération du nom de fichier avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    freq_min = df['frequence_Hz'].min()
    freq_max = df['frequence_Hz'].max()
    n_points = len(df)
    
    report_filename = f"rapport_{timestamp}_freq{freq_min:.0f}-{freq_max:.0f}Hz_{n_points}pts.txt"
    report_path = os.path.join(output_dir, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("RAPPORT D'ANALYSE - CALIBRATION DDS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Fichier source : {os.path.basename(df.name) if hasattr(df, 'name') else 'balayage_frequence.csv'}\n\n")
        
        f.write("📊 RÉSUMÉ DES MESURES\n")
        f.write("-" * 30 + "\n")
        f.write(f"Nombre total de mesures : {len(df)}\n")
        f.write(f"Plage de fréquences : {df['frequence_Hz'].min():.1f} Hz - {df['frequence_Hz'].max():.1f} Hz\n")
        f.write(f"Date de la première mesure : {df['timestamp'].iloc[0] if 'timestamp' in df.columns else 'N/A'}\n")
        f.write(f"Date de la dernière mesure : {df['timestamp'].iloc[-1] if 'timestamp' in df.columns else 'N/A'}\n\n")
        
        f.write("📈 STATISTIQUES DÉTAILLÉES\n")
        f.write("-" * 30 + "\n")
        f.write(f"Déphasage (CH4 par rapport à CH3) :\n")
        f.write(f"  Moyenne : {problems['summary']['phase_mean']:.2f}°\n")
        f.write(f"  Écart-type : {problems['summary']['phase_std']:.2f}°\n")
        f.write(f"  Min/Max : {problems['summary']['phase_min']:.2f}° / {problems['summary']['phase_max']:.2f}°\n\n")
        
        f.write(f"Fonction de transfert (VPP_CH4/VPP_CH3) :\n")
        f.write(f"  Moyenne : {problems['summary']['transfer_mean']:.4f}\n")
        f.write(f"  Écart-type : {problems['summary']['transfer_std']:.4f}\n")
        f.write(f"  Min/Max : {problems['summary']['transfer_min']:.4f} / {problems['summary']['transfer_max']:.4f}\n\n")
        
        f.write("⚠️ PROBLÈMES DÉTECTÉS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Problèmes de déphasage (> {PHASE_THRESHOLD}°) : {problems['summary']['phase_problems_count']}\n")
        if problems['phase_problems']:
            f.write("  Fréquences concernées :\n")
            for _, row in problems['phase_problems'].iterrows():
                f.write(f"    - {row['frequence_Hz']:.1f} Hz : {row['phase_deg']:.2f}°\n")
        
        f.write(f"\nProblèmes de fonction de transfert (hors [{TRANSFER_THRESHOLD_MIN}, {TRANSFER_THRESHOLD_MAX}]) : {problems['summary']['transfer_problems_count']}\n")
        if problems['transfer_problems']:
            f.write("  Fréquences concernées :\n")
            for _, row in problems['transfer_problems'].iterrows():
                f.write(f"    - {row['frequence_Hz']:.1f} Hz : {row['transfer_function']:.4f}\n")
        
        f.write("\n🎯 RECOMMANDATIONS\n")
        f.write("-" * 30 + "\n")
        if problems['summary']['phase_problems_count'] > 0:
            f.write("• Appliquer des corrections de phase pour les fréquences problématiques\n")
        if problems['summary']['transfer_problems_count'] > 0:
            f.write("• Appliquer des corrections d'amplitude pour les fréquences problématiques\n")
        if problems['summary']['phase_problems_count'] == 0 and problems['summary']['transfer_problems_count'] == 0:
            f.write("• Aucune correction nécessaire - système bien calibré\n")
        
        f.write("• Conserver les tables de correction pour utilisation future\n")
        f.write("• Relancer un balayage de validation après correction\n")
    
    print(f"✓ Rapport généré : {report_path}")
    
    # Sauvegarder les problèmes en CSV
    if problems['phase_problems']:
        phase_csv = os.path.join(output_dir, 'problemes_phase.csv')
        problems['phase_problems'].to_csv(phase_csv, index=False)
        print(f"✓ Problèmes de phase sauvegardés : {phase_csv}")
    
    if problems['transfer_problems']:
        transfer_csv = os.path.join(output_dir, 'problemes_transfert.csv')
        problems['transfer_problems'].to_csv(transfer_csv, index=False)
        print(f"✓ Problèmes de transfert sauvegardés : {transfer_csv}")
    
    return report_path

def main():
    # Mise à jour des seuils globaux (doit être fait avant l'utilisation dans parser)
    global PHASE_THRESHOLD, TRANSFER_THRESHOLD_MIN, TRANSFER_THRESHOLD_MAX
    
    parser = argparse.ArgumentParser(description='Analyse des résultats de calibration DDS')
    parser.add_argument('--csv', type=str, default=DEFAULT_CSV_PATH, 
                       help=f'Fichier CSV à analyser (défaut: {DEFAULT_CSV_PATH})')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_DIR, 
                       help=f'Dossier de sortie (défaut: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--phase-threshold', type=float, default=PHASE_THRESHOLD, 
                       help=f'Seuil de déphasage en degrés (défaut: {PHASE_THRESHOLD})')
    parser.add_argument('--transfer-min', type=float, default=TRANSFER_THRESHOLD_MIN, 
                       help=f'Seuil min fonction de transfert (défaut: {TRANSFER_THRESHOLD_MIN})')
    parser.add_argument('--transfer-max', type=float, default=TRANSFER_THRESHOLD_MAX, 
                       help=f'Seuil max fonction de transfert (défaut: {TRANSFER_THRESHOLD_MAX})')
    
    args = parser.parse_args()
    
    # Mise à jour des seuils globaux avec les valeurs des arguments
    PHASE_THRESHOLD = args.phase_threshold
    TRANSFER_THRESHOLD_MIN = args.transfer_min
    TRANSFER_THRESHOLD_MAX = args.transfer_max
    
    print("=== Analyse des résultats de calibration DDS ===")
    print(f"Seuils : déphasage ±{PHASE_THRESHOLD}°, transfert [{TRANSFER_THRESHOLD_MIN}, {TRANSFER_THRESHOLD_MAX}]")
    
    # Chargement des données
    df = load_data(args.csv)
    if df is None:
        return
    
    # Création des graphiques
    plot_path = create_plots(df, args.output)
    
    # Identification des problèmes
    problems = identify_problems(df)
    
    # Génération du rapport
    report_path = generate_report(df, problems, args.output)
    
    print(f"\n✅ Analyse terminée !")
    print(f"📊 Graphiques : {plot_path}")
    print(f"📄 Rapport : {report_path}")

if __name__ == "__main__":
    main() 