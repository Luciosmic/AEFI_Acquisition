#!/usr/bin/env python3
"""
Script pour visualiser les données d'acquisition CSV
Affiche les 8 canaux ADC en fonction du temps avec analyse de bruit
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from datetime import datetime
from scipy import stats
import seaborn as sns

def analyze_noise_statistics(valid_data, output_dir):
    """
    Analyse rapide du bruit pour chaque signal
    - Écart-type 
    - Distribution statistique (normalité, skewness, kurtosis)
    - Corrélation croisée entre les voies
    
    Args:
        valid_data (DataFrame): Données valides
        output_dir (str): Dossier de sortie pour les graphiques
    """
    
    adc_columns = ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                   'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4']
    
    print(f"\n🔬 ANALYSE DE BRUIT")
    print("=" * 50)
    
    # 1. Analyse de l'écart-type et statistiques de base
    print(f"\n📊 ÉCART-TYPE ET STATISTIQUES DE BASE:")
    noise_stats = {}
    
    for col in adc_columns:
        data = valid_data[col]
        mean_val = data.mean()
        std_val = data.std()
        rms_val = np.sqrt(np.mean(data**2))
        peak_to_peak = data.max() - data.min()
        
        noise_stats[col] = {
            'mean': mean_val,
            'std': std_val,
            'rms': rms_val,
            'peak_to_peak': peak_to_peak,
            'snr_db': 20 * np.log10(abs(mean_val) / std_val) if std_val > 0 else float('inf')
        }
        
        print(f"   {col:10}: σ={std_val:6.2f}  RMS={rms_val:6.2f}  P2P={peak_to_peak:6.0f}  SNR={noise_stats[col]['snr_db']:5.1f}dB")
    
    # 2. Analyse de la distribution statistique (normalité)
    print(f"\n📈 DISTRIBUTION STATISTIQUE (Test de normalité):")
    distribution_stats = {}
    
    for col in adc_columns:
        data = valid_data[col]
        
        # Test de normalité de Shapiro-Wilk (si N < 5000)
        if len(data) < 5000:
            shapiro_stat, shapiro_p = stats.shapiro(data)
        else:
            # Pour les gros échantillons, utiliser Kolmogorov-Smirnov
            shapiro_stat, shapiro_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        
        # Skewness (asymétrie) et Kurtosis
        skewness = stats.skew(data)
        kurtosis = stats.kurtosis(data)
        
        distribution_stats[col] = {
            'shapiro_stat': shapiro_stat,
            'shapiro_p': shapiro_p,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'is_normal': shapiro_p > 0.05
        }
        
        normal_status = "✅ Normal" if shapiro_p > 0.05 else "❌ Non-normal"
        print(f"   {col:10}: {normal_status}  p={shapiro_p:.4f}  Skew={skewness:5.2f}  Kurt={kurtosis:5.2f}")
    
    # 3. Matrice de corrélation croisée
    print(f"\n🔗 CORRÉLATION CROISÉE ENTRE VOIES:")
    correlation_matrix = valid_data[adc_columns].corr()
    
    # Afficher les corrélations significatives (> 0.3 ou < -0.3)
    print("   Corrélations significatives (|r| > 0.3):")
    significant_correlations = []
    
    for i, col1 in enumerate(adc_columns):
        for j, col2 in enumerate(adc_columns):
            if i < j:  # Éviter les doublons
                corr_val = correlation_matrix.loc[col1, col2]
                if abs(corr_val) > 0.3:
                    significant_correlations.append((col1, col2, corr_val))
                    print(f"     {col1} ↔ {col2}: r={corr_val:5.2f}")
    
    if not significant_correlations:
        print("     Aucune corrélation significative détectée")
    
    # 4. Créer les graphiques d'analyse
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    
    # Figure 1: Histogrammes des distributions
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    fig.suptitle('Distribution statistique des canaux ADC', fontsize=14)
    
    for idx, col in enumerate(adc_columns):
        row = idx // 4
        col_idx = idx % 4
        ax = axes[row, col_idx]
        
        data = valid_data[col]
        ax.hist(data, bins=50, alpha=0.7, density=True, color='skyblue', edgecolor='black')
        
        # Superposer une courbe normale théorique
        mu, sigma = data.mean(), data.std()
        x = np.linspace(data.min(), data.max(), 100)
        normal_curve = stats.norm.pdf(x, mu, sigma)
        ax.plot(x, normal_curve, 'r-', linewidth=2, label='Normal théorique')
        
        ax.set_title(f'{col}\nσ={sigma:.2f}, Skew={distribution_stats[col]["skewness"]:.2f}')
        ax.set_xlabel('Valeur ADC')
        ax.set_ylabel('Densité')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    distrib_file = os.path.join(output_dir, f"{timestamp}_noise_analysis_distributions.png")
    plt.savefig(distrib_file, dpi=300, bbox_inches='tight')
    print(f"💾 Distributions sauvegardées: {distrib_file}")
    plt.show()
    
    # Figure 2: Matrice de corrélation
    plt.figure(figsize=(10, 8))
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))  # Masquer la partie supérieure
    
    sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, fmt='.2f')
    
    plt.title('Matrice de corrélation croisée entre canaux ADC')
    plt.tight_layout()
    
    corr_file = os.path.join(output_dir, f"{timestamp}_noise_analysis_correlation.png")
    plt.savefig(corr_file, dpi=300, bbox_inches='tight')
    print(f"💾 Corrélations sauvegardées: {corr_file}")
    plt.show()
    
    # 5. Résumé des résultats
    print(f"\n📋 RÉSUMÉ DE L'ANALYSE:")
    print(f"   • Écart-type moyen: {np.mean([stats['std'] for stats in noise_stats.values()]):.2f}")
    print(f"   • SNR moyen: {np.mean([stats['snr_db'] for stats in noise_stats.values() if stats['snr_db'] != float('inf')]):.1f} dB")
    print(f"   • Canaux avec distribution normale: {sum([1 for stats in distribution_stats.values() if stats['is_normal']])}/{len(adc_columns)}")
    print(f"   • Corrélations significatives détectées: {len(significant_correlations)}")
    
    return noise_stats, distribution_stats, correlation_matrix

def plot_acquisition_data(csv_file):
    """
    Charge et affiche les données d'acquisition depuis un fichier CSV
    
    Args:
        csv_file (str): Chemin vers le fichier CSV
    """
    
    # Vérifier que le fichier existe
    if not os.path.exists(csv_file):
        print(f"❌ Fichier non trouvé: {csv_file}")
        return
    
    print(f"📊 Chargement des données: {os.path.basename(csv_file)}")
    
    try:
        # Charger les données
        df = pd.read_csv(csv_file)
        
        # Vérifier les colonnes nécessaires
        required_cols = ['timestamp', 'adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                        'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4', 'is_valid']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Colonnes manquantes: {missing_cols}")
            return
        
        # Filtrer uniquement les données valides
        valid_data = df[df['is_valid'] == True].copy()
        total_rows = len(df)
        valid_rows = len(valid_data)
        
        print(f"📈 Données totales: {total_rows}")
        print(f"✅ Données valides: {valid_rows} ({(valid_rows/total_rows)*100:.1f}%)")
        
        if valid_rows == 0:
            print("❌ Aucune donnée valide à afficher")
            return
        
        # Convertir timestamp en datetime si c'est une string
        if valid_data['timestamp'].dtype == 'object':
            valid_data['timestamp'] = pd.to_datetime(valid_data['timestamp'])
        
        # Créer un axe temporel relatif (en secondes depuis le début)
        start_time = valid_data['timestamp'].iloc[0]
        valid_data['time_rel'] = (valid_data['timestamp'] - start_time).dt.total_seconds()
        
        # Configuration de la figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Données d\'acquisition - {os.path.basename(csv_file)}', fontsize=14)
        
        # ADC1 - Canaux 1 et 2
        ax1.plot(valid_data['time_rel'], valid_data['adc1_ch1'], 'b-', linewidth=1, label='ADC1 Ch1', alpha=0.8)
        ax1.plot(valid_data['time_rel'], valid_data['adc1_ch2'], 'r-', linewidth=1, label='ADC1 Ch2', alpha=0.8)
        ax1.set_title('ADC1 - Canaux 1 & 2')
        ax1.set_xlabel('Temps (s)')
        ax1.set_ylabel('Valeur ADC')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # ADC1 - Canaux 3 et 4
        ax2.plot(valid_data['time_rel'], valid_data['adc1_ch3'], 'g-', linewidth=1, label='ADC1 Ch3', alpha=0.8)
        ax2.plot(valid_data['time_rel'], valid_data['adc1_ch4'], 'm-', linewidth=1, label='ADC1 Ch4', alpha=0.8)
        ax2.set_title('ADC1 - Canaux 3 & 4')
        ax2.set_xlabel('Temps (s)')
        ax2.set_ylabel('Valeur ADC')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # ADC2 - Canaux 1 et 2
        ax3.plot(valid_data['time_rel'], valid_data['adc2_ch1'], 'c-', linewidth=1, label='ADC2 Ch1', alpha=0.8)
        ax3.plot(valid_data['time_rel'], valid_data['adc2_ch2'], 'orange', linewidth=1, label='ADC2 Ch2', alpha=0.8)
        ax3.set_title('ADC2 - Canaux 1 & 2')
        ax3.set_xlabel('Temps (s)')
        ax3.set_ylabel('Valeur ADC')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # ADC2 - Canaux 3 et 4
        ax4.plot(valid_data['time_rel'], valid_data['adc2_ch3'], 'brown', linewidth=1, label='ADC2 Ch3', alpha=0.8)
        ax4.plot(valid_data['time_rel'], valid_data['adc2_ch4'], 'pink', linewidth=1, label='ADC2 Ch4', alpha=0.8)
        ax4.set_title('ADC2 - Canaux 3 & 4')
        ax4.set_xlabel('Temps (s)')
        ax4.set_ylabel('Valeur ADC')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Sauvegarder le graphique
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        csv_name = os.path.splitext(os.path.basename(csv_file))[0]
        output_file = os.path.join(os.path.dirname(csv_file), f"{timestamp}_plot_acquisition_{csv_name}.png")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"💾 Graphique sauvegardé: {output_file}")
        
        # Afficher le graphique
        plt.show()
        
        # Statistiques des données
        print(f"\n📊 Statistiques des données:")
        print(f"   Durée totale: {valid_data['time_rel'].iloc[-1]:.2f} secondes")
        print(f"   Nombre d'échantillons: {len(valid_data)}")
        print(f"   Fréquence moyenne: {len(valid_data)/valid_data['time_rel'].iloc[-1]:.2f} Hz")
        
        if 'acquisition_time_ms' in valid_data.columns:
            print(f"   Temps d'acquisition moyen: {valid_data['acquisition_time_ms'].mean():.2f} ms")
        
        # Plages de valeurs pour chaque canal
        adc_columns = ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                      'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4']
        
        print(f"\n📈 Plages de valeurs:")
        for col in adc_columns:
            min_val = valid_data[col].min()
            max_val = valid_data[col].max()
            mean_val = valid_data[col].mean()
            std_val = valid_data[col].std()
            print(f"   {col}: {min_val:.0f} à {max_val:.0f} (moy: {mean_val:.1f} ± {std_val:.1f})")
        
        # NOUVELLE SECTION: Analyse de bruit
        analyze_noise_statistics(valid_data, os.path.dirname(csv_file))
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")

def plot_all_channels_single_plot(csv_file):
    """
    Version alternative: tous les canaux sur un seul graphique
    """
    if not os.path.exists(csv_file):
        print(f"❌ Fichier non trouvé: {csv_file}")
        return
    
    try:
        df = pd.read_csv(csv_file)
        valid_data = df[df['is_valid'] == True].copy()
        
        if len(valid_data) == 0:
            print("❌ Aucune donnée valide")
            return
        
        # Convertir timestamp
        if valid_data['timestamp'].dtype == 'object':
            valid_data['timestamp'] = pd.to_datetime(valid_data['timestamp'])
        
        start_time = valid_data['timestamp'].iloc[0]
        valid_data['time_rel'] = (valid_data['timestamp'] - start_time).dt.total_seconds()
        
        # Graphique unique avec tous les canaux
        plt.figure(figsize=(15, 8))
        
        colors = ['blue', 'red', 'green', 'magenta', 'cyan', 'orange', 'brown', 'pink']
        adc_columns = ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                      'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4']
        
        for i, col in enumerate(adc_columns):
            plt.plot(valid_data['time_rel'], valid_data[col], 
                    color=colors[i], linewidth=1, label=col, alpha=0.8)
        
        plt.title(f'Tous les canaux ADC - {os.path.basename(csv_file)}')
        plt.xlabel('Temps (s)')
        plt.ylabel('Valeur ADC')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Sauvegarder
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        csv_name = os.path.splitext(os.path.basename(csv_file))[0]
        output_file = os.path.join(os.path.dirname(csv_file), f"{timestamp}_plot_all_channels_{csv_name}.png")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"💾 Graphique sauvegardé: {output_file}")
        
        plt.show()
        
        # NOUVELLE SECTION: Analyse de bruit pour le mode single plot aussi
        analyze_noise_statistics(valid_data, os.path.dirname(csv_file))
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    # Utilisation
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Par défaut, utiliser le fichier que vous avez mentionné
        csv_file = "results/2025-07-03_1048_dataWriting.csv"
        
        # Si le fichier par défaut n'existe pas, demander à l'utilisateur
        if not os.path.exists(csv_file):
            csv_file = input("📁 Chemin vers le fichier CSV: ").strip().strip('"')
    
    print("🎯 Choisissez le type de graphique:")
    print("1. Graphiques séparés par ADC (recommandé)")
    print("2. Tous les canaux sur un seul graphique")
    
    choice = input("Votre choix (1/2): ").strip()
    
    if choice == "2":
        plot_all_channels_single_plot(csv_file)
    else:
        plot_acquisition_data(csv_file) 