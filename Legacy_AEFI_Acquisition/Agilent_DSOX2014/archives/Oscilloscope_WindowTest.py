import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import os
import json
import pandas as pd
import random
from pathlib import Path

# Ajout du chemin pour les modules personnalisés
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'getE3D', 'instruments'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Agilent_DSOX2014'))

from EFImagingBench_DDS_ADC_SerialCommunicationModule import SerialCommunicator
from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController

def set_timebase_for_frequency(scope, freq, n_periods=20):
    period = 1.0 / freq
    total_time = n_periods * period
    sec_per_div = total_time / 10
    sec_per_div = max(sec_per_div, 1e-7)
    scope.scope.write(f":TIMebase:SCALe {sec_per_div}")
    print(f"Fenêtre temporelle réglée : {sec_per_div:.2e} s/div pour {n_periods} périodes à {freq} Hz")

def optimize_vdiv(scope, channel, v, margin=0.9):
    measures = scope.get_measurements(channel)
    Vpp = measures['VPP']
    vdiv = Vpp / (8 * margin) if Vpp else 1.0
    vdiv = max(vdiv, 0.01)  # 10 mV/div minimum
    scope.configure_channel(channel=channel, vdiv=vdiv, offset=0.0, coupling="DC")
    print(f"Échelle verticale réglée : {vdiv:.2f} V/div pour Vpp={Vpp}")
    return vdiv

def robust_optimize_vdiv(scope, channel, vdiv_try=None, margin=0.9, vdiv_min=0.01, vdiv_max=50):
    """
    Optimise l'échelle verticale pour viser ~90% de la dynamique écran, en évitant les valeurs aberrantes.
    Essaie plusieurs vdiv si besoin.
    Retourne : vdiv_opt, Vpp, essais (liste de tuples (vdiv, Vpp))
    """
    if vdiv_try is None:
        vdiv_try = [0.2, 0.5, 1, 2, 5, 10, 20]
    essais = []
    Vpp = None
    vdiv_opt = None

    # 1. Cherche une première valeur non aberrante
    for vdiv in vdiv_try:
        scope.configure_channel(channel=channel, vdiv=vdiv, offset=0.0, coupling="DC")
        time.sleep(0.2)
        measures = scope.get_measurements(channel)
        Vpp = measures.get('VPP', None)
        try:
            vpp_val = float(Vpp)
            if np.isnan(vpp_val) or vpp_val < 1e-3 or vpp_val > 1e3:
                essais.append((vdiv, Vpp))
                continue
        except Exception:
            essais.append((vdiv, Vpp))
            continue
        essais.append((vdiv, Vpp))
        vdiv_opt = vdiv
        break

    if vdiv_opt is None:
        # Aucun Vpp correct trouvé
        return None, None, essais

    # 2. Ajuste pour viser 90% de la dynamique
    target_ratio = 8 * margin  # 8 divisions * 0.9
    vdiv_target = float(Vpp) / target_ratio
    vdiv_target = min(max(vdiv_target, vdiv_min), vdiv_max)
    scope.configure_channel(channel=channel, vdiv=vdiv_target, offset=0.0, coupling="DC")
    time.sleep(0.2)
    measures = scope.get_measurements(channel)
    Vpp_final = measures.get('VPP', None)
    essais.append((vdiv_target, Vpp_final))

    return vdiv_target, Vpp_final, essais

# Plages de test
FREQ_RANGE = (100, 100000)  # Hz
GAIN_RANGE = (0, 7000)
SONDE_RATIO = 10
DDS_CHANNEL = 1
OSC_CHANNEL = 1
N_TESTS = 20

RESULTS_PATH = Path(__file__).parent / 'window_optimization_results.csv'

# Initialisation des instruments
dds = SerialCommunicator()
scope = OscilloscopeDSOX2014AController()

dds.connect(port="COM10")

results = []

for i in range(N_TESTS):
    freq = random.randint(*FREQ_RANGE)
    gain = random.randint(*GAIN_RANGE)
    print(f"\nTest {i+1}/{N_TESTS} : freq = {freq} Hz, gain = {gain}")
    
    # Configuration DDS
    dds.set_dds_frequency(freq)
    dds.set_dds_gain(DDS_CHANNEL, gain)
    time.sleep(0.2)
    
    # Configuration base de temps
    set_timebase_for_frequency(scope, freq)
    
    # Optimisation robuste de la fenêtre
    vdiv_opt, Vpp_final, essais = robust_optimize_vdiv(scope, OSC_CHANNEL)
    
    # Mesures automatiques complémentaires
    measures = scope.get_measurements(OSC_CHANNEL)
    Vrms = measures.get('VRMS', None)
    
    print(f"Test {i+1}/{N_TESTS} : freq={freq} Hz, gain={gain} | vdiv_opt={vdiv_opt} | Vpp={Vpp_final} | essais={essais}")
    
    # Demande à l'utilisateur
    while True:
        user_input = input(f"Test {i+1}/{N_TESTS} : freq = {freq} Hz, gain = {gain} | La fenêtre est-elle bien optimisée ? (o/n) : ").strip().lower()
        if user_input in ["o", "n"]:
            break
        print("Réponse invalide. Tapez 'o' ou 'n'.")
    
    # Stockage du résultat
    results.append({
        'freq': freq,
        'gain': gain,
        'vdiv_opt': vdiv_opt,
        'Vpp': Vpp_final,
        'Vrms': Vrms,
        'essais': str(essais),
        'user_ok': user_input
    })
    # Sauvegarde intermédiaire
    pd.DataFrame(results).to_csv(RESULTS_PATH, index=False)

print(f"\nTous les tests sont terminés. Résultats sauvegardés dans {RESULTS_PATH}")
dds.disconnect()
scope.close() 