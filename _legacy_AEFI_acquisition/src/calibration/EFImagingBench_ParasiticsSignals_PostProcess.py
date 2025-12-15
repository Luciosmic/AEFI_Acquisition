import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os
from pathlib import Path
import pickle

# Facteur de conversion ADC vers microvolts (gain=1: ±4.0V)
# Pour tests, on garde une conversion 1:1
CONVERSION_FACTOR = 1  # ADC codes vers volts
MICROVOLT_FACTOR = 1  # Volts vers microvolts

def process_parasitic_signals(data_file: str, viz_dir: Path = None, interpolated_dir: Path = None) -> dict:
    """
    Traite les données de caractérisation des signaux parasites et génère les fonctions de compensation.
    
    Args:
        data_file: Chemin vers le fichier JSON de caractérisation
        viz_dir: Dossier pour les visualisations
        interpolated_dir: Dossier pour les fonctions d'interpolation
    
    Returns:
        dict: Fonctions d'interpolation pour chaque canal
    """
    # Charger les données
    with open(data_file, 'r') as f:
        data = json.load(f)

    # Configuration des dossiers de sortie
    if viz_dir is None or interpolated_dir is None:
        # Remonter d'un niveau par rapport au dossier data
        parent_dir = Path(data_file).parent.parent
        if viz_dir is None:
            viz_dir = parent_dir / "visualization"
        if interpolated_dir is None:
            interpolated_dir = parent_dir / "interpolated_calibration_data"
    
    # Création des dossiers si nécessaire
    viz_dir.mkdir(exist_ok=True, parents=True)
    interpolated_dir.mkdir(exist_ok=True, parents=True)

    print(f"[DEBUG] Dossiers de sortie:")
    print(f"  - Visualisations: {viz_dir}")
    print(f"  - Interpolations: {interpolated_dir}")

    # Nom de base pour les fichiers
    base_name = Path(data_file).stem

    # Extraire fréquences et résultats
    frequencies = np.array(data['metadata']['frequencies_hz'])
    results = data['results']

    # Configuration des canaux
    channels_adc1 = ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4']
    channels_adc2 = ['adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4']
    metric = 'mean'

    # Dictionnaire pour stocker les fonctions d'interpolation (en codes ADC)
    interpolation_functions = {}

    def plot_adc(channels, adc_name):
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f'Signaux parasites - {adc_name}', fontsize=14)
        
        for i, channel in enumerate(channels):
            ax = axes[i//2, i%2]
            
            # Extraire les codes ADC bruts
            adc_codes = np.array([r['channels'][channel][metric] for r in results])
            
            # Créer l'interpolation en codes ADC et la stocker
            f_interp = interp1d(frequencies, adc_codes, kind='cubic', bounds_error=False, fill_value='extrapolate')
            interpolation_functions[channel] = f_interp
            
            # Points pour affichage lisse (en microvolts pour visualisation)
            freq_smooth = np.logspace(np.log10(frequencies.min()), np.log10(frequencies.max()), 500)
            codes_smooth = f_interp(freq_smooth)
            
            # Conversion en microvolts UNIQUEMENT pour l'affichage
            values_uv = adc_codes * CONVERSION_FACTOR * MICROVOLT_FACTOR
            values_smooth_uv = codes_smooth * CONVERSION_FACTOR * MICROVOLT_FACTOR
            
            # Tracé double axe : codes ADC et microvolts
            ax1 = ax
            ax2 = ax1.twinx()
            
            # Codes ADC (axe gauche)
            line1 = ax1.semilogx(frequencies, adc_codes, 'o', color='blue', markersize=4, label='Codes ADC')
            ax1.semilogx(freq_smooth, codes_smooth, '-', color='blue', alpha=0.5, label='Interpolation ADC')
            ax1.set_ylabel('Codes ADC', color='blue')
            ax1.tick_params(axis='y', labelcolor='blue')
            
            # Microvolts (axe droit)
            line2 = ax2.semilogx(frequencies, values_uv, 'o', color='red', markersize=4, label='µV')
            ax2.semilogx(freq_smooth, values_smooth_uv, '-', color='red', alpha=0.5, label='Interpolation µV')
            ax2.set_ylabel('Microvolts (µV)', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
            
            ax1.set_xlabel('Fréquence (Hz)')
            ax1.set_title(channel)
            
            # Légende combinée
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper right')
            
            ax1.grid(True)
        
        plt.tight_layout()
        
        # Sauvegarder la figure
        fig_name = f"{base_name}_{adc_name.lower()}_parasitic_signals.png"
        fig_path = viz_dir / fig_name
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f"Figure sauvegardée: {fig_path}")
        
        plt.close()  # Fermer la figure pour libérer la mémoire

    # Tracer et sauvegarder les deux ADCs
    plot_adc(channels_adc1, 'ADC1')
    plot_adc(channels_adc2, 'ADC2')

    # Sauvegarder les fonctions d'interpolation pour compensation live
    compensation_file = interpolated_dir / f"{base_name}_compensation_functions.pkl"
    with open(compensation_file, 'wb') as f:
        pickle.dump(interpolation_functions, f)
    print(f"Fonctions de compensation sauvegardées: {compensation_file}")

    # Sauvegarder aussi dans src/data_processing pour l'AcquisitionManager
    try:
        project_root = Path(__file__).parent.parent.parent # Remonter d'un niveau pour atteindre le dossier racine
        data_processing_dir = project_root / "src" / "data_processing"
        data_processing_dir.mkdir(exist_ok=True, parents=True)
        
        # Nom de fichier standardisé pour l'AcquisitionManager
        manager_compensation_file = data_processing_dir / "noexcitation_parasitic_signals_characterization_compensation_functions.pkl"
        with open(manager_compensation_file, 'wb') as f:
            pickle.dump(interpolation_functions, f)
        print(f"Fonctions de compensation pour AcquisitionManager: {manager_compensation_file}")
    except Exception as e:
        print(f"⚠️ Impossible de sauvegarder dans data_processing: {e}")

    return interpolation_functions

if __name__ == '__main__':
    # Exemple d'utilisation directe du script
    file_name = "2025-07-30_094211_parasitic_signals_characterization.json"
    data_file = Path(__file__).parent / "data" / file_name
    
    # Les dossiers seront créés au même niveau que data
    interpolation_functions = process_parasitic_signals(data_file)  # Utilise les dossiers par défaut
    
    # Afficher exemple d'utilisation
    print("\n=== UTILISATION POUR COMPENSATION LIVE ===")
    print("# Pour charger les fonctions de compensation:")
    print("import pickle")
    print("with open('chemin/vers/compensation_functions.pkl', 'rb') as f:")
    print("    compensation_funcs = pickle.load(f)")
    print()
    print("# Pour compenser une fréquence donnée:")
    print("frequency = 1000.0  # Hz")
    print("for channel in compensation_funcs:")
    print("    # La fonction retourne directement les codes ADC à soustraire")
    print("    parasitic_signal_codes = int(round(compensation_funcs[channel](frequency)))")
    print("    compensated_value = raw_adc_value - parasitic_signal_codes")