# Visualiseur LIDAR en direct

Outil de banc autonome : affiche en direct ce que mesure un LIDAR série ESP32 (VL53L0X, lignes `"<brut> <moyenne10>"`), sans lancer l'application AEFI. Sert à installer et aligner l'obstacle avant une calibration de transmission, et à constater le bruit du capteur.

La lecture passe par l'adapter de l'application (`src/infrastructure/hardware/esp32_serial_lidar/`) : même règle de parsing (colonne brute seule, `0` = pas de retour, première ligne jetée).

## Lancement

```
uv run python external_modules/lidar_live_viewer/lidar_live_viewer.py --port COM9
```

Options : `--port` (défaut `COM9`), `--baudrate` (défaut `115200`). Un autre LIDAR au même format : changer `--port`.

## Affichage

- dernière distance brute (mm, **unité supposée** : brut × 1, non vérifiée) ou « pas de retour » ;
- moyenne et écart-type sur les N dernières lectures valides (N réglable, défaut 25), nombre de lectures, débit (Hz), nombre de « pas de retour » ;
- courbe des 60 dernières secondes ;
- bouton « Remise à zéro des stats ».

## Port exclusif

Un port COM ne peut être tenu que par un seul programme. Fermer le visualiseur (fenêtre ou Ctrl+C) avant de lancer l'application AEFI ou un moniteur série sur le même port, et inversement. Si le port est déjà pris, la fenêtre affiche le message d'erreur au lieu des mesures.
