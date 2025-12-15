import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import numpy as np

# Définir le chemin du fichier rawData (par défaut)
raw_path = Path(__file__).parent / '20240612_120000_rawData_test.csv'

if len(sys.argv) > 1:
    raw_path = Path(sys.argv[1])

prefix = raw_path.stem.replace('rawData', '')
processed_path = raw_path.with_name(raw_path.stem.replace('rawData', 'processedData') + raw_path.suffix)

if processed_path.exists():
    print(f"Fichier processedData trouvé : {processed_path}")
    df = pd.read_csv(processed_path)
else:
    print(f"Fichier processedData non trouvé. Calcul à partir du rawData : {raw_path}")
    df_raw = pd.read_csv(raw_path)
    results = []
    for (freq, gain), group in df_raw.groupby(['frequence', 'gain']):
        t = group['t'].values
        v = group['v'].values
        if len(v) < 2:
            continue
        Vpp = np.max(v) - np.min(v)
        N = len(v)
        window = np.hanning(N)
        v_win = v * window
        dt = t[1] - t[0]
        f = np.fft.rfftfreq(N, d=dt)
        V = np.fft.rfft(v_win)
        coherent_gain = np.sum(window) / N
        V_mag = (2 / (N * coherent_gain)) * np.abs(V)
        peak_idx = np.argmax(V_mag)
        peak_freq = f[peak_idx]
        peak_amp = V_mag[peak_idx]
        n_harmonics = 10
        harmonic_amps = []
        for i in range(2, n_harmonics + 2):
            harmonic_freq = peak_freq * i
            idx = np.argmin(np.abs(f - harmonic_freq))
            harmonic_amps.append(V_mag[idx])
        thd = np.sqrt(np.sum(np.array(harmonic_amps)**2)) / peak_amp if peak_amp > 0 else None
        results.append({
            'frequence': freq,
            'gain': gain,
            'Vpp': Vpp,
            'peak_freq': peak_freq,
            'peak_amp': peak_amp,
            'thd': thd
        })
    df = pd.DataFrame(results)
    df.to_csv(processed_path, index=False)
    print(f"Fichier processedData généré : {processed_path}")

fig_prefix = processed_path.stem

# Heatmap Vpp
try:
    pivot_vpp = df.pivot(index='frequence', columns='gain', values='Vpp')
    plt.figure(figsize=(10,6))
    plt.imshow(pivot_vpp, aspect='auto', origin='lower', cmap='viridis',
               extent=[df['gain'].min(), df['gain'].max(), df['frequence'].min(), df['frequence'].max()])
    plt.colorbar(label='Vpp (V)')
    plt.xlabel('Gain DDS')
    plt.ylabel('Fréquence (Hz)')
    plt.title('Heatmap Vpp (V) en fonction du gain et de la fréquence')
    plt.tight_layout()
    plt.savefig(Path(__file__).parent / f'{fig_prefix}_heatmap_Vpp.png')
    plt.close()
    print(f"Heatmap Vpp sauvegardée sous : {fig_prefix}_heatmap_Vpp.png")
except Exception as e:
    print(f"Impossible de générer la heatmap Vpp : {e}")

# Heatmap THD
if 'thd' in df.columns:
    try:
        pivot_thd = df.pivot(index='frequence', columns='gain', values='thd')
        plt.figure(figsize=(10,6))
        plt.imshow(pivot_thd, aspect='auto', origin='lower', cmap='magma',
                   extent=[df['gain'].min(), df['gain'].max(), df['frequence'].min(), df['frequence'].max()])
        plt.colorbar(label='THD')
        plt.xlabel('Gain DDS')
        plt.ylabel('Fréquence (Hz)')
        plt.title('Heatmap THD en fonction du gain et de la fréquence')
        plt.tight_layout()
        plt.savefig(Path(__file__).parent / f'{fig_prefix}_heatmap_THD.png')
        plt.close()
        print(f"Heatmap THD sauvegardée sous : {fig_prefix}_heatmap_THD.png")
    except Exception as e:
        print(f"Impossible de générer la heatmap THD : {e}")
else:
    print("Colonne 'thd' absente du DataFrame, heatmap THD non générée.")

print('Visualisations synthétiques sauvegardées dans le dossier results.') 