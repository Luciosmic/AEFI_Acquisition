import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
import subprocess

# Ajout du chemin pour les modules personnalisés
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'getE3D', 'instruments'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Agilent_DSOX2014'))

from EFImagingBench_DDS_ADC_SerialCommunicationModule import SerialCommunicator
from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController

def get_valid_filename():
    """Demande à l'utilisateur un nom de fichier valide."""
    while True:
        user_input = input("Entrez un nom pour les fichiers (ou appuyez sur Entrée pour 'Default') : ").strip()
        if not user_input:
            return "Default"
        
        # Remplacer les espaces par des underscores
        filename = user_input.replace(" ", "_")
        
        # Vérifier si le nom contient uniquement des caractères autorisés
        if re.match(r'^[a-zA-Z0-9_-]+$', filename):
            return filename
        else:
            print("Erreur : Le nom ne doit contenir que des lettres, chiffres, tirets (-) et underscores (_)")

# Paramètres de test
FREQUENCE = 1000  # 10 kHz
GAINS = np.linspace(5000, 10000, 2, dtype=int)  # xmin, xmax, npoints
SONDE_RATIO = 1  # Sonde x1, donné par l'utilisateur
DDS_CHANNEL = 1  # Canal DDS à utiliser
OSC_CHANNEL = 1  # Canal oscilloscope à utiliser

now = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = Path(os.path.dirname(__file__)) / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

# Demander le nom de fichier à l'utilisateur
file_suffix = get_valid_filename()

# Demander si une sonde est utilisée et son ratio
while True:
    sonde_input = input("Utilisez-vous une sonde ? (o/n) : ").strip().lower()
    if sonde_input in ['o', 'oui', 'y', 'yes']:
        while True:
            ratio_input = input("Entrez le ratio de la sonde (ex: 1, 10, 100) : ").strip()
            try:
                SONDE_RATIO = float(ratio_input)
                if SONDE_RATIO > 0:
                    break
                else:
                    print("Le ratio doit être un nombre positif.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
        break
    elif sonde_input in ['n', 'non', 'no']:
        SONDE_RATIO = 1
        break
    else:
        print("Répondez par 'o' (oui) ou 'n' (non).")

# Demander si on veut générer les graphiques temporels et spectres pour chaque gain
while True:
    gen_details = input("Générer les spectres FFT pour chaque gain dans un sous-dossier 'spectrums' ? (o/n) : ").strip().lower()
    if gen_details in ['o', 'oui', 'y', 'yes']:
        GENERATE_DETAIL_PLOTS = True
        break
    elif gen_details in ['n', 'non', 'no', '']:
        GENERATE_DETAIL_PLOTS = False
        break
    else:
        print("Répondez par 'o' (oui) ou 'n' (non).")

# Définir les chemins de fichiers
csv_raw_path = RESULTS_DIR / f"{now}_rawData_{file_suffix}.csv"
csv_processed_path = RESULTS_DIR / f"{now}_processedData_{file_suffix}.csv"
json_param_path = RESULTS_DIR / f"{now}_Parameters_{file_suffix}.json"

all_data = []
all_analysis = []

def set_timebase_for_frequency(scope, freq, n_periods=20):
    """Configure la base de temps pour voir n_periods périodes"""
    period = 1.0 / freq
    total_time = n_periods * period
    sec_per_div = total_time / 10
    sec_per_div = max(sec_per_div, 1e-7)
    scope.scope.write(f":TIMebase:SCALe {sec_per_div}")
    print(f"Fenêtre temporelle réglée : {sec_per_div:.2e} s/div pour {n_periods} périodes à {freq} Hz")

def compute_fft(t, v):
    N = len(v)
    window = np.hanning(N)
    v_win = v * window
    dt = t[1] - t[0]
    fs = 1/dt
    f = np.fft.rfftfreq(N, d=dt)
    V = np.fft.rfft(v_win)
    amplitude_correction = 2 / np.sum(window) * N
    V_mag = np.abs(V) * amplitude_correction
    return f, V_mag, fs

def plot_time_domain(t, v, freq, gain, save_dir, date_str, suffix):
    plt.figure(figsize=(10, 5))
    plt.plot(t*1e3, v)
    plt.title(f"Signal temporel - Freq: {freq} Hz, Gain: {gain}")
    plt.xlabel("Temps (ms)")
    plt.ylabel("Tension (V)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_dir / f"{date_str}_signal_temporel_freq{freq}_gain{gain}_{suffix}.png")
    plt.close()

def plot_fft(f, V_mag, freq, gain, save_dir, date_str, suffix):
    plt.figure(figsize=(10, 5))
    plt.semilogx(f, 20*np.log10(V_mag+1e-12))
    plt.title(f"Spectre - Freq: {freq} Hz, Gain: {gain}")
    plt.xlabel("Fréquence (Hz)")
    plt.ylabel("Amplitude (dBV)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_dir / f"{date_str}_spectre_freq{freq}_gain{gain}_{suffix}.png")
    plt.close()

def plot_analysis_results(df, save_dir, date_str, suffix):
    """Génère les graphiques d'analyse à partir des données."""
    # THD en fonction du gain
    plt.figure(figsize=(8,5))
    plt.plot(df['gain'], df['thd'], marker='o')
    plt.xlabel('Gain DDS')
    plt.ylabel('THD')
    plt.title('THD en fonction du gain DDS')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_dir / f"{date_str}_thd_vs_gain_{suffix}.png")
    plt.close()

    # Vpp en fonction du gain
    plt.figure(figsize=(8,5))
    plt.plot(df['gain'], df['Vpp'], marker='o', color='orange')
    plt.xlabel('Gain DDS')
    plt.ylabel('Vpp (V)')
    plt.title('Vpp en fonction du gain DDS')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_dir / f"{date_str}_vpp_vs_gain_{suffix}.png")
    plt.close()

    # Amplitude fondamentale en fonction du gain
    plt.figure(figsize=(8,5))
    plt.plot(df['gain'], df['peak_amp'], marker='o', color='green')
    plt.xlabel('Gain DDS')
    plt.ylabel('Amplitude fondamentale (V)')
    plt.title('Amplitude fondamentale en fonction du gain DDS')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_dir / f"{date_str}_peakamp_vs_gain_{suffix}.png")
    plt.close()

    # Fréquence fondamentale en fonction du gain (filtrage des outliers)
    freq = df['peak_freq']
    Q1 = freq.quantile(0.25)
    Q3 = freq.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    mask = (freq >= lower) & (freq <= upper)
    n_removed = (~mask).sum()
    df_filtered = df[mask]
    print(f"Points aberrants retirés pour la fréquence fondamentale : {n_removed}")
    # Optimisation de la fenêtre : variation = 90% de l'axe Y
    fmin = df_filtered['peak_freq'].min()
    fmax = df_filtered['peak_freq'].max()
    fcenter = (fmin + fmax) / 2
    fspan = fmax - fmin
    if fspan == 0:
        ylim = (fmin - 0.05*fmin, fmax + 0.05*fmax)
    else:
        margin = fspan / 0.9 * 0.05
        ylim = (fmin - margin, fmax + margin)
    plt.figure(figsize=(8,5))
    plt.plot(df_filtered['gain'], df_filtered['peak_freq'], marker='o', color='purple')
    plt.xlabel('Gain DDS')
    plt.ylabel('Fréquence fondamentale (Hz)')
    plt.title('Fréquence fondamentale en fonction du gain DDS')
    plt.ylim(ylim)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_dir / f"{date_str}_freq_vs_gain_{suffix}.png")
    plt.close()

    print('Graphiques d\'analyse sauvegardés dans le dossier results.')

