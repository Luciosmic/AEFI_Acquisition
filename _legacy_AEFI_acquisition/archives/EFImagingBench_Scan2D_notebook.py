# %% [markdown]
# # EFImagingBench Scan 2D - Développement interactif avec Cursor
# 
# Ce fichier utilise la syntaxe Cursor pour créer des cellules Jupyter dans un fichier .py
# Suivant la todo-list du fichier `EFImagingBench_Scan2D_tasks.md`
# 
# **Objectif :** Créer un script minimal pour un balayage 2D avec acquisition synchronisée

# %% [markdown]
# ## 1. Initialisation des modules
# 
# Nous commençons par importer et initialiser le contrôleur de moteurs et le module d'acquisition.

# %%
import sys
import os

# Ajouter les chemins relatifs vers les modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "ArcusPerformaxPythonController"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "getE3D"))

from controller.EFImagingBench_Controller_ArcusPerformax4EXStage import EFImagingStageController
from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator

print("Modules importés avec succès")

# %% [markdown]
# ### 1.1. Initialisation du contrôleur de moteurs
# 
# Le chemin DLL et les paramètres de vitesse par défaut sont intégrés dans la classe.

# %%
stage = EFImagingStageController()
print("Contrôleur de moteurs initialisé")

# %% [markdown]
# ### 1.2. Initialisation du module d'acquisition

# %%
acq = SerialCommunicator()
success, msg = acq.connect("COM10")  # Adapter le port série selon votre configuration
if not success:
    raise RuntimeError(f"Erreur de connexion acquisition : {msg}")
print("Module d'acquisition connecté avec succès")

# %% [markdown]
# ## 2. Homing des axes
# 
# Le homing est **obligatoire** avant tout déplacement. On effectue le homing des axes X et Y.

# %% [markdown]
# ### 2.1. Homing axe X

# %%
print("Début du homing axe X...")
stage.home('x')
stage.wait_move('x', timeout=30)
print("Homing axe X terminé")

# %% [markdown]
# ### 2.2. Homing axe Y

# %%
print("Début du homing axe Y...")
stage.home('y')
stage.wait_move('y', timeout=30)
print("Homing axe Y terminé")

# %% [markdown]
# ### 2.3. Vérification que les deux axes sont bien "homés"

# %%
if not (stage.is_axis_homed('x') and stage.is_axis_homed('y')):
    raise RuntimeError("Homing non effectué sur X ou Y. Impossible de continuer.")
print("✅ Vérification réussie : les deux axes sont homés et prêts")

# %% [markdown]
# ## 3. Configuration du balayage
# 
# Définir les paramètres du scan 2D : nombre de lignes, longueurs, vitesses, fréquence d'échantillonnage.

# %%
# Configuration du balayage
x_nb = 10          # Nombre de lignes dans la direction X
x_length = 5000    # Longueur de balayage en X (en unités moteur)
y_length = 3000    # Longueur de balayage en Y (en unités moteur)
y_speed = 300      # Vitesse de déplacement sur Y (en unités/s)
sampling_rate = 1000  # Fréquence d'échantillonnage (Hz)

print(f"Configuration du scan :")
print(f"  - Nombre de lignes X : {x_nb}")
print(f"  - Longueur X : {x_length}")
print(f"  - Longueur Y : {y_length}")
print(f"  - Vitesse Y : {y_speed}")
print(f"  - Fréquence échantillonnage : {sampling_rate} Hz")

# %% [markdown]
# ## 4. Balayage 2D et acquisition
# 
# **Structure pour la boucle de scan** - À développer selon les prochaines étapes de la todo-list

# %%
import numpy as np
import time

# Calcul des positions X
x_positions = np.linspace(0, x_length, x_nb)

# Structure pour stocker les données
scan_data = {
    'x_positions': [],
    'y_speeds': [],
    'acquisition_data': [],
    'timestamps': []
}

print(f"Positions X calculées : {x_positions}")
print("Structure de données initialisée")
print("🚧 Prêt pour développer la boucle de scan")

# %% [markdown]
# ## 5. Fermeture propre
# 
# N'oubliez pas de fermer proprement les connexions à la fin du développement.

# %%
# Fermeture des connexions (à exécuter en fin de session)
# stage.close()
# acq.disconnect()
print("💡 Pensez à fermer les connexions : stage.close() et acq.disconnect()") 
