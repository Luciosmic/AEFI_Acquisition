#!/usr/bin/env python3
"""
Analyse du drift des signaux ADC (canaux 1 et 2 uniquement) lors de cycles arrêt/redémarrage d'acquisition
- 3 fréquences : 1000, 2000, 10000 Hz
- 500 cycles par fréquence
- Aucune excitation DDS (gain_dds=0)
- Export JSON structuré, dossier data/
- Plots normalisés pour canaux 1 et 2 uniquement
"""
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import sys
import os

# === Ajout dynamique des chemins d'import (comme dans la caractérisation) ===
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Remonte à la racine du projet (EFImagingBench_App)
src_dir = project_root / "src"
paths_to_add = [
    str(project_root),
    str(src_dir),
]
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"[DEBUG] Added to PYTHONPATH: {path}")

# Import du manager (chemin relatif comme dans la caractérisation)
from core.AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_acquisition_manager import AcquisitionManager

# Paramètres de l'expérience
target_frequencies = [1000, 2000, 10000]  # Hz
n_cycles = 500
n_samples_per_cycle = 20  # Nombre d'échantillons à récupérer à chaque cycle
stabilization_delay = 1.0  # s, temps d'attente après démarrage


def run_drift_analysis(port="COM10"):
    results = []
    manager = AcquisitionManager(port=port)
    for freq in target_frequencies:
        freq_results = {
            "frequency_hz": freq,
            "cycles": []
        }
        for cycle in range(n_cycles):
            print(f"[INFO] Fréquence {freq} Hz - Cycle {cycle+1}/{n_cycles}")
            # Config sans excitation
            config = {
                'freq_hz': freq,
                'gain_dds': 0,
                'n_avg': 10
            }
            # Démarrage
            started = manager.start_acquisition('exploration', config)
            if not started:
                print("[ERREUR] Impossible de démarrer l'acquisition")
                freq_results["cycles"].append({"error": "start_failed"})
                continue
            time.sleep(stabilization_delay)
            # Récupération des échantillons
            samples = manager.get_latest_samples(n_samples_per_cycle)
            # Arrêt
            manager.stop_acquisition()
            # Extraction des valeurs ADC brutes (canaux 1 et 2 uniquement)
            samples_list = []
            for s in samples:
                samples_list.append({
                    "timestamp": s.timestamp.isoformat(),
                    "adc1_ch1": s.adc1_ch1,
                    "adc1_ch2": s.adc1_ch2
                })
            freq_results["cycles"].append({
                "cycle": cycle+1,
                "samples": samples_list
            })
            # Nettoyage du buffer pour le cycle suivant
            manager.clear_buffer()
        results.append(freq_results)
    # Export JSON
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    script_dir = Path(__file__).parent
    output_dir = script_dir / "data"
    output_dir.mkdir(exist_ok=True, parents=True)
    output_file = output_dir / f"{timestamp}_parasitic_signals_drift_analysis_ch1ch2.json"
    export_data = {
        "metadata": {
            "timestamp": timestamp,
            "frequencies_hz": target_frequencies,
            "n_cycles": n_cycles,
            "n_samples_per_cycle": n_samples_per_cycle,
            "channels": ["adc1_ch1", "adc1_ch2"]
        },
        "results": results
    }
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    print(f"[EXPORT] Données sauvegardées : {output_file}")

    # === Analyse statistique et plots (canaux 1 et 2 uniquement) ===
    import numpy as np
    import matplotlib.pyplot as plt

    stats = {}
    for freq_result in results:
        freq = freq_result["frequency_hz"]
        cycles = freq_result["cycles"]
        # Pour chaque canal, on collecte les valeurs sur tous les cycles
        channel_names = ["adc1_ch1", "adc1_ch2"]  # Canaux 1 et 2 uniquement
        channel_values = {ch: [] for ch in channel_names}
        for cycle in cycles:
            # On prend le premier échantillon de chaque cycle (ou la moyenne si plusieurs)
            samples = cycle.get("samples", [])
            if not samples:
                for ch in channel_names:
                    channel_values[ch].append(np.nan)
                continue
            # Moyenne sur les échantillons du cycle
            for ch in channel_names:
                vals = [s[ch] for s in samples]
                channel_values[ch].append(np.mean(vals))
        # Calcul stats
        freq_stats = {}
        for ch in channel_names:
            vals = np.array(channel_values[ch])
            freq_stats[ch] = {
                "mean": float(np.nanmean(vals)),
                "std": float(np.nanstd(vals)),
                "min": float(np.nanmin(vals)),
                "max": float(np.nanmax(vals)),
                "values": vals.tolist()
            }
        stats[freq] = freq_stats
        # Plot avec normalisation (soustraction de la première valeur)
        plt.figure(figsize=(12,8))
        for ch in channel_names:
            values = np.array(channel_values[ch])
            if len(values) > 0 and not np.isnan(values[0]):
                # Normalisation : soustraction de la première valeur
                normalized_values = values - values[0]
                plt.plot(range(1, len(normalized_values)+1), normalized_values, marker='o', markersize=2, label=ch, alpha=0.7)
        plt.title(f"Variabilité ADC normalisée vs numéro de cycle\nFréquence = {freq} Hz (Canaux 1 et 2)")
        plt.xlabel("Numéro du cycle")
        plt.ylabel("Variation ADC (valeur - valeur_cycle1)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plot_name = f"{timestamp}_drift_plot_ch1ch2_{freq}Hz.png"
        plot_path = output_dir / plot_name
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"[PLOT] Figure sauvegardée : {plot_path}")
    # Ajout des stats au JSON
    export_data["statistics"] = stats
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    print("[STATS] Statistiques ajoutées à l'export JSON.")


def main():
    run_drift_analysis()

if __name__ == '__main__':
    main() 