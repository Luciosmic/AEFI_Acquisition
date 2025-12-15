import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# Définir les paramètres pour les figures IEEE
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "font.size": 8,
    "figure.figsize": (3.5, 2.5),  # Largeur de colonne
    "figure.dpi": 600
})

# Vérifier que le fichier existe
csv_file = 'convergence_study_data.csv'
if not os.path.exists(csv_file):
    print(f"Erreur: Le fichier {csv_file} n'existe pas dans le répertoire courant.")
    print(f"Répertoire courant: {os.getcwd()}")
    exit(1)

# Afficher les premières lignes du fichier pour diagnostic
print("Contenu des premières lignes du fichier:")
with open(csv_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        print(f"{i+1}: {line.strip()}")
        if i >= 3:
            break

# Charger les données du fichier CSV
try:
    data = pd.read_csv(csv_file, encoding='utf-8')
    print("Lecture réussie du fichier CSV")
except Exception as e:
    print(f"Erreur lors de la lecture du fichier: {e}")
    exit(1)

# Afficher les colonnes pour vérification
print("Colonnes détectées:")
print(data.columns.tolist())
print("\nPremières lignes des données:")
print(data.head())

# Première figure: potentiels électriques vs r_air
fig1, ax1 = plt.subplots()
ax1.plot(data['r_air (cm)'], data['Potentiel électrique Flottant (V)'], 'o-', label='Flottant')
ax1.plot(data['r_air (cm)'], data['Potentiel électrique Zero Charge (V)'], 's-', label='Zero Charge')
ax1.plot(data['r_air (cm)'], data['Moyenne (V)'], '^-', label='Moyenne')

ax1.set_xlabel('$r_{air}$ (cm)')
ax1.set_ylabel('Potentiel électrique (V)')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend(frameon=False, fontsize=7)

# Ajuster les limites pour mieux voir les variations
y_min = min(data['Potentiel électrique Flottant (V)'].min(), 
            data['Potentiel électrique Zero Charge (V)'].min(), 
            data['Moyenne (V)'].min()) * 0.99
y_max = max(data['Potentiel électrique Flottant (V)'].max(), 
            data['Potentiel électrique Zero Charge (V)'].max(), 
            data['Moyenne (V)'].max()) * 1.01
ax1.set_ylim(y_min, y_max)

# Ajuster les marges
plt.tight_layout()

# Deuxième figure: erreurs en % vs r_air
fig2, ax2 = plt.subplots()
ax2.plot(data['r_air (cm)'], data['erreur en %'], 'o-', label='Flottant')  # erreur en % pour Flottant
ax2.plot(data['r_air (cm)'], data['erreur en %.1'], 's-', label='Zero Charge')  # erreur en % pour Zero Charge
ax2.plot(data['r_air (cm)'], data['erreur en %.2'], '^-', label='Moyenne')  # erreur en % pour Moyenne

ax2.set_xlabel('$r_{air}$ (cm)')
ax2.set_ylabel('Erreur (%)')
ax2.set_yscale('log')  # Échelle logarithmique pour mieux visualiser les petites erreurs
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend(frameon=False, fontsize=7)

# Ajuster les marges
plt.tight_layout()

# Générer un timestamp pour les noms de fichiers
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Sauvegarder les figures en format EPS
fig1.savefig(f"{timestamp}_convergence_study_potentiels.eps", format="eps", dpi=600)
fig1.savefig(f"{timestamp}_convergence_study_potentiels.pdf", format="pdf", dpi=600)

fig2.savefig(f"{timestamp}_convergence_study_erreurs.eps", format="eps", dpi=600)
fig2.savefig(f"{timestamp}_convergence_study_erreurs.pdf", format="pdf", dpi=600)

print(f"Figures sauvegardées avec le préfixe: {timestamp}_convergence_study")

# Afficher les figures
plt.show() 