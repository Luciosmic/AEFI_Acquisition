#!/usr/bin/env python3
"""
Analyse du drift des signaux ADC lors de cycles arrêt/redémarrage d'acquisition
- 3 fréquences : 1000, 10000, 50000 Hz
- 10 cycles par fréquence
- Aucune excitation DDS (gain_dds=0)
- Export JSON structuré, dossier data/

MODE 1 : Cycles arrêt/redémarrage (original)
MODE 2 : Changement de fréquence continu sans redémarrage
MODE 3 : Test avec/sans excitation (gain=0 vs gain=5000)
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
target_frequencies = [2000,10000]  # Hz
n_cycles = 20
n_samples_per_cycle = 10  # Nombre d'échantillons à récupérer à chaque cycle
stabilization_delay = 2.0  # s, temps d'attente après démarrage
excitation_gain = 5000  # Gain DDS pour l'excitation


def run_drift_analysis(port="COM10"):
    """
    MODE 1 : Analyse de dérive avec cycles arrêt/redémarrage
    """
    results = []
    manager = AcquisitionManager(port=port)
    
    # === 🔄 DÉSACTIVATION EXPLICITE DES POST-TRAITEMENTS ===
    # Force l'utilisation des données ADC brutes (référentiel capteur)
    manager.toggle_frame_rotation(False)  # Désactive la rotation
    manager.set_display_frame('sensor')   # Force le référentiel capteur
    print("[INFO] Rotation de référentiel désactivée - Données ADC brutes uniquement")
    
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
            # Récupération des échantillons BRUTS (buffer sensor)

            samples = manager.get_latest_samples(n_samples_per_cycle)
            
            # Arrêt
            manager.stop_acquisition()
            # Extraction des valeurs ADC brutes
            samples_list = []
            for s in samples:
                samples_list.append({
                    "timestamp": s.timestamp.isoformat(),
                    "adc1_ch1": s.adc1_ch1,
                    "adc1_ch2": s.adc1_ch2,
                    "adc1_ch3": s.adc1_ch3,
                    "adc1_ch4": s.adc1_ch4,
                    "adc2_ch1": s.adc2_ch1,
                    "adc2_ch2": s.adc2_ch2,
                    "adc2_ch3": s.adc2_ch3,
                    "adc2_ch4": s.adc2_ch4
                })
            freq_results["cycles"].append({
                "cycle": cycle+1,
                "samples": samples_list
            })
            # Nettoyage du buffer pour le cycle suivant
            manager.clear_buffer()
        results.append(freq_results)
    
    # Export et analyse
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _export_and_analyze(results, timestamp, "restart_cycles")


def run_drift_analysis_continuous(port="COM10"):
    """
    MODE 2 : Analyse de dérive avec changement de fréquence continu
    """
    results = []
    manager = AcquisitionManager(port=port)
    
    # === 🔄 DÉSACTIVATION EXPLICITE DES POST-TRAITEMENTS ===
    # Force l'utilisation des données ADC brutes (référentiel capteur)
    manager.toggle_frame_rotation(False)  # Désactive la rotation
    manager.set_display_frame('sensor')   # Force le référentiel capteur
    print("[INFO] Rotation de référentiel désactivée - Données ADC brutes uniquement")
    
    # Configuration initiale sans excitation
    initial_config = {
        'freq_hz': target_frequencies[0],
        'gain_dds': 0,
        'n_avg': 10
    }
    
    # Démarrage unique de l'acquisition
    print(f"[INFO] Démarrage acquisition continue - Fréquence initiale: {target_frequencies[0]} Hz")
    started = manager.start_acquisition('exploration', initial_config)
    if not started:
        print("[ERREUR] Impossible de démarrer l'acquisition")
        return
    
    time.sleep(stabilization_delay)
    
    try:
        for cycle in range(n_cycles):
            print(f"[INFO] Cycle {cycle+1}/{n_cycles}")
            cycle_results = {
                "cycle": cycle+1,
                "frequency_phases": []
            }
            
            # Pour chaque fréquence dans le cycle
            for freq_idx, freq in enumerate(target_frequencies):
                print(f"  [INFO] Changement vers fréquence {freq} Hz")
                
                # Mise à jour de la configuration (fréquence uniquement)
                manager.update_configuration({'freq_hz': freq})
                time.sleep(stabilization_delay)
                
                # Récupération des échantillons BRUTS (buffer sensor)
                samples = manager.get_latest_samples(n_samples_per_cycle)
                
                # Extraction des valeurs ADC brutes
                samples_list = []
                for s in samples:
                    samples_list.append({
                        "timestamp": s.timestamp.isoformat(),
                        "adc1_ch1": s.adc1_ch1,
                        "adc1_ch2": s.adc1_ch2,
                        "adc1_ch3": s.adc1_ch3,
                        "adc1_ch4": s.adc1_ch4,
                        "adc2_ch1": s.adc2_ch1,
                        "adc2_ch2": s.adc2_ch2,
                        "adc2_ch3": s.adc2_ch3,
                        "adc2_ch4": s.adc2_ch4
                    })
                
                cycle_results["frequency_phases"].append({
                    "frequency_hz": freq,
                    "phase_order": freq_idx + 1,
                    "samples": samples_list
                })
            
            results.append(cycle_results)
            
            # Nettoyage du buffer pour le cycle suivant
            manager.clear_buffer()
    
    finally:
        # Arrêt propre de l'acquisition
        manager.stop_acquisition()
    
    # Export et analyse
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _export_and_analyze(results, timestamp, "continuous_frequency_changes")


def run_excitation_impact_analysis(port="COM10"):
    """
    MODE 3 : Analyse de l'impact de l'excitation (gain=0 vs gain=5000)
    """
    results = []
    manager = AcquisitionManager(port=port)
    
    # === 🔄 DÉSACTIVATION EXPLICITE DES POST-TRAITEMENTS ===
    # Force l'utilisation des données ADC brutes (référentiel capteur)
    manager.toggle_frame_rotation(False)  # Désactive la rotation
    manager.set_display_frame('sensor')   # Force le référentiel capteur
    print("[INFO] Rotation de référentiel désactivée - Données ADC brutes uniquement")
    
    for freq in target_frequencies:
        freq_results = {
            "frequency_hz": freq,
            "cycles": []
        }
        
        for cycle in range(n_cycles):
            print(f"[INFO] Fréquence {freq} Hz - Cycle {cycle+1}/{n_cycles}")
            cycle_results = {
                "cycle": cycle+1,
                "phases": []
            }
            
            # === PHASE 1 : Sans excitation (gain=0) ===
            print(f"  [INFO] Phase 1 : Sans excitation (gain=0)")
            config_no_excitation = {
                'freq_hz': freq,
                'gain_dds': 0,
                'n_avg': 10
            }
            
            started = manager.start_acquisition('exploration', config_no_excitation)
            if not started:
                print("[ERREUR] Impossible de démarrer l'acquisition")
                cycle_results["phases"].append({"error": "start_failed"})
                freq_results["cycles"].append(cycle_results)
                continue
            
            time.sleep(stabilization_delay)
            samples_no_excitation = manager.get_latest_samples(n_samples_per_cycle)
            manager.stop_acquisition()
            
            # Extraction des valeurs ADC brutes sans excitation
            samples_list_no_excitation = []
            for s in samples_no_excitation:
                samples_list_no_excitation.append({
                    "timestamp": s.timestamp.isoformat(),
                    "adc1_ch1": s.adc1_ch1,
                    "adc1_ch2": s.adc1_ch2,
                    "adc1_ch3": s.adc1_ch3,
                    "adc1_ch4": s.adc1_ch4,
                    "adc2_ch1": s.adc2_ch1,
                    "adc2_ch2": s.adc2_ch2,
                    "adc2_ch3": s.adc2_ch3,
                    "adc2_ch4": s.adc2_ch4
                })
            
            cycle_results["phases"].append({
                "phase": "no_excitation",
                "gain_dds": 0,
                "samples": samples_list_no_excitation
            })
            
            # Nettoyage du buffer
            manager.clear_buffer()
            time.sleep(0.5)  # Pause entre les phases
            
            # === PHASE 2 : Avec excitation (gain=5000) ===
            print(f"  [INFO] Phase 2 : Avec excitation (gain={excitation_gain})")
            config_with_excitation = {
                'freq_hz': freq,
                'gain_dds': excitation_gain,
                'n_avg': 10
            }
            
            started = manager.start_acquisition('exploration', config_with_excitation)
            if not started:
                print("[ERREUR] Impossible de démarrer l'acquisition avec excitation")
                cycle_results["phases"].append({"error": "start_failed"})
                freq_results["cycles"].append(cycle_results)
                continue
            
            time.sleep(stabilization_delay)
            samples_with_excitation = manager.get_latest_samples(n_samples_per_cycle)
            manager.stop_acquisition()
            
            # Extraction des valeurs ADC brutes avec excitation
            samples_list_with_excitation = []
            for s in samples_with_excitation:
                samples_list_with_excitation.append({
                    "timestamp": s.timestamp.isoformat(),
                    "adc1_ch1": s.adc1_ch1,
                    "adc1_ch2": s.adc1_ch2,
                    "adc1_ch3": s.adc1_ch3,
                    "adc1_ch4": s.adc1_ch4,
                    "adc2_ch1": s.adc2_ch1,
                    "adc2_ch2": s.adc2_ch2,
                    "adc2_ch3": s.adc2_ch3,
                    "adc2_ch4": s.adc2_ch4
                })
            
            cycle_results["phases"].append({
                "phase": "with_excitation",
                "gain_dds": excitation_gain,
                "samples": samples_list_with_excitation
            })
            
            freq_results["cycles"].append(cycle_results)
            
            # Nettoyage du buffer pour le cycle suivant
            manager.clear_buffer()
        
        results.append(freq_results)
    
    # Export et analyse
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _export_and_analyze(results, timestamp, "excitation_impact")


def _export_and_analyze(results, timestamp, mode_suffix):
    """
    Fonction commune d'export et d'analyse pour les deux modes
    """
    # Export JSON
    script_dir = Path(__file__).parent
    output_dir = script_dir / "data"
    output_dir.mkdir(exist_ok=True, parents=True)
    output_file = output_dir / f"{timestamp}_parasitic_signals_drift_analysis_{mode_suffix}.json"
    
    export_data = {
        "metadata": {
            "timestamp": timestamp,
            "mode": mode_suffix,
            "frequencies_hz": target_frequencies,
            "n_cycles": n_cycles,
            "n_samples_per_cycle": n_samples_per_cycle,
            "excitation_gain": excitation_gain if mode_suffix == "excitation_impact" else None
        },
        "results": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    print(f"[EXPORT] Données sauvegardées : {output_file}")

    # === Analyse statistique et plots ===
    import numpy as np
    import matplotlib.pyplot as plt

    # Création du dossier visualization pour les figures
    visualization_dir = script_dir / "visualization"
    visualization_dir.mkdir(exist_ok=True, parents=True)
    print(f"[INFO] Figures exportées dans : {visualization_dir}")

    if mode_suffix == "restart_cycles":
        _analyze_restart_mode(results, timestamp, visualization_dir)
    elif mode_suffix == "continuous_frequency_changes":
        _analyze_continuous_mode(results, timestamp, visualization_dir)
    else:  # excitation_impact
        _analyze_excitation_impact_mode(results, timestamp, visualization_dir)
    
    # Ajout des stats au JSON
    export_data["statistics"] = _compute_statistics(results, mode_suffix)
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    print("[STATS] Statistiques ajoutées à l'export JSON.")


def _analyze_restart_mode(results, timestamp, visualization_dir):
    """
    Analyse spécifique pour le mode arrêt/redémarrage
    """
    import numpy as np
    import matplotlib.pyplot as plt
    
    for freq_result in results:
        freq = freq_result["frequency_hz"]
        cycles = freq_result["cycles"]
        
        # Mise à jour : seulement 6 voies (ignore adc2_ch3 et adc2_ch4)
        channel_names = [
            "adc1_ch1", "adc1_ch2", "adc1_ch3", "adc1_ch4",
            "adc2_ch1", "adc2_ch2"
        ]
        channel_values = {ch: [] for ch in channel_names}
        
        for cycle in cycles:
            samples = cycle.get("samples", [])
            if not samples:
                for ch in channel_names:
                    channel_values[ch].append(np.nan)
                continue
            # Moyenne sur les échantillons du cycle
            for ch in channel_names:
                vals = [s[ch] for s in samples]
                channel_values[ch].append(np.mean(vals))
        
        # Plot avec normalisation
        plt.figure(figsize=(10,6))
        for ch in channel_names:
            values = np.array(channel_values[ch])
            if len(values) > 0 and not np.isnan(values[0]):
                normalized_values = values - values[0]
                plt.plot(range(1, len(normalized_values)+1), normalized_values, marker='o', label=ch)
        
        plt.title(f"Variabilité ADC normalisée vs numéro de cycle (Mode Restart)\nFréquence = {freq} Hz")
        plt.xlabel("Numéro du cycle")
        plt.ylabel("Variation ADC (valeur - valeur_cycle1)")
        plt.legend()
        plt.grid(True)
        plot_name = f"{timestamp}_drift_plot_restart_{freq}Hz.png"
        plot_path = visualization_dir / plot_name
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"[PLOT] Figure sauvegardée : {plot_path}")


def _analyze_continuous_mode(results, timestamp, visualization_dir):
    """
    Analyse spécifique pour le mode changement de fréquence continu
    """
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Analyse par fréquence
    for freq in target_frequencies:
        # Mise à jour : seulement 6 voies (ignore adc2_ch3 et adc2_ch4)
        channel_names = [
            "adc1_ch1", "adc1_ch2", "adc1_ch3", "adc1_ch4",
            "adc2_ch1", "adc2_ch2"
        ]
        channel_values = {ch: [] for ch in channel_names}
        
        # Collecte des valeurs pour cette fréquence sur tous les cycles
        for cycle_result in results:
            for phase in cycle_result["frequency_phases"]:
                if phase["frequency_hz"] == freq:
                    samples = phase.get("samples", [])
                    if not samples:
                        for ch in channel_names:
                            channel_values[ch].append(np.nan)
                        continue
                    # Moyenne sur les échantillons de la phase
                    for ch in channel_names:
                        vals = [s[ch] for s in samples]
                        channel_values[ch].append(np.mean(vals))
                    break  # Une seule phase par fréquence par cycle
        
        # Plot avec normalisation
        plt.figure(figsize=(10,6))
        for ch in channel_names:
            values = np.array(channel_values[ch])
            if len(values) > 0 and not np.isnan(values[0]):
                normalized_values = values - values[0]
                plt.plot(range(1, len(normalized_values)+1), normalized_values, marker='o', label=ch)
        
        plt.title(f"Variabilité ADC normalisée vs numéro de cycle (Mode Continu)\nFréquence = {freq} Hz")
        plt.xlabel("Numéro du cycle")
        plt.ylabel("Variation ADC (valeur - valeur_cycle1)")
        plt.legend()
        plt.grid(True)
        plot_name = f"{timestamp}_drift_plot_continuous_{freq}Hz.png"
        plot_path = visualization_dir / plot_name
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"[PLOT] Figure sauvegardée : {plot_path}")
    
    # Plot comparatif des transitions de fréquence
    _plot_frequency_transitions(results, timestamp, visualization_dir)


def _plot_frequency_transitions(results, timestamp, visualization_dir):
    """
    Plot spécifique pour analyser les transitions entre fréquences
    """
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Analyse des transitions pour quelques cycles représentatifs
    cycles_to_plot = min(5, len(results))  # Premier 5 cycles
    
    plt.figure(figsize=(15, 8))
    
    for cycle_idx in range(cycles_to_plot):
        cycle_result = results[cycle_idx]
        
        # Collecte des données pour ce cycle
        cycle_data = []
        for phase in cycle_result["frequency_phases"]:
            samples = phase.get("samples", [])
            if samples:
                # Mise à jour : moyenne des 6 canaux principaux uniquement (ignore adc2_ch3 et adc2_ch4)
                avg_values = []
                for sample in samples:
                    avg_val = (sample["adc1_ch1"] + sample["adc1_ch2"] + sample["adc1_ch3"] + sample["adc1_ch4"] + sample["adc2_ch1"] + sample["adc2_ch2"]) / 6
                    avg_values.append(avg_val)
                cycle_data.append({
                    "freq": phase["frequency_hz"],
                    "values": avg_values
                })
        
        # Plot pour ce cycle
        if cycle_data:
            for i, data in enumerate(cycle_data):
                x_pos = i + cycle_idx * len(target_frequencies) * 1.2
                plt.plot([x_pos] * len(data["values"]), data["values"], 
                        marker='o', alpha=0.7, label=f'Cycle {cycle_idx+1}' if i == 0 else "")
                plt.text(x_pos, plt.ylim()[1], f'{data["freq"]}Hz', 
                        ha='center', va='bottom', rotation=45, fontsize=8)
    
    plt.title("Transitions de fréquence - Évolution des valeurs ADC moyennes")
    plt.xlabel("Phase de fréquence")
    plt.ylabel("Valeur ADC moyenne (6 canaux principaux)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks([])  # Pas de ticks sur x pour éviter l'encombrement
    
    plot_name = f"{timestamp}_frequency_transitions_analysis.png"
    plot_path = visualization_dir / plot_name
    plt.savefig(plot_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[PLOT] Analyse des transitions sauvegardée : {plot_path}")


def _analyze_excitation_impact_mode(results, timestamp, visualization_dir):
    """
    Analyse spécifique pour le mode impact de l'excitation
    """
    import numpy as np
    import matplotlib.pyplot as plt
    
    # Analyse par fréquence
    for freq_result in results:
        freq = freq_result["frequency_hz"]
        cycles = freq_result["cycles"]
        
        # Mise à jour : seulement 6 voies (ignore adc2_ch3 et adc2_ch4)
        channel_names = [
            "adc1_ch1", "adc1_ch2", "adc1_ch3", "adc1_ch4",
            "adc2_ch1", "adc2_ch2"
        ]
        
        # Collecte des données pour chaque phase
        no_excitation_values = {ch: [] for ch in channel_names}
        with_excitation_values = {ch: [] for ch in channel_names}
        
        for cycle in cycles:
            phases = cycle.get("phases", [])
            if len(phases) >= 2:
                # Phase sans excitation
                no_exc_phase = phases[0]
                if no_exc_phase.get("phase") == "no_excitation":
                    samples = no_exc_phase.get("samples", [])
                    if samples:
                        for ch in channel_names:
                            vals = [s[ch] for s in samples]
                            no_excitation_values[ch].append(np.mean(vals))
                
                # Phase avec excitation
                with_exc_phase = phases[1]
                if with_exc_phase.get("phase") == "with_excitation":
                    samples = with_exc_phase.get("samples", [])
                    if samples:
                        for ch in channel_names:
                            vals = [s[ch] for s in samples]
                            with_excitation_values[ch].append(np.mean(vals))
        
        # === FIGURE 1 : Variabilité absolue avec excitation (normalisée vs cycle 1) ===
        plt.figure(figsize=(12, 8))
        
        for ch in channel_names:
            with_exc_vals = np.array(with_excitation_values[ch])
            
            if len(with_exc_vals) > 0 and not np.isnan(with_exc_vals[0]):
                # Normalisation par rapport à la première valeur avec excitation
                normalized_vals = with_exc_vals - with_exc_vals[0]
                plt.plot(range(1, len(normalized_vals)+1), normalized_vals, 
                        marker='o', label=ch, alpha=0.7)
        
        plt.title(f"Variabilité absolue avec excitation (gain={excitation_gain})\nFréquence = {freq} Hz")
        plt.xlabel("Numéro du cycle")
        plt.ylabel("Variation ADC par rapport au cycle 1 (valeur - valeur_cycle1)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plot_name = f"{timestamp}_excitation_absolute_variation_{freq}Hz.png"
        plot_path = visualization_dir / plot_name
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"[PLOT] Figure variabilité absolue sauvegardée : {plot_path}")
        
        # === FIGURE 2 : Impact relatif (avec_excitation - sans_excitation pour chaque cycle) ===
        plt.figure(figsize=(12, 8))
        
        for ch in channel_names:
            no_exc_vals = np.array(no_excitation_values[ch])
            with_exc_vals = np.array(with_excitation_values[ch])
            
            if len(no_exc_vals) > 0 and len(with_exc_vals) > 0:
                min_len = min(len(no_exc_vals), len(with_exc_vals))
                
                # Différence cycle par cycle : avec_excitation - sans_excitation
                cycle_by_cycle_impact = with_exc_vals[:min_len] - no_exc_vals[:min_len]
                
                # Normalisation par rapport à la première valeur de l'impact
                if not np.isnan(cycle_by_cycle_impact[0]):
                    normalized_impact = cycle_by_cycle_impact - cycle_by_cycle_impact[0]
                    plt.plot(range(1, len(normalized_impact)+1), normalized_impact, 
                            marker='s', label=ch, alpha=0.7)
        
        plt.title(f"Impact relatif de l'excitation (gain={excitation_gain} - gain=0) normalisé\nFréquence = {freq} Hz")
        plt.xlabel("Numéro du cycle")
        plt.ylabel("Variation de l'impact ADC par rapport au cycle 1")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plot_name = f"{timestamp}_excitation_relative_impact_normalized_{freq}Hz.png"
        plot_path = visualization_dir / plot_name
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"[PLOT] Figure impact relatif normalisé sauvegardée : {plot_path}")


def _compute_statistics(results, mode_suffix):
    """
    Calcul des statistiques pour les deux modes
    """
    import numpy as np
    
    stats = {}
    
    if mode_suffix == "restart_cycles":
        # Statistiques par fréquence pour le mode restart
        for freq_result in results:
            freq = freq_result["frequency_hz"]
            cycles = freq_result["cycles"]
            
            # Mise à jour : seulement 6 voies (ignore adc2_ch3 et adc2_ch4)
            channel_names = [
                "adc1_ch1", "adc1_ch2", "adc1_ch3", "adc1_ch4",
                "adc2_ch1", "adc2_ch2"
            ]
            channel_values = {ch: [] for ch in channel_names}
            
            for cycle in cycles:
                samples = cycle.get("samples", [])
                if not samples:
                    for ch in channel_names:
                        channel_values[ch].append(np.nan)
                    continue
                for ch in channel_names:
                    vals = [s[ch] for s in samples]
                    channel_values[ch].append(np.mean(vals))
            
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
    
    elif mode_suffix == "continuous_frequency_changes":
        # Statistiques par fréquence pour le mode continu
        for freq in target_frequencies:
            # Mise à jour : seulement 6 voies (ignore adc2_ch3 et adc2_ch4)
            channel_names = [
                "adc1_ch1", "adc1_ch2", "adc1_ch3", "adc1_ch4",
                "adc2_ch1", "adc2_ch2"
            ]
            channel_values = {ch: [] for ch in channel_names}
            
            for cycle_result in results:
                for phase in cycle_result["frequency_phases"]:
                    if phase["frequency_hz"] == freq:
                        samples = phase.get("samples", [])
                        if not samples:
                            for ch in channel_names:
                                channel_values[ch].append(np.nan)
                            continue
                        for ch in channel_names:
                            vals = [s[ch] for s in samples]
                            channel_values[ch].append(np.mean(vals))
                        break
            
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
    
    else:  # excitation_impact
        # Statistiques pour le mode impact de l'excitation
        for freq_result in results:
            freq = freq_result["frequency_hz"]
            cycles = freq_result["cycles"]
            
            # Mise à jour : seulement 6 voies (ignore adc2_ch3 et adc2_ch4)
            channel_names = [
                "adc1_ch1", "adc1_ch2", "adc1_ch3", "adc1_ch4",
                "adc2_ch1", "adc2_ch2"
            ]
            
            no_excitation_values = {ch: [] for ch in channel_names}
            with_excitation_values = {ch: [] for ch in channel_names}
            
            for cycle in cycles:
                phases = cycle.get("phases", [])
                if len(phases) >= 2:
                    # Phase sans excitation
                    no_exc_phase = phases[0]
                    if no_exc_phase.get("phase") == "no_excitation":
                        samples = no_exc_phase.get("samples", [])
                        if samples:
                            for ch in channel_names:
                                vals = [s[ch] for s in samples]
                                no_excitation_values[ch].append(np.mean(vals))
                    
                    # Phase avec excitation
                    with_exc_phase = phases[1]
                    if with_exc_phase.get("phase") == "with_excitation":
                        samples = with_exc_phase.get("samples", [])
                        if samples:
                            for ch in channel_names:
                                vals = [s[ch] for s in samples]
                                with_excitation_values[ch].append(np.mean(vals))
            
            freq_stats = {
                "no_excitation": {},
                "with_excitation": {},
                "impact_analysis": {}
            }
            
            for ch in channel_names:
                no_exc_vals = np.array(no_excitation_values[ch])
                with_exc_vals = np.array(with_excitation_values[ch])
                
                freq_stats["no_excitation"][ch] = {
                    "mean": float(np.nanmean(no_exc_vals)),
                    "std": float(np.nanstd(no_exc_vals)),
                    "min": float(np.nanmin(no_exc_vals)),
                    "max": float(np.nanmax(no_exc_vals)),
                    "values": no_exc_vals.tolist()
                }
                
                freq_stats["with_excitation"][ch] = {
                    "mean": float(np.nanmean(with_exc_vals)),
                    "std": float(np.nanstd(with_exc_vals)),
                    "min": float(np.nanmin(with_exc_vals)),
                    "max": float(np.nanmax(with_exc_vals)),
                    "values": with_exc_vals.tolist()
                }
                
                # Analyse de l'impact
                if len(no_exc_vals) > 0 and len(with_exc_vals) > 0:
                    min_len = min(len(no_exc_vals), len(with_exc_vals))
                    difference = with_exc_vals[:min_len] - no_exc_vals[:min_len]
                    relative_impact = np.where(no_exc_vals[:min_len] != 0, 
                                             difference / np.abs(no_exc_vals[:min_len]) * 100,
                                             0)
                    
                    freq_stats["impact_analysis"][ch] = {
                        "absolute_impact_mean": float(np.nanmean(difference)),
                        "absolute_impact_std": float(np.nanstd(difference)),
                        "relative_impact_mean": float(np.nanmean(relative_impact)),
                        "relative_impact_std": float(np.nanstd(relative_impact)),
                        "absolute_differences": difference.tolist(),
                        "relative_impacts": relative_impact.tolist()
                    }
            
            stats[freq] = freq_stats
    
    return stats


def main():
    print("=== Analyse de dérive des signaux parasites ===")
    print("Trois modes disponibles :")
    print("1. Mode arrêt/redémarrage (original)")
    print("2. Mode changement de fréquence continu")
    print("3. Mode impact de l'excitation (gain=0 vs gain=5000)")
    
    while True:
        try:
            choice = input("\nChoisissez le mode (1, 2 ou 3) : ").strip()
            if choice == "1":
                print("\n=== Mode 1 : Cycles arrêt/redémarrage ===")
                run_drift_analysis()
                break
            elif choice == "2":
                print("\n=== Mode 2 : Changement de fréquence continu ===")
                run_drift_analysis_continuous()
                break
            elif choice == "3":
                print(f"\n=== Mode 3 : Impact de l'excitation (gain=0 vs gain={excitation_gain}) ===")
                run_excitation_impact_analysis()
                break
            else:
                print("Choix invalide. Veuillez entrer 1, 2 ou 3.")
        except KeyboardInterrupt:
            print("\nInterruption par l'utilisateur.")
            break
        except Exception as e:
            print(f"Erreur : {e}")
            break

if __name__ == '__main__':
    main()
