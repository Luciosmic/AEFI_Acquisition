#!/usr/bin/env python3
"""
Script de Post-traitement et Analyse Spectrale - Accéléromètre LSM9D
====================================================================

Ce script permet de :
- Analyser spectralement les données collectées par accelerometer_analysis_script.py
- Calculer la FFT et la densité spectrale de puissance (PSD)
- Identifier les fréquences dominantes et le niveau de bruit
- Comparer différentes expériences (statique vs mouvement)
- Générer des rapports d'analyse automatiques

Auteur: Post-traitement pour banc d'imagerie EF
Date: 2024
"""

import sys
import os
import json
import csv
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse

# Dépendances scientifiques
try:
    from scipy import signal, stats
    from scipy.fft import fft, fftfreq
    import pandas as pd
except ImportError as e:
    print(f"❌ Dépendance manquante: {e}")
    print("Installation requise: pip install scipy pandas matplotlib")
    sys.exit(1)

# Utiliser la configuration centralisée
from config_paths import DATA_DIRECTORY, RESULTS_DIRECTORY

class AccelerometerSpectralAnalyzer:
    """
    Analyseur spectral pour les données de l'accéléromètre LSM9D.
    """
    
    def __init__(self, data_directory=None):
        """
        Initialise l'analyseur spectral.
        
        :param data_directory: Répertoire contenant les données à analyser (utilise la config par défaut si None)
        """
        # Utiliser la configuration centralisée
        self.data_directory = Path(data_directory) if data_directory else DATA_DIRECTORY
        self.results_directory = RESULTS_DIRECTORY
        self.results_directory.mkdir(exist_ok=True)
        
        # Configuration de l'analyse
        self.config = {
            'sampling_rate_default': 20.0,  # Hz
            'freq_bands': {
                'low': (0.1, 2.0),      # Basses fréquences
                'mid': (2.0, 8.0),      # Moyennes fréquences  
                'high': (8.0, 10.0)     # Hautes fréquences
            },
            'window_types': ['hann', 'blackman', 'hamming'],
            'plot_style': {
                'figsize': (15, 10),
                'dpi': 300,
                'style': 'seaborn-v0_8'
            }
        }
        
        # Résultats d'analyse
        self.experiments = {}
        self.analysis_results = {}
        
    def load_experiment_data(self, csv_file: str) -> Dict:
        """
        Charge les données d'une expérience depuis un fichier CSV.
        
        :param csv_file: Chemin vers le fichier CSV
        :return: Dictionnaire contenant les données et métadonnées
        """
        csv_path = Path(csv_file)
        if not csv_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {csv_file}")
        
        # Charger les paramètres JSON s'ils existent
        json_file = csv_path.with_name(csv_path.stem + '_params.json')
        params = {}
        if json_file.exists():
            with open(json_file, 'r') as f:
                params = json.load(f)
        
        # Charger les données CSV
        df = pd.read_csv(csv_file)
        
        # Vérifier les colonnes requises
        required_cols = ['timestamp', 'time_relative', 'acc_x', 'acc_y', 'acc_z']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colonnes manquantes: {missing_cols}")
        
        # Calculer la fréquence d'échantillonnage réelle
        if len(df) > 1:
            dt = np.diff(df['time_relative'].values)
            sampling_rate = 1.0 / np.median(dt[dt > 0])
        else:
            sampling_rate = params.get('actual_sampling_rate', self.config['sampling_rate_default'])
        
        experiment_data = {
            'data': df,
            'params': params,
            'sampling_rate': sampling_rate,
            'duration': df['time_relative'].iloc[-1] if len(df) > 0 else 0,
            'filename': csv_path.name,
            'experiment_type': params.get('type', 'unknown')
        }
        
        print(f"✅ Données chargées: {csv_path.name}")
        print(f"   📊 {len(df)} points, {sampling_rate:.1f} Hz, {experiment_data['duration']:.1f}s")
        
        return experiment_data
    
    def calculate_fft_spectrum(self, signal_data: np.ndarray, sampling_rate: float, 
                             window: str = 'hann') -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule le spectre FFT d'un signal.
        
        :param signal_data: Données du signal
        :param sampling_rate: Fréquence d'échantillonnage
        :param window: Type de fenêtrage
        :return: (fréquences, amplitudes)
        """
        # Appliquer la fenêtre
        if window == 'hann':
            windowed_signal = signal_data * np.hanning(len(signal_data))
        elif window == 'blackman':
            windowed_signal = signal_data * np.blackman(len(signal_data))
        elif window == 'hamming':
            windowed_signal = signal_data * np.hamming(len(signal_data))
        else:
            windowed_signal = signal_data
        
        # Calculer la FFT
        fft_values = fft(windowed_signal)
        fft_freqs = fftfreq(len(windowed_signal), 1/sampling_rate)
        
        # Prendre seulement les fréquences positives
        positive_freqs = fft_freqs[:len(fft_freqs)//2]
        fft_magnitude = np.abs(fft_values[:len(fft_values)//2])
        
        # Normaliser
        fft_magnitude = fft_magnitude / len(signal_data)
        
        return positive_freqs, fft_magnitude
    
    def calculate_psd(self, signal_data: np.ndarray, sampling_rate: float, 
                     method: str = 'welch') -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule la densité spectrale de puissance (PSD).
        
        :param signal_data: Données du signal
        :param sampling_rate: Fréquence d'échantillonnage
        :param method: Méthode de calcul ('welch', 'periodogram')
        :return: (fréquences, PSD)
        """
        if method == 'welch':
            # Utiliser la méthode de Welch avec overlap
            freqs, psd = signal.welch(
                signal_data, 
                fs=sampling_rate,
                window='hann',
                nperseg=min(len(signal_data)//4, 512),
                overlap=0.5
            )
        else:
            # Periodogramme simple
            freqs, psd = signal.periodogram(signal_data, fs=sampling_rate)
        
        return freqs, psd
    
    def analyze_noise_characteristics(self, signal_data: np.ndarray, 
                                    sampling_rate: float) -> Dict:
        """
        Analyse les caractéristiques de bruit d'un signal.
        
        :param signal_data: Données du signal
        :param sampling_rate: Fréquence d'échantillonnage
        :return: Dictionnaire des métriques de bruit
        """
        # Statistiques temporelles
        mean_val = np.mean(signal_data)
        std_val = np.std(signal_data)
        rms_val = np.sqrt(np.mean(signal_data**2))
        peak_to_peak = np.max(signal_data) - np.min(signal_data)
        
        # Analyse spectrale
        freqs, psd = self.calculate_psd(signal_data, sampling_rate)
        
        # Puissance par bandes de fréquence
        band_powers = {}
        for band_name, (f_low, f_high) in self.config['freq_bands'].items():
            mask = (freqs >= f_low) & (freqs <= f_high)
            band_powers[band_name] = np.trapz(psd[mask], freqs[mask])
        
        # Fréquence dominante
        dominant_freq_idx = np.argmax(psd[1:]) + 1  # Exclure DC
        dominant_freq = freqs[dominant_freq_idx]
        dominant_power = psd[dominant_freq_idx]
        
        # Densité spectrale de bruit (moyenne hors pics)
        # Exclure les 5% de valeurs les plus élevées pour estimer le plancher de bruit
        sorted_psd = np.sort(psd[1:])  # Exclure DC
        noise_floor_idx = int(0.95 * len(sorted_psd))
        noise_floor = np.mean(sorted_psd[:noise_floor_idx])
        
        return {
            'temporal': {
                'mean': mean_val,
                'std': std_val,
                'rms': rms_val,
                'peak_to_peak': peak_to_peak,
                'snr_estimate': abs(mean_val) / std_val if std_val > 0 else float('inf')
            },
            'spectral': {
                'dominant_frequency': dominant_freq,
                'dominant_power': dominant_power,
                'noise_floor': noise_floor,
                'total_power': np.trapz(psd, freqs),
                'band_powers': band_powers
            },
            'frequencies': freqs,
            'psd': psd
        }
    
    def compare_experiments(self, static_data: Dict, movement_data: Dict) -> Dict:
        """
        Compare une expérience statique avec une expérience en mouvement.
        
        :param static_data: Données de l'expérience statique
        :param movement_data: Données de l'expérience en mouvement
        :return: Résultats de comparaison
        """
        comparison = {
            'static_experiment': static_data['filename'],
            'movement_experiment': movement_data['filename'],
            'analysis': {}
        }
        
        # Analyser chaque axe
        for axis in ['x', 'y', 'z']:
            col_name = f'acc_{axis}'
            
            # Données statiques
            static_signal = static_data['data'][col_name].values
            static_analysis = self.analyze_noise_characteristics(
                static_signal, static_data['sampling_rate']
            )
            
            # Données en mouvement
            movement_signal = movement_data['data'][col_name].values
            movement_analysis = self.analyze_noise_characteristics(
                movement_signal, movement_data['sampling_rate']
            )
            
            # Calculs de comparaison
            noise_increase = {
                'std_ratio': movement_analysis['temporal']['std'] / static_analysis['temporal']['std'],
                'rms_ratio': movement_analysis['temporal']['rms'] / static_analysis['temporal']['rms'],
                'power_ratio': movement_analysis['spectral']['total_power'] / static_analysis['spectral']['total_power']
            }
            
            comparison['analysis'][axis] = {
                'static': static_analysis,
                'movement': movement_analysis,
                'noise_increase': noise_increase
            }
        
        return comparison
    
    def generate_spectral_plots(self, experiment_data: Dict, save_path: Optional[str] = None):
        """
        Génère les graphiques d'analyse spectrale pour une expérience.
        
        :param experiment_data: Données de l'expérience
        :param save_path: Chemin de sauvegarde optionnel
        """
        try:
            plt.style.use(self.config['plot_style']['style'])
        except:
            pass  # Style non disponible
        
        fig, axes = plt.subplots(3, 3, figsize=self.config['plot_style']['figsize'])
        fig.suptitle(f"Analyse Spectrale - {experiment_data['filename']}", fontsize=16)
        
        axes_names = ['X', 'Y', 'Z']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, axis in enumerate(['x', 'y', 'z']):
            col_name = f'acc_{axis}'
            signal_data = experiment_data['data'][col_name].values
            time_data = experiment_data['data']['time_relative'].values
            sampling_rate = experiment_data['sampling_rate']
            
            # Analyser le signal
            analysis = self.analyze_noise_characteristics(signal_data, sampling_rate)
            
            # 1. Signal temporel
            ax1 = axes[i, 0]
            ax1.plot(time_data, signal_data, color=colors[i], linewidth=0.8)
            ax1.set_title(f'Accélération {axes_names[i]} - Temporel')
            ax1.set_xlabel('Temps (s)')
            ax1.set_ylabel('Accélération (m/s²)')
            ax1.grid(True, alpha=0.3)
            
            # Ajouter statistiques
            stats_text = f"Moy: {analysis['temporal']['mean']:.4f}\n"
            stats_text += f"Std: {analysis['temporal']['std']:.4f}\n"
            stats_text += f"RMS: {analysis['temporal']['rms']:.4f}"
            ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # 2. FFT
            ax2 = axes[i, 1]
            freqs, fft_mag = self.calculate_fft_spectrum(signal_data, sampling_rate)
            ax2.semilogy(freqs, fft_mag, color=colors[i], linewidth=1.0)
            ax2.set_title(f'FFT - Axe {axes_names[i]}')
            ax2.set_xlabel('Fréquence (Hz)')
            ax2.set_ylabel('Amplitude')
            ax2.grid(True, alpha=0.3)
            ax2.set_xlim(0, sampling_rate/2)
            
            # 3. PSD
            ax3 = axes[i, 2]
            freqs_psd = analysis['frequencies']
            psd = analysis['psd']
            ax3.loglog(freqs_psd, psd, color=colors[i], linewidth=1.0)
            ax3.set_title(f'PSD - Axe {axes_names[i]}')
            ax3.set_xlabel('Fréquence (Hz)')
            ax3.set_ylabel('PSD (m²/s⁴/Hz)')
            ax3.grid(True, alpha=0.3)
            
            # Marquer la fréquence dominante
            dom_freq = analysis['spectral']['dominant_frequency']
            dom_power = analysis['spectral']['dominant_power']
            ax3.axvline(dom_freq, color='red', linestyle='--', alpha=0.7)
            ax3.text(dom_freq, dom_power, f' {dom_freq:.1f} Hz', 
                    verticalalignment='bottom', color='red')
        
        plt.tight_layout()
        
        # Sauvegarder si demandé
        if save_path:
            plt.savefig(save_path, dpi=self.config['plot_style']['dpi'], 
                       bbox_inches='tight')
            print(f"📊 Graphique sauvegardé: {save_path}")
        
        return fig
    
    def generate_comparison_plot(self, comparison_data: Dict, save_path: Optional[str] = None):
        """
        Génère un graphique de comparaison entre expériences statique et dynamique.
        
        :param comparison_data: Données de comparaison
        :param save_path: Chemin de sauvegarde optionnel
        """
        try:
            plt.style.use(self.config['plot_style']['style'])
        except:
            pass
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Comparaison Statique vs Mouvement', fontsize=16)
        
        axes_names = ['X', 'Y', 'Z']
        colors_static = ['#FF9999', '#99DDDD', '#99BBFF']
        colors_movement = ['#FF3333', '#33BBBB', '#3377FF']
        
        for i, axis in enumerate(['x', 'y', 'z']):
            analysis = comparison_data['analysis'][axis]
            
            # 1. Comparaison PSD
            ax1 = axes[0, i]
            
            static_freqs = analysis['static']['frequencies']
            static_psd = analysis['static']['psd']
            movement_freqs = analysis['movement']['frequencies']
            movement_psd = analysis['movement']['psd']
            
            ax1.loglog(static_freqs, static_psd, color=colors_static[i], 
                      linewidth=1.5, label='Statique', alpha=0.8)
            ax1.loglog(movement_freqs, movement_psd, color=colors_movement[i], 
                      linewidth=1.5, label='Mouvement', alpha=0.8)
            
            ax1.set_title(f'PSD Comparaison - Axe {axes_names[i]}')
            ax1.set_xlabel('Fréquence (Hz)')
            ax1.set_ylabel('PSD (m²/s⁴/Hz)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. Comparaison métriques
            ax2 = axes[1, i]
            
            metrics = ['std', 'rms', 'peak_to_peak']
            static_values = [analysis['static']['temporal'][m] for m in metrics]
            movement_values = [analysis['movement']['temporal'][m] for m in metrics]
            
            x_pos = np.arange(len(metrics))
            width = 0.35
            
            ax2.bar(x_pos - width/2, static_values, width, 
                   color=colors_static[i], label='Statique', alpha=0.8)
            ax2.bar(x_pos + width/2, movement_values, width, 
                   color=colors_movement[i], label='Mouvement', alpha=0.8)
            
            ax2.set_title(f'Métriques Temporelles - Axe {axes_names[i]}')
            ax2.set_xlabel('Métrique')
            ax2.set_ylabel('Valeur (m/s²)')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels(['Std', 'RMS', 'Peak-to-Peak'])
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config['plot_style']['dpi'], 
                       bbox_inches='tight')
            print(f"📊 Graphique de comparaison sauvegardé: {save_path}")
        
        return fig
    
    def generate_analysis_report(self, analysis_results: Dict, output_file: str):
        """
        Génère un rapport d'analyse au format texte.
        
        :param analysis_results: Résultats de l'analyse
        :param output_file: Fichier de sortie
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT D'ANALYSE SPECTRALE - ACCÉLÉROMÈTRE LSM9D\n")
            f.write("=" * 80 + "\n")
            f.write(f"Généré le: {timestamp}\n\n")
            
            for exp_name, results in analysis_results.items():
                f.write(f"\n{'='*60}\n")
                f.write(f"EXPÉRIENCE: {exp_name}\n")
                f.write(f"{'='*60}\n")
                
                if 'single_analysis' in results:
                    # Analyse simple
                    data = results['single_analysis']
                    f.write(f"Type: {data['experiment_type']}\n")
                    f.write(f"Durée: {data['duration']:.1f}s\n")
                    f.write(f"Fréquence d'échantillonnage: {data['sampling_rate']:.1f} Hz\n\n")
                    
                    for axis in ['x', 'y', 'z']:
                        f.write(f"\nAxe {axis.upper()}:\n")
                        f.write(f"-" * 20 + "\n")
                        
                        if 'analysis_per_axis' in results and axis in results['analysis_per_axis']:
                            analysis = results['analysis_per_axis'][axis]
                            
                            # Métriques temporelles
                            temp = analysis['temporal']
                            f.write(f"  Temporel:\n")
                            f.write(f"    Moyenne: {temp['mean']:.6f} m/s²\n")
                            f.write(f"    Écart-type: {temp['std']:.6f} m/s²\n")
                            f.write(f"    RMS: {temp['rms']:.6f} m/s²\n")
                            f.write(f"    Peak-to-Peak: {temp['peak_to_peak']:.6f} m/s²\n")
                            f.write(f"    SNR estimé: {temp['snr_estimate']:.2f}\n")
                            
                            # Métriques spectrales
                            spec = analysis['spectral']
                            f.write(f"  Spectral:\n")
                            f.write(f"    Fréquence dominante: {spec['dominant_frequency']:.2f} Hz\n")
                            f.write(f"    Puissance dominante: {spec['dominant_power']:.2e}\n")
                            f.write(f"    Plancher de bruit: {spec['noise_floor']:.2e}\n")
                            f.write(f"    Puissance totale: {spec['total_power']:.2e}\n")
                            
                            # Puissance par bandes
                            f.write(f"  Puissance par bandes:\n")
                            for band, power in spec['band_powers'].items():
                                f.write(f"    {band}: {power:.2e}\n")
                
                elif 'comparison' in results:
                    # Analyse comparative
                    comp = results['comparison']
                    f.write(f"Expérience statique: {comp['static_experiment']}\n")
                    f.write(f"Expérience mouvement: {comp['movement_experiment']}\n\n")
                    
                    for axis in ['x', 'y', 'z']:
                        f.write(f"\nComparaison Axe {axis.upper()}:\n")
                        f.write(f"-" * 30 + "\n")
                        
                        if axis in comp['analysis']:
                            noise_inc = comp['analysis'][axis]['noise_increase']
                            f.write(f"  Augmentation du bruit:\n")
                            f.write(f"    Ratio Std: {noise_inc['std_ratio']:.2f}x\n")
                            f.write(f"    Ratio RMS: {noise_inc['rms_ratio']:.2f}x\n")
                            f.write(f"    Ratio Puissance: {noise_inc['power_ratio']:.2f}x\n")
        
        print(f"📄 Rapport généré: {output_file}")
    
    def analyze_single_experiment(self, csv_file: str) -> Dict:
        """
        Analyse une expérience individuelle.
        
        :param csv_file: Fichier CSV à analyser
        :return: Résultats d'analyse
        """
        print(f"\n🔍 Analyse de l'expérience: {csv_file}")
        
        # Charger les données
        experiment_data = self.load_experiment_data(csv_file)
        
        # Analyser chaque axe
        analysis_per_axis = {}
        for axis in ['x', 'y', 'z']:
            col_name = f'acc_{axis}'
            signal_data = experiment_data['data'][col_name].values
            analysis_per_axis[axis] = self.analyze_noise_characteristics(
                signal_data, experiment_data['sampling_rate']
            )
        
        # Générer les graphiques
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = self.results_directory / f"spectral_analysis_{experiment_data['filename']}_{timestamp}.png"
        self.generate_spectral_plots(experiment_data, plot_filename)
        
        results = {
            'single_analysis': experiment_data,
            'analysis_per_axis': analysis_per_axis,
            'plot_file': plot_filename
        }
        
        return results
    
    def run_batch_analysis(self):
        """
        Lance l'analyse de tous les fichiers dans le répertoire de données.
        """
        print(f"🔬 Analyse en lot du répertoire: {self.data_directory}")
        
        if not self.data_directory.exists():
            print(f"❌ Répertoire non trouvé: {self.data_directory}")
            return
        
        # Trouver tous les fichiers CSV
        csv_files = list(self.data_directory.glob("*.csv"))
        if not csv_files:
            print(f"❌ Aucun fichier CSV trouvé dans {self.data_directory}")
            return
        
        print(f"📂 {len(csv_files)} fichiers trouvés")
        
        # Analyser chaque fichier
        for csv_file in csv_files:
            try:
                results = self.analyze_single_experiment(str(csv_file))
                self.analysis_results[csv_file.stem] = results
                
            except Exception as e:
                print(f"❌ Erreur analyse {csv_file.name}: {e}")
        
        # Rechercher des paires statique/mouvement pour comparaison
        self._find_and_compare_experiments()
        
        # Générer le rapport final
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_directory / f"analysis_report_{timestamp}.txt"
        self.generate_analysis_report(self.analysis_results, report_file)
        
        print(f"\n✅ Analyse terminée. Résultats dans: {self.results_directory}")
    
    def _find_and_compare_experiments(self):
        """
        Trouve et compare automatiquement les expériences statiques et dynamiques.
        """
        # Identifier les expériences par type
        noise_experiments = []
        movement_experiments = []
        
        for exp_name, results in self.analysis_results.items():
            if 'single_analysis' in results:
                exp_type = results['single_analysis'].get('experiment_type', '')
                if 'noise' in exp_type.lower():
                    noise_experiments.append((exp_name, results))
                elif 'movement' in exp_type.lower():
                    movement_experiments.append((exp_name, results))
        
        # Faire des comparaisons si possible
        if noise_experiments and movement_experiments:
            print(f"\n🔄 Comparaison automatique trouvée:")
            print(f"   📊 {len(noise_experiments)} expérience(s) statique(s)")
            print(f"   🏃 {len(movement_experiments)} expérience(s) dynamique(s)")
            
            # Prendre la première de chaque type pour comparaison
            static_exp = noise_experiments[0]
            movement_exp = movement_experiments[0]
            
            comparison = self.compare_experiments(
                static_exp[1]['single_analysis'],
                movement_exp[1]['single_analysis']
            )
            
            # Générer le graphique de comparaison
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comp_plot_file = self.results_directory / f"comparison_{timestamp}.png"
            self.generate_comparison_plot(comparison, comp_plot_file)
            
            # Sauvegarder les résultats
            comparison_name = f"comparison_{static_exp[0]}_vs_{movement_exp[0]}"
            self.analysis_results[comparison_name] = {
                'comparison': comparison,
                'comparison_plot': comp_plot_file
            }

def main():
    """Fonction principale avec interface en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Analyse spectrale des données d'accéléromètre LSM9D"
    )
    parser.add_argument(
        '--data-dir', 
        default='accelerometer_data',
        help='Répertoire contenant les données (défaut: accelerometer_data)'
    )
    parser.add_argument(
        '--file', 
        help='Analyser un fichier spécifique au lieu du répertoire entier'
    )
    parser.add_argument(
        '--output-dir',
        default='analysis_results',
        help='Répertoire de sortie (défaut: analysis_results)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔬 ANALYSEUR SPECTRAL - ACCÉLÉROMÈTRE LSM9D")
    print("=" * 80)
    
    # Créer l'analyseur
    analyzer = AccelerometerSpectralAnalyzer(args.data_dir)
    analyzer.results_directory = Path(args.output_dir)
    analyzer.results_directory.mkdir(exist_ok=True)
    
    try:
        if args.file:
            # Analyser un fichier spécifique
            print(f"📊 Analyse du fichier: {args.file}")
            results = analyzer.analyze_single_experiment(args.file)
            
            # Générer un mini-rapport
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = analyzer.results_directory / f"single_analysis_report_{timestamp}.txt"
            analyzer.analysis_results['single_file'] = results
            analyzer.generate_analysis_report(analyzer.analysis_results, report_file)
            
        else:
            # Analyse en lot
            analyzer.run_batch_analysis()
        
        print("\n🎉 Analyse spectrale terminée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 