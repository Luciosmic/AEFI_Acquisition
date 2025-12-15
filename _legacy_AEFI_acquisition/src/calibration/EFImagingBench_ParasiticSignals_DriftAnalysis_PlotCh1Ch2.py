#!/usr/bin/env python3
"""
Script de post-processing pour afficher les plots de drift analysis (canaux 1 et 2 uniquement)
Lit un fichier JSON existant et génère les plots normalisés
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

def plot_drift_analysis_ch1ch2(json_file_path):
    """
    Lit un fichier JSON de drift analysis et génère les plots pour canaux 1 et 2
    
    Args:
        json_file_path: Chemin vers le fichier JSON de drift analysis
    """
    # Lecture du fichier JSON
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Extraction des métadonnées
    metadata = data.get('metadata', {})
    results = data.get('results', [])
    
    print(f"[INFO] Analyse de drift - {len(results)} fréquences")
    print(f"[INFO] Métadonnées: {metadata}")
    
    # Configuration des canaux à analyser
    channel_names = ["adc1_ch1", "adc1_ch2"]
    
    # Création du dossier de sortie pour les plots
    json_path = Path(json_file_path)
    output_dir = json_path.parent / "plots_ch1ch2"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Timestamp pour les noms de fichiers
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    # Analyse pour chaque fréquence
    for freq_result in results:
        freq = freq_result.get("frequency_hz", "unknown")
        cycles = freq_result.get("cycles", [])
        
        print(f"[INFO] Traitement fréquence {freq} Hz - {len(cycles)} cycles")
        
        # Collecte des valeurs pour chaque canal
        channel_values = {ch: [] for ch in channel_names}
        
        for cycle in cycles:
            samples = cycle.get("samples", [])
            if not samples:
                # Si pas d'échantillons, ajouter NaN
                for ch in channel_names:
                    channel_values[ch].append(np.nan)
                continue
            
            # Moyenne sur les échantillons du cycle pour chaque canal
            for ch in channel_names:
                if ch in samples[0]:  # Vérifier que le canal existe
                    vals = [s[ch] for s in samples if ch in s]
                    if vals:
                        channel_values[ch].append(np.mean(vals))
                    else:
                        channel_values[ch].append(np.nan)
                else:
                    channel_values[ch].append(np.nan)
        
        # Calcul des statistiques
        stats = {}
        for ch in channel_names:
            vals = np.array(channel_values[ch])
            valid_vals = vals[~np.isnan(vals)]
            if len(valid_vals) > 0:
                stats[ch] = {
                    "mean": float(np.mean(valid_vals)),
                    "std": float(np.std(valid_vals)),
                    "min": float(np.min(valid_vals)),
                    "max": float(np.max(valid_vals)),
                    "n_valid_cycles": len(valid_vals)
                }
            else:
                stats[ch] = {"error": "Aucune donnée valide"}
        
        # Affichage des statistiques
        print(f"\n[STATS] Fréquence {freq} Hz:")
        for ch, stat in stats.items():
            if "error" not in stat:
                print(f"  {ch}: mean={stat['mean']:.1f}, std={stat['std']:.1f}, min={stat['min']:.1f}, max={stat['max']:.1f}")
            else:
                print(f"  {ch}: {stat['error']}")
        
        # Génération du plot normalisé
        plt.figure(figsize=(12, 8))
        
        for ch in channel_names:
            values = np.array(channel_values[ch])
            valid_mask = ~np.isnan(values)
            
            if np.sum(valid_mask) > 1:  # Au moins 2 points valides
                valid_values = values[valid_mask]
                valid_cycles = np.arange(1, len(values) + 1)[valid_mask]
                
                # Normalisation : soustraction de la première valeur valide
                normalized_values = valid_values - valid_values[0]
                
                plt.plot(valid_cycles, normalized_values, marker='o', markersize=2, 
                        label=f"{ch} (std={stats[ch]['std']:.1f})", alpha=0.7)
        
        plt.title(f"Variabilité ADC normalisée vs numéro de cycle\nFréquence = {freq} Hz (Canaux 1 et 2)")
        plt.xlabel("Numéro du cycle")
        plt.ylabel("Variation ADC (valeur - valeur_cycle1)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Sauvegarde du plot
        plot_name = f"{timestamp}_drift_plot_ch1ch2_{freq}Hz.png"
        plot_path = output_dir / plot_name
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        
        print(f"[PLOT] Figure sauvegardée: {plot_path}")
    
    print(f"\n[FIN] Analyse terminée. Plots sauvegardés dans: {output_dir}")


def main():
    """Point d'entrée principal"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python EFImagingBench_ParasiticSignals_DriftAnalysis_PlotCh1Ch2.py <fichier_json>")
        print("Exemple: python EFImagingBench_ParasiticSignals_DriftAnalysis_PlotCh1Ch2.py data/2025-01-XX_XXXXXX_parasitic_signals_drift_analysis.json")
        return
    
    json_file = sys.argv[1]
    json_file = r"C:\Users\manip\Dropbox\Luis\1 PROJETS\1 - THESE\Ressources\ExperimentalData_ASSOCE\Dev\EFImagingBench_App\src\calibration\data\2025-07-30_120943_parasitic_signals_drift_analysis.json"
    
    if not Path(json_file).exists():
        print(f"[ERREUR] Fichier non trouvé: {json_file}")
        return
    
    plot_drift_analysis_ch1ch2(json_file)


if __name__ == '__main__':
    main() 