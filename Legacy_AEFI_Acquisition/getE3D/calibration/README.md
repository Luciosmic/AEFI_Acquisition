# Calibration des DDS et Mesures de Phase

Ce dossier contient tout le nécessaire pour effectuer les mesures et la calibration des signaux DDS, afin de garantir que les signaux restent parfaitement en phase même après amplification.

## Organisation

- `mesures/` : fichiers de mesures brutes (CSV, TXT, etc.)
- `scripts/` : scripts Python pour automatiser les mesures, l'analyse et la calibration

## Procédure type

1. **Mesures** :
   - Utiliser les scripts de `scripts/` pour piloter le banc, collecter les signaux (avant/après amplification) et enregistrer les données dans `mesures/`.
2. **Analyse** :
   - Calculer le déphasage, l'amplitude, etc. à partir des mesures.
3. **Calibration** :
   - Ajuster les paramètres DDS pour compenser les déphasages/amplitudes.
   - Documenter les résultats et corrections appliquées.

## À compléter
- Ajouter ici toute information utile sur la procédure, les instruments utilisés, ou les scripts spécifiques. 