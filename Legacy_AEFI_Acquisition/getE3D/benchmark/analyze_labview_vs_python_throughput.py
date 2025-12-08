#!/usr/bin/env python3
"""
Analyse comparative des débits d'acquisition : LabVIEW vs Python
- Analyse des anciennes données LabVIEW par blocs aléatoires
- Estimation du débit d'acquisition réel
- Comparaison avec les résultats Python actuels
"""

import json
import csv
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from datetime import datetime

class LabVIEWThroughputAnalyzer:
    """
    Analyseur de débit d'acquisition pour les données LabVIEW
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.results = {}
        
    def load_json_config(self, json_path: Path) -> Dict:
        """Charge la configuration JSON d'un fichier LabVIEW"""
        with open(json_path, 'r') as f:
            config = json.load(f)
        return config
    
    def extract_averaging(self, config: Dict) -> int:
        """Extrait uniquement la valeur du moyennage"""
        # Chercher dans dds_adc_v2 d'abord
        if 'dds_adc_v2' in config:
            averaging = config['dds_adc_v2'].get('averaging')
            if averaging:
                return averaging
        
        # Chercher dans dds_adc_mux si pas trouvé
        if 'dds_adc_mux' in config:
            averaging = config['dds_adc_mux'].get('averaging')
            if averaging:
                return averaging
        
        # Valeur par défaut
        return 127
    
    def analyze_csv_block(self, csv_path: Path, block_size: int = 100, 
                         num_blocks: int = 10) -> dict:
        """
        Analyse des blocs aléatoires dans un fichier CSV (mode explicite selon dossier)
        """
        print(f"[ANALYSE] Lecture de {csv_path.name}")
        try:
            if 'old_data_for_comparison' in str(csv_path):
                print("[DEBUG] Mode LabVIEW (timestamps en première ligne, analyse sur colonnes)")
                timestamps_row = pd.read_csv(csv_path, header=None, nrows=1)
                total_samples = len(timestamps_row.columns)
                if total_samples < block_size:
                    print(f"[ERREUR] Pas assez de données ({total_samples} < {block_size})")
                    return {'throughput_mean': 0, 'throughput_std': 0, 'valid_blocks': 0}
                # Blocs espacés (début, milieu, fin)
                block_positions = [
                    0,
                    total_samples // 2 - block_size // 2,
                    total_samples - block_size
                ]
                throughputs = []
                for i, start_pos in enumerate(block_positions):
                    end_pos = min(start_pos + block_size, total_samples)
                    df_block = pd.read_csv(csv_path, header=None, usecols=range(start_pos, end_pos))
                    block = df_block.iloc[0].values
                    time_span = block[-1] - block[0]
                    if time_span > 0:
                        throughput = len(block) / time_span
                        throughputs.append(throughput)
                        print(f"[DEBUG] Bloc {i+1}: {len(block)} échantillons, temps {time_span:.3f}s, débit {throughput:.1f} Hz")
                if throughputs:
                    return {
                        'throughput_mean': np.mean(throughputs),
                        'throughput_std': np.std(throughputs),
                        'valid_blocks': len(throughputs)
                    }
                else:
                    return {'throughput_mean': 0, 'throughput_std': 0, 'valid_blocks': 0}
            else:
                print("[DEBUG] Mode Python (timestamp en colonne, analyse sur lignes)")
                df = pd.read_csv(csv_path, comment='#')
                timestamps = df['timestamp'].values
                total_samples = len(timestamps)
                if total_samples < block_size:
                    print(f"[ERREUR] Pas assez de données ({total_samples} < {block_size})")
                    return {'throughput_mean': 0, 'throughput_std': 0, 'valid_blocks': 0}
                throughputs = []
                for i in range(num_blocks):
                    start_idx = np.random.randint(0, total_samples - block_size + 1)
                    block = timestamps[start_idx:start_idx+block_size]
                    time_span = block[-1] - block[0]
                    if time_span > 0:
                        throughput = block_size / time_span
                        throughputs.append(throughput)
                        print(f"[DEBUG] Bloc {i+1}: {block_size} échantillons, temps {time_span:.3f}s, débit {throughput:.1f} Hz")
                if throughputs:
                    return {
                        'throughput_mean': np.mean(throughputs),
                        'throughput_std': np.std(throughputs),
                        'valid_blocks': len(throughputs)
                    }
                else:
                    return {'throughput_mean': 0, 'throughput_std': 0, 'valid_blocks': 0}
        except Exception as e:
            print(f"[ERREUR] Impossible de lire {csv_path}: {e}")
            return {'throughput_mean': 0, 'throughput_std': 0, 'valid_blocks': 0}
    
    def analyze_labview_data(self, block_size: int = 100, num_blocks: int = 10) -> Dict:
        """
        Analyse complète des données LabVIEW et Python
        
        Args:
            block_size: Taille de chaque bloc d'analyse
            num_blocks: Nombre de blocs par fichier
            
        Returns:
            Résultats d'analyse par fichier avec identifiants "moyennage_provenance"
        """
        print(f"[ANALYSE] Début analyse LabVIEW et Python - {block_size} samples/bloc, {num_blocks} blocs/fichier (DEBUG)")
        
        all_results = {}
        
        # 1. ANALYSE DES FICHIERS LABVIEW (old_data_for_comparison)
        print(f"\n[ANALYSE] Analyse des fichiers LabVIEW...")
        labview_dir = self.data_dir / "old_data_for_comparison"
        if labview_dir.exists():
            json_files = list(labview_dir.glob("*.json"))
            
            for json_file in json_files:
                print(f"\n[ANALYSE] Traitement de {json_file.name}")
                
                # Chargement de la configuration
                try:
                    config = self.load_json_config(json_file)
                    averaging = self.extract_averaging(config)
                except Exception as e:
                    print(f"[ERREUR] Impossible de charger {json_file}: {e}")
                    continue
                
                # Recherche du fichier CSV correspondant
                csv_pattern = json_file.stem.replace('.json', '') + '_E_all.csv'
                csv_files = list(labview_dir.glob(f"*{csv_pattern}*"))
                
                if not csv_files:
                    # Recherche alternative
                    csv_files = list(labview_dir.glob(f"*{json_file.stem.split('_')[0]}*_E_all.csv"))
                
                if not csv_files:
                    print(f"[ERREUR] Aucun fichier CSV trouvé pour {json_file.name}")
                    continue
                
                csv_file = csv_files[0]
                
                # Analyse des blocs CSV
                block_results = self.analyze_csv_block(csv_file, block_size, num_blocks)
                
                if block_results and block_results['valid_blocks'] > 0:
                    identifier = f"{averaging}_LabVIEW"
                    file_result = {
                        'moyennage': averaging,
                        'provenance': 'LabVIEW',
                        'csv_file': csv_file.name,
                        'json_file': json_file.name,
                        'stats': {
                            'mean_throughput_hz': block_results['throughput_mean'],
                            'std_throughput_hz': block_results['throughput_std'],
                            'valid_blocks_count': block_results['valid_blocks'],
                            'total_blocks': num_blocks
                        }
                    }
                    
                    all_results[identifier] = file_result
                    
                    print(f"[RESULTAT] {json_file.name}:")
                    print(f"  - Moyennage: {averaging}")
                    print(f"  - Débit moyen: {file_result['stats']['mean_throughput_hz']:.1f} ± {file_result['stats']['std_throughput_hz']:.1f} Hz")
                    print(f"  - Blocs valides: {file_result['stats']['valid_blocks_count']}/{file_result['stats']['total_blocks']}")
        else:
            print(f"[ERREUR] Dossier LabVIEW non trouvé: {labview_dir}")
        
        # 2. ANALYSE DES FICHIERS PYTHON (data)
        print(f"\n[ANALYSE] Analyse des fichiers Python (référence)...")
        python_files = [
            "2025-07-04_132431_benchmark_navg10_vsTime.csv",
            "2025-07-04_132434_benchmark_navg50_vsTime.csv", 
            "2025-07-04_133854_benchmark_navg10_vsTime.csv",
            "2025-07-04_133911_benchmark_navg50_vsTime.csv"
        ]
        
        for csv_filename in python_files:
            csv_path = self.data_dir / csv_filename
            if csv_path.exists():
                print(f"\n[ANALYSE] Traitement de {csv_filename}")
                
                # Extraction du moyennage depuis le nom de fichier
                if "navg10" in csv_filename:
                    averaging = 10
                elif "navg50" in csv_filename:
                    averaging = 50
                else:
                    averaging = 1
                
                # Analyse des blocs CSV
                block_results = self.analyze_csv_block(csv_path, block_size, num_blocks)
                
                if block_results and block_results['valid_blocks'] > 0:
                    identifier = f"{averaging}_Python"
                    file_result = {
                        'moyennage': averaging,
                        'provenance': 'Python',
                        'csv_file': csv_filename,
                        'stats': {
                            'mean_throughput_hz': block_results['throughput_mean'],
                            'std_throughput_hz': block_results['throughput_std'],
                            'valid_blocks_count': block_results['valid_blocks'],
                            'total_blocks': num_blocks
                        }
                    }
                    
                    all_results[identifier] = file_result
                    
                    print(f"[RESULTAT] {csv_filename}:")
                    print(f"  - Source: Python")
                    print(f"  - Moyennage: {averaging}")
                    print(f"  - Débit moyen: {file_result['stats']['mean_throughput_hz']:.1f} ± {file_result['stats']['std_throughput_hz']:.1f} Hz")
                    print(f"  - Blocs valides: {file_result['stats']['valid_blocks_count']}/{file_result['stats']['total_blocks']}")
            else:
                print(f"[ERREUR] Fichier Python non trouvé: {csv_filename}")
        
        return all_results
    
    def compare_with_python_results(self, labview_results: Dict) -> Dict:
        """
        Compare les résultats LabVIEW avec nos résultats Python
        
        Args:
            labview_results: Résultats d'analyse LabVIEW et Python
            
        Returns:
            Comparaison structurée
        """
        # Extraire les résultats Python et LabVIEW des données analysées
        python_results = {}
        labview_only_results = {}
        
        for key, result in labview_results.items():
            if result['provenance'] == 'Python':
                # Résultat Python
                moyennage = result['moyennage']
                python_results[moyennage] = result['stats']['mean_throughput_hz']
            else:
                # Résultat LabVIEW
                labview_only_results[key] = result
        
        comparison = {
            'python_results': python_results,
            'labview_results': {},
            'comparison': {}
        }
        
        for file_key, result in labview_only_results.items():
            moyennage = result['moyennage']
            labview_throughput = result['stats']['mean_throughput_hz']
            comparison['labview_results'][moyennage] = labview_throughput
            
            if moyennage in python_results:
                python_throughput = python_results[moyennage]
                ratio = labview_throughput / python_throughput if python_throughput > 0 else 0
                
                comparison['comparison'][moyennage] = {
                    'labview_hz': labview_throughput,
                    'python_hz': python_throughput,
                    'ratio_labview_python': ratio,
                    'difference_hz': labview_throughput - python_throughput,
                    'file': result.get('json_file', result['csv_file'])
                }
        
        return comparison
    
    def generate_report(self, labview_results: Dict, comparison: Dict) -> str:
        """Génère un rapport de comparaison"""
        report = []
        report.append("=" * 80)
        report.append("RAPPORT DE COMPARAISON : LABVIEW vs PYTHON")
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Résultats Python
        report.append("RÉSULTATS PYTHON (acquisition réelle):")
        report.append("-" * 50)
        for file_key, result in labview_results.items():
            if result['provenance'] == 'Python':
                moyennage = result['moyennage']
                stats = result['stats']
                report.append(f"  {result['csv_file']}:")
                report.append(f"    - Moyennage: {moyennage}")
                report.append(f"    - Débit: {stats['mean_throughput_hz']:.1f} ± {stats['std_throughput_hz']:.1f} Hz")
                report.append(f"    - Blocs valides: {stats['valid_blocks_count']}/{stats['total_blocks']}")
        report.append("")
        
        # Résultats LabVIEW
        report.append("RÉSULTATS LABVIEW (extrapolation par blocs):")
        report.append("-" * 50)
        for file_key, result in labview_results.items():
            if result['provenance'] == 'LabVIEW':
                moyennage = result['moyennage']
                stats = result['stats']
                report.append(f"  {result['json_file']}:")
                report.append(f"    - Moyennage: {moyennage}")
                report.append(f"    - Débit: {stats['mean_throughput_hz']:.1f} ± {stats['std_throughput_hz']:.1f} Hz")
                report.append(f"    - Blocs valides: {stats['valid_blocks_count']}/{stats['total_blocks']}")
        report.append("")
        
        # Comparaison
        report.append("COMPARAISON DIRECTE:")
        report.append("-" * 50)
        all_averagings = set(comparison['labview_results'].keys()) | set(comparison['python_results'].keys())
        for avg in sorted(all_averagings):
            comp = comparison['comparison'].get(avg, None)
            if comp:
                report.append(f"  Moyennage {avg}:")
                report.append(f"    - LabVIEW: {comp['labview_hz']:.1f} Hz")
                report.append(f"    - Python:  {comp['python_hz']:.1f} Hz")
                report.append(f"    - Ratio:   {comp['ratio_labview_python']:.2f}x")
                report.append(f"    - Différence: {comp['difference_hz']:+.1f} Hz")
                report.append(f"    - Fichier: {comp['file']}")
                report.append("")
            else:
                if avg in comparison['labview_results'] and avg not in comparison['python_results']:
                    report.append(f"  Moyennage {avg}: Présent dans LabVIEW, absent dans les fichiers Python.")
                elif avg in comparison['python_results'] and avg not in comparison['labview_results']:
                    report.append(f"  Moyennage {avg}: Présent dans Python, absent dans les fichiers LabVIEW.")
        report.append("")
        
        # Conclusion
        report.append("CONCLUSION:")
        report.append("-" * 50)
        if comparison['comparison']:
            ratios = [comp['ratio_labview_python'] for comp in comparison['comparison'].values()]
            mean_ratio = np.mean(ratios)
            report.append(f"  Ratio moyen LabVIEW/Python: {mean_ratio:.2f}x")
            
            if mean_ratio > 1.5:
                report.append("  → LabVIEW semble plus rapide que Python")
            elif mean_ratio < 0.7:
                report.append("  → Python semble plus rapide que LabVIEW")
            else:
                report.append("  → Performances comparables entre LabVIEW et Python")
        else:
            report.append("  Aucune comparaison possible (moyennages différents)")
        
        return "\n".join(report)
    
    def save_results(self, labview_results: Dict, comparison: Dict, output_dir: str = "results"):
        """Sauvegarde les résultats d'analyse"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Rapport texte
        report = self.generate_report(labview_results, comparison)
        report_file = output_path / f"labview_vs_python_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Données JSON
        data_file = output_path / f"labview_analysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'labview_results': labview_results,
                'comparison': comparison,
                'analysis_timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\n[SAUVEGARDE] Résultats sauvegardés dans {output_path}")
        print(f"  - Rapport: {report_file}")
        print(f"  - Données: {data_file}")
        
        return report_file, data_file


def main():
    """Fonction principale"""
    # Configuration pour debug rapide
    data_dir = "getE3D/benchmark/data/"
    block_size = 10   # Taille des blocs d'analyse (inchangé)
    num_blocks = 30  # Nombre de blocs par fichier (robuste)
    
    print("=" * 80)
    print("ANALYSE COMPARATIVE LABVIEW vs PYTHON")
    print("=" * 80)
    
    # Création de l'analyseur
    analyzer = LabVIEWThroughputAnalyzer(data_dir)
    
    # Analyse des données LabVIEW
    print(f"\n[ANALYSE] Début de l'analyse des données LabVIEW...")
    labview_results = analyzer.analyze_labview_data(block_size, num_blocks)
    
    if not labview_results:
        print("[ERREUR] Aucun résultat d'analyse LabVIEW obtenu")
        return
    
    # Comparaison avec Python
    print(f"\n[COMPARAISON] Comparaison avec les résultats Python...")
    comparison = analyzer.compare_with_python_results(labview_results)
    
    # Génération du rapport
    print(f"\n[RAPPORT] Génération du rapport...")
    report = analyzer.generate_report(labview_results, comparison)
    print(report)
    
    # Sauvegarde
    analyzer.save_results(labview_results, comparison)
    
    print(f"\n[TERMINÉ] Analyse complète terminée")


if __name__ == "__main__":
    main() 