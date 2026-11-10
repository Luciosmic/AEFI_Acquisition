#!/usr/bin/env python3
"""
Analyse de dérive des signaux parasites électroniques.

Objectif :
- Comparer plusieurs sessions de caractérisation
- Détecter les dérives temporelles des offsets et signaux parasites  
- Générer rapports de stabilité électronique
- Recommandations pour fréquence de re-calibration

Auteur: Luis Saluden  
Date: 2025-01-27
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict, Optional
import glob

class ParasiticSignalsDriftAnalyzer:
    """
    Analyseur de dérive des signaux parasites entre sessions
    """
    
    def __init__(self, data_directory="."):
        """
        Args:
            data_directory: Répertoire contenant les fichiers de caractérisation
        """
        self.data_dir = data_directory
        self.sessions = []
        self.comparison_results = {}
        
    def load_sessions(self, pattern="*_parasitic_signals_characterization.json") -> int:
        """
        Charge toutes les sessions de caractérisation
        Args:
            pattern: Pattern de fichiers à charger
        Returns:
            Nombre de sessions chargées
        """
        json_files = glob.glob(os.path.join(self.data_dir, pattern))
        
        print(f"🔍 Recherche sessions: {pattern}")
        print(f"   Répertoire: {self.data_dir}")
        print(f"   Fichiers trouvés: {len(json_files)}")
        
        self.sessions = []
        
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r') as f:
                    session_data = json.load(f)
                
                # Extraction métadonnées session
                metadata = session_data.get('metadata', {})
                session_info = {
                    'filename': os.path.basename(json_file),
                    'session_id': os.path.splitext(os.path.basename(json_file))[0].replace('_parasitic_signals_characterization', ''),
                    'timestamp_start': metadata.get('timestamp_start'),
                    'timestamp_end': metadata.get('timestamp_end'),
                    'frequencies': metadata.get('frequencies_hz', []),
                    'config': metadata.get('measurement_config', {}),
                    'results': session_data.get('results', [])
                }
                
                self.sessions.append(session_info)
                print(f"   ✅ {session_info['session_id']}: {len(session_info['results'])} mesures")
                
            except Exception as e:
                print(f"   ❌ Erreur chargement {json_file}: {e}")
        
        print(f"\n📊 {len(self.sessions)} sessions chargées")
        return len(self.sessions)
    
    def analyze_drift_by_frequency(self, channel='adc1_ch1', metric='mean') -> Dict:
        """
        Analyse la dérive d'un canal spécifique en fonction de la fréquence
        Args:
            channel: Canal à analyser (ex: 'adc1_ch1')
            metric: Métrique à analyser ('mean', 'std', 'rms')
        Returns:
            Dictionnaire avec résultats d'analyse
        """
        if len(self.sessions) < 2:
            print(f"❌ Besoin d'au moins 2 sessions pour analyser la dérive")
            return {}
        
        print(f"📈 Analyse dérive {channel}.{metric}")
        
        # Collecte données par fréquence
        frequency_data = {}  # freq -> [session1_value, session2_value, ...]
        
        for session in self.sessions:
            for result in session['results']:
                freq = result['frequency_hz']
                
                if channel in result.get('channels', {}):
                    value = result['channels'][channel].get(metric, np.nan)
                    
                    if freq not in frequency_data:
                        frequency_data[freq] = []
                    frequency_data[freq].append(value)
        
        # Analyse statistique par fréquence
        drift_analysis = {
            'channel': channel,
            'metric': metric,
            'n_sessions': len(self.sessions),
            'frequencies': []
        }
        
        for freq in sorted(frequency_data.keys()):
            values = frequency_data[freq]
            
            if len(values) >= 2:  # Au moins 2 sessions
                freq_stats = {
                    'frequency_hz': freq,
                    'n_measurements': len(values),
                    'values': values,
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'range': np.max(values) - np.min(values),
                    'cv_percent': 100 * np.std(values) / abs(np.mean(values)) if np.mean(values) != 0 else np.inf,
                    'drift_absolute': np.max(values) - np.min(values),
                    'drift_relative_percent': 100 * (np.max(values) - np.min(values)) / abs(np.mean(values)) if np.mean(values) != 0 else np.inf
                }
                drift_analysis['frequencies'].append(freq_stats)
        
        print(f"   ✅ Analysé {len(drift_analysis['frequencies'])} fréquences")
        return drift_analysis
    
    def compute_global_stability(self) -> Dict:
        """
        Calcule les métriques de stabilité globale
        Returns:
            Dictionnaire avec métriques de stabilité
        """
        channels = ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                   'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4']
        metrics = ['mean', 'std', 'rms']
        
        stability_report = {
            'n_sessions': len(self.sessions),
            'session_ids': [s['session_id'] for s in self.sessions],
            'channels': {}
        }
        
        for channel in channels:
            stability_report['channels'][channel] = {}
            
            for metric in metrics:
                drift_data = self.analyze_drift_by_frequency(channel, metric)
                
                if drift_data and drift_data['frequencies']:
                    # Métriques globales de stabilité
                    all_cv = [f['cv_percent'] for f in drift_data['frequencies'] if not np.isinf(f['cv_percent'])]
                    all_drift_rel = [f['drift_relative_percent'] for f in drift_data['frequencies'] if not np.isinf(f['drift_relative_percent'])]
                    
                    stability_report['channels'][channel][metric] = {
                        'n_frequencies': len(drift_data['frequencies']),
                        'mean_cv_percent': np.mean(all_cv) if all_cv else np.nan,
                        'max_cv_percent': np.max(all_cv) if all_cv else np.nan,
                        'mean_drift_relative_percent': np.mean(all_drift_rel) if all_drift_rel else np.nan,
                        'max_drift_relative_percent': np.max(all_drift_rel) if all_drift_rel else np.nan,
                        'frequencies_unstable': len([f for f in drift_data['frequencies'] if f['cv_percent'] > 5.0]),  # CV > 5%
                        'stability_rating': self._compute_stability_rating(all_cv, all_drift_rel)
                    }
        
        return stability_report
    
    def _compute_stability_rating(self, cv_values: List[float], drift_values: List[float]) -> str:
        """
        Évalue la stabilité globale
        Args:
            cv_values: Coefficients de variation (%)
            drift_values: Dérives relatives (%)
        Returns:
            Rating de stabilité ('excellent', 'good', 'fair', 'poor')
        """
        if not cv_values or not drift_values:
            return 'unknown'
        
        max_cv = np.max(cv_values) if cv_values else np.inf
        max_drift = np.max(drift_values) if drift_values else np.inf
        
        if max_cv < 1.0 and max_drift < 2.0:
            return 'excellent'
        elif max_cv < 3.0 and max_drift < 5.0:
            return 'good'
        elif max_cv < 8.0 and max_drift < 15.0:
            return 'fair'
        else:
            return 'poor'
    
    def generate_drift_plots(self, output_dir=".", channels=['adc1_ch1', 'adc1_ch3', 'adc2_ch1']) -> List[str]:
        """
        Génère graphiques de dérive pour les canaux principaux
        Args:
            output_dir: Répertoire de sortie
            channels: Canaux à tracer
        Returns:
            Liste des fichiers générés
        """
        if len(self.sessions) < 2:
            print("❌ Besoin d'au moins 2 sessions pour tracer la dérive")
            return []
        
        print(f"📊 Génération graphiques dérive...")
        generated_files = []
        
        for channel in channels:
            print(f"   Graphique {channel}...")
            
            # Analyse dérive pour moyennes
            drift_data = self.analyze_drift_by_frequency(channel, 'mean')
            
            if not drift_data or not drift_data['frequencies']:
                continue
            
            # Préparation données plotting
            frequencies = [f['frequency_hz'] for f in drift_data['frequencies']]
            means = [f['mean'] for f in drift_data['frequencies']]
            stds = [f['std'] for f in drift_data['frequencies']]
            ranges = [f['range'] for f in drift_data['frequencies']]
            
            # Création figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Subplot 1: Valeurs moyennes avec barres d'erreur
            ax1.errorbar(frequencies, means, yerr=stds, fmt='o-', capsize=5, markersize=4)
            ax1.set_xscale('log')
            ax1.set_xlabel('Fréquence (Hz)')
            ax1.set_ylabel(f'{channel} - Valeur moyenne (codes ADC)')
            ax1.set_title(f'Dérive {channel} - Valeurs moyennes par fréquence\n({len(self.sessions)} sessions)')
            ax1.grid(True, alpha=0.3)
            
            # Subplot 2: Étendue de dérive
            ax2.semilogx(frequencies, ranges, 'ro-', markersize=4)
            ax2.set_xlabel('Fréquence (Hz)')
            ax2.set_ylabel('Étendue dérive (max - min)')
            ax2.set_title(f'Amplitude de dérive par fréquence')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Sauvegarde
            filename = f"drift_analysis_{channel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            generated_files.append(filename)
            print(f"     ✅ {filename}")
        
        return generated_files
    
    def export_drift_report(self, output_dir=".", session_id=None) -> str:
        """
        Exporte rapport complet de dérive
        Args:
            output_dir: Répertoire de sortie
            session_id: ID du rapport (auto si None)
        Returns:
            Nom du fichier de rapport
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        report_filename = f"{session_id}_drift_analysis_report.json"
        report_path = os.path.join(output_dir, report_filename)
        
        # Calcul stabilité globale
        stability_report = self.compute_global_stability()
        
        # Rapport complet
        full_report = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.0',
                'data_directory': self.data_dir,
                'sessions_analyzed': len(self.sessions)
            },
            'sessions_info': [{
                'session_id': s['session_id'],
                'timestamp_start': s['timestamp_start'],
                'n_measurements': len(s['results'])
            } for s in self.sessions],
            'stability_report': stability_report,
            'recommendations': self._generate_recommendations(stability_report)
        }
        
        # Export JSON
        with open(report_path, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        print(f"💾 Rapport exporté: {report_filename}")
        return report_filename
    
    def _generate_recommendations(self, stability_report: Dict) -> List[str]:
        """
        Génère recommandations basées sur l'analyse de stabilité
        Args:
            stability_report: Rapport de stabilité
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        # Analyse globale
        poor_channels = []
        for channel, metrics in stability_report['channels'].items():
            for metric, data in metrics.items():
                if data.get('stability_rating') in ['poor', 'fair']:
                    poor_channels.append(f"{channel}.{metric}")
        
        if len(poor_channels) == 0:
            recommendations.append("✅ Excellente stabilité électronique détectée sur tous les canaux")
            recommendations.append("📅 Recommandation: Re-calibration mensuelle suffisante")
        elif len(poor_channels) < 5:
            recommendations.append(f"⚠️ Instabilité détectée sur {len(poor_channels)} canaux: {', '.join(poor_channels[:3])}")
            recommendations.append("📅 Recommandation: Re-calibration hebdomadaire conseillée")
            recommendations.append("🔧 Vérifier l'alimentation et la thermique du banc")
        else:
            recommendations.append(f"❌ Instabilité majeure détectée sur {len(poor_channels)} canaux")
            recommendations.append("📅 Recommandation: Re-calibration quotidienne nécessaire")
            recommendations.append("🔧 URGENT: Vérifier l'électronique, masses, blindages")
            recommendations.append("🌡️ Vérifier stabilité thermique environnementale")
        
        # Recommandations spécifiques
        if stability_report['n_sessions'] < 5:
            recommendations.append("📊 Acquérir plus de sessions pour statistiques robustes (min 5)")
        
        return recommendations


def main():
    """Script principal d'analyse de dérive"""
    print("📈 ANALYSE DE DÉRIVE - SIGNAUX PARASITES ÉLECTRONIQUES")
    print("=" * 60)
    
    # Configuration
    DATA_DIR = "."  # Répertoire contenant les fichiers JSON de caractérisation
    
    # Création analyseur
    analyzer = ParasiticSignalsDriftAnalyzer(data_directory=DATA_DIR)
    
    # Chargement sessions
    n_sessions = analyzer.load_sessions()
    
    if n_sessions < 2:
        print("❌ Besoin d'au moins 2 sessions pour analyser la dérive")
        print("💡 Lancez d'abord plusieurs caractérisations avec EFImagingBench_ParasiticSignals_Characterization.py")
        return
    
    print("\n🔬 ANALYSE DE STABILITÉ...")
    print("-" * 40)
    
    # Génération graphiques
    plot_files = analyzer.generate_drift_plots()
    
    # Export rapport
    report_file = analyzer.export_drift_report()
    
    print(f"\n🎯 ANALYSE TERMINÉE")
    print(f"   Rapport: {report_file}")
    print(f"   Graphiques: {len(plot_files)} fichiers générés")
    print(f"   Sessions analysées: {n_sessions}")


if __name__ == "__main__":
    main() 