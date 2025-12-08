import numpy as np
import time
import sys
import os
import pandas as pd
import random
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'getE3D', 'instruments'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Agilent_DSOX2014'))

from EFImagingBench_DDS_ADC_SerialCommunicationModule import SerialCommunicator
from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController

def is_aberrant(val):
    try:
        v = float(val)
        return (np.isnan(v) or abs(v) > 1e3 or v > 1e6)
    except:
        return True

def set_timebase_for_frequency(scope, freq, n_periods=20):
    period = 1.0 / freq
    total_time = n_periods * period
    sec_per_div = total_time / 10
    sec_per_div = max(sec_per_div, 1e-7)
    scope.scope.write(f":TIMebase:SCALe {sec_per_div}")
    print(f"Fenêtre temporelle réglée : {sec_per_div:.2e} s/div pour {n_periods} périodes à {freq} Hz")

# Plages problématiques
FREQ_RANGE = (50000, 100000)  # Hz
GAIN_RANGE = (50, 1500)
SONDE_RATIO = 10
DDS_CHANNEL = 1
OSC_CHANNEL = 1
N_TESTS = 30

VDIV_TRY = [0.2, 0.5, 1, 2, 5]  # V/div à tester si aberrant

RESULTS_PATH = Path(__file__).parent / 'window_optimization_results_robust.csv'

dds = SerialCommunicator()
scope = OscilloscopeDSOX2014AController()

dds.connect(port="COM10")

results = []

for i in range(N_TESTS):
    freq = random.randint(*FREQ_RANGE)
    gain = random.randint(*GAIN_RANGE)
    print(f"\nTest {i+1}/{N_TESTS} : freq = {freq} Hz, gain = {gain}")
    
    dds.set_dds_frequency(freq)
    dds.set_dds_gain(DDS_CHANNEL, gain)
    time.sleep(0.2)
    set_timebase_for_frequency(scope, freq)
    
    # Première tentative : optimisation automatique
    vdiv_auto = 0.2
    scope.configure_channel(channel=OSC_CHANNEL, vdiv=vdiv_auto, offset=0.0, coupling="DC")
    scope.configure_acquisition(average_count=64)
    scope.configure_trigger(source="CHAN1", level=0.0, slope="POS")
    time.sleep(0.2)
    measures = scope.get_measurements(OSC_CHANNEL)
    Vpp = measures.get('VPP', None)
    Vrms = measures.get('VRMS', None)
    vdiv_used = vdiv_auto
    auto_aberrant = is_aberrant(Vpp) or is_aberrant(Vrms)
    tried_vdivs = [vdiv_auto]
    
    # Si aberrant, essaie d'autres vdiv
    if auto_aberrant:
        for vdiv in VDIV_TRY:
            scope.configure_channel(channel=OSC_CHANNEL, vdiv=vdiv, offset=0.0, coupling="DC")
            time.sleep(0.2)
            measures = scope.get_measurements(OSC_CHANNEL)
            Vpp = measures.get('VPP', None)
            Vrms = measures.get('VRMS', None)
            tried_vdivs.append(vdiv)
            if not (is_aberrant(Vpp) or is_aberrant(Vrms)):
                vdiv_used = vdiv
                break
    
    # Demande à l'utilisateur
    while True:
        user_input = input(f"Test {i+1}/{N_TESTS} : freq = {freq} Hz, gain = {gain}, vdiv={vdiv_used} | Vpp={Vpp}, Vrms={Vrms} | La fenêtre est-elle bien optimisée ? (o/n) : ").strip().lower()
        if user_input in ["o", "n"]:
            break
        print("Réponse invalide. Tapez 'o' ou 'n'.")
    
    results.append({
        'freq': freq,
        'gain': gain,
        'vdiv_used': vdiv_used,
        'Vpp': Vpp,
        'Vrms': Vrms,
        'auto_aberrant': auto_aberrant,
        'tried_vdivs': str(tried_vdivs),
        'user_ok': user_input
    })
    pd.DataFrame(results).to_csv(RESULTS_PATH, index=False)

print(f"\nTous les tests sont terminés. Résultats sauvegardés dans {RESULTS_PATH}")
dds.disconnect()
scope.close() 