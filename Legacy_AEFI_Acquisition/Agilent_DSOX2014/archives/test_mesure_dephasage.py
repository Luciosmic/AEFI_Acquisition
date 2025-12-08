import time
import numpy as np
from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController

# Paramètres
CH1 = 3  # Canal 3
CH2 = 4  # Canal 4

scope = OscilloscopeDSOX2014AController()
try:
    # Essai SCPI direct (si supporté)
    try:
        phase_deg = float(scope.scope.query(f":MEASure:PHASe? CHANnel{CH1},CHANnel{CH2}"))
        print(f"Déphasage (SCPI) entre CH{CH1} et CH{CH2} : {phase_deg:.2f}°")
    except Exception as e:
        print("Commande SCPI de phase non supportée ou erreur :", e)
        print("On tente le calcul à partir des signaux bruts...")
        # Acquisition brute
        t1, v1 = scope.get_waveform(channel=CH1)
        t2, v2 = scope.get_waveform(channel=CH2)
        # Interpolation sur grille commune si besoin
        if not np.allclose(t1, t2):
            t_common = np.linspace(max(t1[0], t2[0]), min(t1[-1], t2[-1]), min(len(t1), len(t2)))
            v1 = np.interp(t_common, t1, v1)
            v2 = np.interp(t_common, t2, v2)
        else:
            t_common = t1
        # Calcul du déphasage par cross-corrélation
        v1 = v1 - np.mean(v1)
        v2 = v2 - np.mean(v2)
        corr = np.correlate(v1, v2, mode='full')
        lag = np.argmax(corr) - (len(v1) - 1)
        dt = t_common[1] - t_common[0]
        period = abs(1.0 / (np.fft.fftfreq(len(t_common), d=dt)[np.argmax(np.abs(np.fft.fft(v1)[1:]))+1]))
        phase = 360.0 * lag * dt / period
        print(f"Déphasage estimé (cross-corrélation) entre CH{CH1} et CH{CH2} : {phase:.2f}°")
finally:
    scope.close() 