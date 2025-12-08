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
    while True:
        user_input = input("Entrez un nom pour les fichiers (ou appuyez sur Entrée pour 'Default') : ").strip()
        if not user_input:
            return "Default"
        filename = user_input.replace(" ", "_")
        if re.match(r'^[a-zA-Z0-9_-]+$', filename):
            return filename
        else:
            
            print("Erreur : Le nom ne doit contenir que des lettres, chiffres, tirets (-) et underscores (_)")

# Paramètres de test
# Sweep logarithmique de 10Hz à 1MHz avec 10 points par décade
decades = np.log10(1e6/10)  # Nombre de décades entre 10Hz et 1MHz
points_per_decade = 10
num_points = int(decades * points_per_decade)
FREQUENCES = np.logspace(1, 6, 2)  # De 10^1 Hz à 10^6 Hz
GAINS = np.linspace(1000, 20000, 2, dtype=int)  # xmin, xmax, npoints
SONDE_RATIO = 1
DDS_CHANNEL = 1
OSC_CHANNEL = 1

now = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = Path(os.path.dirname(__file__)) / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

file_suffix = get_valid_filename()

# Demander si une sonde est utilisée et son ratio
while True:
    sonde_input = input("Utilisez-vous une sonde ? (n/o) [n] : ").strip().lower()
    if not sonde_input:  # Si l'utilisateur appuie juste sur Entrée
        SONDE_RATIO = 1
        break
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

csv_raw_path = RESULTS_DIR / f"{now}_rawData_{file_suffix}.csv"
json_param_path = RESULTS_DIR / f"{now}_Parameters_{file_suffix}.json"

all_data = []

def set_timebase_for_frequency(scope, freq, n_periods=20):
    """Configure la base de temps pour voir n_periods périodes"""
    period = 1.0 / freq
    total_time = n_periods * period
    sec_per_div = total_time / 10
    sec_per_div = max(sec_per_div, 1e-7)
    scope.scope.write(f":TIMebase:SCALe {sec_per_div}")
    print(f"Fenêtre temporelle réglée : {sec_per_div:.2e} s/div pour {n_periods} périodes à {freq} Hz")

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

success, msg = dds.connect(port="COM10")
if not success:
    raise Exception(f"Erreur connexion DDS: {msg}")

for freq in FREQUENCES:
    print(f"\n=== Caractérisation à {freq} Hz ===")
    dds.set_dds_frequency(freq)
    set_timebase_for_frequency(scope, freq)
    for gain in GAINS:
        print(f"--- Test avec gain = {gain} ---")
        success, msg = dds.set_dds_gain(DDS_CHANNEL, gain)
        if not success:
            print(f"Erreur configuration gain DDS: {msg}")
            continue
        time.sleep(0.2)
        
        # Configuration de l'oscilloscope
        print(f"\nConfiguration pour f={freq}Hz, gain={gain}")
        set_timebase_for_frequency(scope, freq)
        vdiv_max = 5 * SONDE_RATIO
        scope.configure_channel(channel=1, vdiv=vdiv_max, offset=0.0, coupling="AC", sonde_ratio=SONDE_RATIO)
        print("Optimisation de la fenêtre verticale...")
        vdiv_opt, Vpp, essais = scope.optimize_vdiv(channel=1, vdiv_init=vdiv_max, sonde_ratio=SONDE_RATIO)
        if vdiv_opt is None:
            print(f"⚠️ Impossible d'optimiser la fenêtre verticale pour f={freq}Hz, gain={gain}")
            continue
        print(f"Fenêtre optimisée : {vdiv_opt}V/div (Vpp={Vpp}V)")
        

        # Configuration de l'acquisition
        scope.configure_acquisition(average_count=64)
        
        time.sleep(0.2)
        t, v = scope.get_waveform(channel=1)
        v = v * SONDE_RATIO


        for ti, vi in zip(t, v):
            all_data.append({
                'frequence': freq,
                'gain': gain,
                't': ti,
                'v': vi
            })

# Vérification qu'on a des données avant de sauvegarder
if len(all_data) == 0:
    print("Aucune donnée n'a été acquise. Vérifiez la connexion avec l'oscilloscope.")
    dds.disconnect()
    scope.close()
    sys.exit(1)

# Sauvegarde des données brutes
pd.DataFrame(all_data).to_csv(csv_raw_path, index=False)

# Sauvegarde des paramètres de configuration uniquement
parameters = {
    'frequences': FREQUENCES,
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

dds.disconnect()
scope.close()
print("\nFin du script.")

# Appel automatique du script de post-process/visualisation
visualisation_script = str((RESULTS_DIR / 'visualisation_EFImagingBenh_DDSAmplification_CaracterisationFreqGain.py').resolve())
try:
    subprocess.run([sys.executable, visualisation_script, str(csv_raw_path)], check=True)
except Exception as e:
    print(f"Erreur lors de l'appel du script de post-process/visualisation : {e}") 