# EFImagingBench_Oscilloscope_DSOX2014.py

Ce module fournit une interface Python pour contrôler et acquérir des mesures depuis un oscilloscope Keysight/Agilent DSO-X 2014A via PyVISA.

## Fonctionnalités principales
- **Connexion automatique** à l'oscilloscope via USB (PyVISA).
- **Configuration des canaux** (échelle verticale, offset, couplage AC/DC, ratio de sonde).
- **Configuration de l'acquisition** (moyennage, mode normal).
- **Configuration du trigger** (source, niveau, pente).
- **Configuration de la base de temps** (échelle horizontale, position).
- **Acquisition de la forme d'onde** (récupération du signal brut).
- **Lecture des mesures automatiques** (Vpp, Vrms, fréquence, etc.).
- **Optimisation automatique de la fenêtre verticale** pour maximiser la dynamique du signal sans saturation.
- **Mesure de phase** entre deux canaux.
- **Gestion robuste des erreurs de communication** avec réinitialisation automatique.

## Classe principale
### `OscilloscopeDSOX2014AController`

#### Méthodes principales :
- `connect()` : Connexion automatique à l'oscilloscope USB.
- `reset_device()` : Réinitialise l'oscilloscope en cas de problème de communication.
- `safe_query(command, max_retries)` : Exécute une requête SCPI avec gestion des erreurs et tentatives de récupération.
- `configure_channel(channel, vdiv, offset, coupling, sonde_ratio)` : Configure un canal (échelle, offset, couplage AC/DC) en tenant compte du ratio de sonde.
- `configure_acquisition(average_count)` : Configure le mode d'acquisition (moyennage ou normal).
- `configure_trigger(source, level, slope)` : Configure le trigger.
- `configure_timebase(tscale, position)` : Configure la base de temps (échelle horizontale et position).
- `get_waveform(channel)` : Récupère la forme d'onde du canal spécifié.
- `get_measurements(channel)` : Récupère les mesures automatiques (Vpp, Vrms, etc.).
- `optimize_vdiv(channel, margin, vdiv_min, vdiv_max, coupling, vdiv_init, sonde_ratio)` :
    - Optimise automatiquement l'échelle verticale pour que le signal occupe ~90% de la dynamique de l'écran.
    - Essaie plusieurs valeurs de vdiv si besoin, évite les valeurs aberrantes.
    - Permet de choisir le couplage (AC par défaut, DC possible).
    - Prend en compte le ratio de sonde (x1, x10, etc.) pour adapter l'échelle.
    - Gère correctement la conversion entre la valeur de vdiv demandée et la valeur effective appliquée à l'oscilloscope.
    - Retourne un tuple (success, vdiv_opt, Vpp, essais) où success est un booléen indiquant si l'optimisation s'est bien terminée.
- `measure_phase(ch1, ch2)` : Mesure le déphasage entre deux canaux (en degrés).
- `close()` : Ferme proprement la connexion à l'oscilloscope.

## Exemple d'utilisation
```python
from EFImagingBench_Oscilloscope_DSOX2014 import OscilloscopeDSOX2014AController
import time

scope = OscilloscopeDSOX2014AController()
# Configuration avec sonde x10
scope.configure_channel(channel=1, vdiv=5.0, offset=0.0, coupling="AC", sonde_ratio=10)
scope.configure_acquisition(average_count=64)
scope.configure_trigger(source="CHAN1", level=0.0, slope="POS")

# Configuration de la base de temps pour visualiser un signal de 1kHz (1ms)
scope.configure_timebase(tscale=0.0002, position=0.0)  # 200µs/div pour voir ~2 périodes

time.sleep(1)
t, v = scope.get_waveform(channel=1)
measures = scope.get_measurements(channel=1)

# Optimisation automatique de la fenêtre avec sonde x10
success, vdiv_opt, Vpp, essais = scope.optimize_vdiv(channel=1, coupling="AC", sonde_ratio=10)
if success:
    print(f"vdiv optimal : {vdiv_opt}, Vpp : {Vpp}, essais : {essais}")

# Mesure de phase entre canaux 1 et 2
try:
    phase = scope.measure_phase(1, 2)
    print(f"Déphasage : {phase} degrés")
except RuntimeError as e:
    print(f"Erreur de mesure de phase : {e}")

scope.close()
```

## Dépendances
- Python 3.x
- pyvisa
- numpy

## Notes
- Le module est conçu pour le modèle DSO-X 2014A, mais peut fonctionner avec d'autres modèles compatibles SCPI/VISA.
- Pour le couplage, "AC" est recommandé pour la plupart des signaux alternatifs.
- L'optimisation de la fenêtre permet d'automatiser la mise à l'échelle du signal pour des mesures fiables et reproductibles.
- Le paramètre `sonde_ratio` permet de prendre en compte les sondes d'atténuation (x1, x10, etc.) :
  - Une sonde x10 a un `sonde_ratio=10`
  - La valeur effective de vdiv appliquée à l'oscilloscope est `vdiv * sonde_ratio`
  - Les valeurs retournées par `optimize_vdiv` sont déjà ajustées : le vdiv_opt est la valeur brute (avant multiplication par sonde_ratio)
  - Exemple : avec une sonde x10, si optimize_vdiv retourne vdiv_opt=0.5, l'échelle effective sur l'oscilloscope sera 5V/div
- La méthode `configure_timebase` vérifie que les valeurs demandées ont bien été appliquées par l'oscilloscope et retourne un booléen indiquant le succès de l'opération.
- La méthode `safe_query` améliore la robustesse des communications SCPI :
  - Gère automatiquement les erreurs de timeout
  - Effectue plusieurs tentatives en cas d'échec
  - Réinitialise l'appareil si nécessaire via `reset_device()`
- La méthode `reset_device` permet de récupérer la communication en cas de problème persistant :
  - Ferme et rétablit la connexion
  - Envoie une commande de reset (*RST) à l'oscilloscope
  - Vérifie que la communication est rétablie 