def to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(v) for v in obj]
    return obj

# Initialisation des instruments
dds = SerialCommunicator()
scope = OscilloscopeDSOX2014AController()

# Connexion DDS
success, msg = dds.connect(port="COM10")
if not success:
    raise Exception(f"Erreur connexion DDS: {msg}")

# Configuration de la fréquence
dds.set_dds_frequency(FREQUENCE)

# Configuration de la base de temps
set_timebase_for_frequency(scope, FREQUENCE)

# Créer le sous-dossier spectrums si besoin
SPECTRUMS_DIR = RESULTS_DIR / 'spectrums'
if GENERATE_DETAIL_PLOTS:
    SPECTRUMS_DIR.mkdir(exist_ok=True)

for gain in GAINS:
    print(f"\n--- Test avec gain = {gain} ---")
    success, msg = dds.set_dds_gain(DDS_CHANNEL, gain)
    if not success:
        print(f"Erreur configuration gain DDS: {msg}")
        continue
    time.sleep(0.2)
    vdiv_opt, Vpp, essais = scope.optimize_vdiv(channel=OSC_CHANNEL, vdiv_max=5*SONDE_RATIO, coupling="AC", sonde_ratio=SONDE_RATIO)
    print(f"vdiv optimisé : {vdiv_opt}, Vpp : {Vpp}, essais : {essais}")
    scope.configure_acquisition(average_count=64)
    time.sleep(0.2)
    t, v = scope.get_waveform(channel=OSC_CHANNEL)
    v = v * SONDE_RATIO
    # Ajout des données brutes
    for ti, vi in zip(t, v):
        all_data.append({
            'gain': gain,
            't': ti,
            'v': vi
        })

# Sauvegarde des données brutes
pd.DataFrame(all_data).to_csv(csv_raw_path, index=False)

# Sauvegarde des paramètres de configuration uniquement
parameters = {
    'frequence': FREQUENCE,
    'gains': GAINS.tolist() if hasattr(GAINS, 'tolist') else GAINS,
    'sonde_ratio': SONDE_RATIO,
    'dds_channel': DDS_CHANNEL,
    'osc_channel': OSC_CHANNEL,
    'date_acquisition': now
}
with open(json_param_path, 'w') as fjson:
    json.dump(to_serializable(parameters), fjson, indent=2)

print(f"Données brutes sauvegardées dans {csv_raw_path}")
print(f"Paramètres de configuration sauvegardés dans {json_param_path}")

# Fermeture des instruments
dds.disconnect()
scope.close()
print("\nFin du script.")

# Appel automatique du script de post-process/visualisation
visualisation_script = str((RESULTS_DIR / 'visualisation_EFImagingBenh_DDSAmplification_CaracterisationGain.py').resolve())
try:
    subprocess.run([sys.executable, visualisation_script, str(csv_raw_path)], check=True)
except Exception as e:
    print(f"Erreur lors de l'appel du script de post-process/visualisation : {e}")
