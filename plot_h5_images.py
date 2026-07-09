"""
Script minimal pour tracer les 6 images présentes dans le fichier H5.
"""
import h5py
import numpy as np
import matplotlib.pyplot as plt

# Ouvrir le fichier H5
with h5py.File("data_repository/2025-12-17_205835_scan_nuit_cylindre_pla_stepScanResults.h5", 'r') as f:
    # Lire les données du scan
    scan_data = f['scan_data']
    positions = scan_data['positions'][:]
    measurements = scan_data['measurements'][:]
    
    # Extraire les coordonnées uniques
    x_coords = np.unique(positions[:, 0])
    y_coords = np.unique(positions[:, 1])
    
    # Créer les 6 images (une par colonne de measurements)
    images = []
    for i in range(6):
        img = np.full((len(y_coords), len(x_coords)), np.nan)
        for pos, meas in zip(positions, measurements):
            x_idx = np.where(x_coords == pos[0])[0][0]
            y_idx = np.where(y_coords == pos[1])[0][0]
            img[y_idx, x_idx] = meas[i]
        images.append(img)

# Tracer les 6 images
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i in range(6):
    ax = axes[i]
    im = ax.imshow(images[i], aspect='auto', origin='lower', 
                  extent=[x_coords.min(), x_coords.max(), 
                          y_coords.min(), y_coords.max()])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f'Image {i+1}')
    plt.colorbar(im, ax=ax)

plt.tight_layout()
plt.show()
