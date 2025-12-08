import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import numpy as np

# Définir le chemin du fichier rawData (par défaut)
raw_path = Path(__file__).parent / '20250612_112928_rawData_DDSOnly.csv'

# Permettre de passer un chemin de fichier en argument
if len(sys.argv) > 1:
    raw_path = Path(sys.argv[1])

# Déduire le nom du fichier processedData
prefix = raw_path.stem.replace('rawData', '')
processed_path = raw_path.with_name(raw_path.stem.replace('rawData', 'processedData') + raw_path.suffix)

# Définir le préfixe pour les figures exportées
if processed_path.exists():
    fig_prefix = processed_path.stem
else:
    fig_prefix = raw_path.stem

if processed_path.exists():
    print(f"Fichier processedData trouvé : {processed_path}")
    df = pd.read_csv(processed_path)
else:
    print(f"Fichier processedData non trouvé. Calcul à partir du rawData : {raw_path}")
    df_raw = pd.read_csv(raw_path)
    # On suppose que le rawData contient : gain, t, v
    # On calcule les données dérivées pour chaque gain
    results = []
    for gain, group in df_raw.groupby('gain'):
        t = group['t'].values
        v = group['v'].values
        if len(v) < 2:
            continue
        Vpp = np.max(v) - np.min(v)
        # FFT et analyse
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
            'gain': gain,
            'Vpp': Vpp,
            'peak_freq': peak_freq,
            'peak_amp': peak_amp,
            'thd': thd
        })
    df = pd.DataFrame(results)
    df.to_csv(processed_path, index=False)
    print(f"Fichier processedData généré : {processed_path}")

# --- Visualisation à partir du processedData ---
colonnes_requises = ['gain', 'thd', 'Vpp', 'peak_amp', 'peak_freq']
df = df.dropna(subset=colonnes_requises)
for col in colonnes_requises:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=colonnes_requises)

# THD en fonction du gain
plt.figure(figsize=(8,5))
plt.plot(df['gain'], df['thd'], marker='o')
plt.xlabel('Gain DDS')
plt.ylabel('THD')
plt.title('THD en fonction du gain DDS')
plt.grid(True)
plt.tight_layout()
plt.savefig(Path(__file__).parent / f'{fig_prefix}_thd_vs_gain.png')
plt.show()

# Vpp en fonction du gain
plt.figure(figsize=(8,5))
plt.plot(df['gain'], df['Vpp'], marker='o', color='orange')
plt.xlabel('Gain DDS')
plt.ylabel('Vpp (V)')
plt.title('Vpp en fonction du gain DDS')
plt.grid(True)
plt.tight_layout()
plt.savefig(Path(__file__).parent / f'{fig_prefix}_vpp_vs_gain.png')
plt.show()

# Amplitude fondamentale en fonction du gain
plt.figure(figsize=(8,5))
plt.plot(df['gain'], df['peak_amp'], marker='o', color='green')
plt.xlabel('Gain DDS')
plt.ylabel('Amplitude fondamentale (V)')
plt.title('Amplitude fondamentale en fonction du gain DDS')
plt.grid(True)
plt.tight_layout()
plt.savefig(Path(__file__).parent / f'{fig_prefix}_peakamp_vs_gain.png')
plt.show()

# Fréquence fondamentale en fonction du gain (filtrage des outliers et optimisation de la fenêtre)
freq = df['peak_freq']
Q1 = freq.quantile(0.25)
Q3 = freq.quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
mask = (freq >= lower) & (freq <= upper)
n_removed = (~mask).sum()
removed_indices = df.index[~mask].tolist()
removed_values = df.loc[~mask, 'peak_freq'].tolist()
if n_removed > 0:
    print(f"Points aberrants retirés pour la fréquence fondamentale : {n_removed}")
    print("Indices retirés :", removed_indices)
    print("Valeurs retirées :", removed_values)
    if n_removed > 0.1 * len(df):
        print("[ALERTE] Plus de 10% des points ont été retirés comme outliers !")
    # Sauvegarde du CSV nettoyé
    cleaned_path = processed_path.with_name(processed_path.stem + '_cleaned.csv')
    df[mask].to_csv(cleaned_path, index=False)
    print(f"Fichier nettoyé sauvegardé sous : {cleaned_path}")
else:
    print("Aucun point aberrant retiré pour la fréquence fondamentale.")
df_filtered = df[mask]
# Optimisation de la fenêtre : variation = 90% de l'axe Y, marge minimale
fmin = df_filtered['peak_freq'].min()
fmax = df_filtered['peak_freq'].max()
fspan = fmax - fmin
min_margin = 5  # Hz, marge minimale absolue
if fspan == 0:
    ylim = (fmin - min_margin, fmax + min_margin)
else:
    margin = max(fspan / 0.9 * 0.05, min_margin)
    ylim = (fmin - margin, fmax + margin)
plt.figure(figsize=(8,5))
plt.plot(df_filtered['gain'], df_filtered['peak_freq'], marker='o', color='purple')
plt.xlabel('Gain DDS')
plt.ylabel('Fréquence fondamentale (Hz)')
plt.title('Fréquence fondamentale en fonction du gain DDS')
plt.ylim(ylim)
plt.grid(True)
plt.tight_layout()
plt.savefig(Path(__file__).parent / f'{fig_prefix}_freq_vs_gain.png')
plt.show()

print('Visualisations sauvegardées dans le dossier results.') 