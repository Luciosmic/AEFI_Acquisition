# EFImagingBench_DDSAmplification_CaracterisationGain

## Description

Ce projet permet de caractériser un système DDS avec amplification en deux étapes bien séparées :

1. **Acquisition** (script principal)
   - Pilote les instruments (DDS, oscilloscope)
   - Acquiert les signaux pour chaque gain
   - Sauvegarde uniquement :
     - Les données brutes (`rawData`) : tous les points temporels (gain, t, v)
     - Les paramètres de configuration (`Parameters`) : fréquence, gains, ratio sonde, canaux, date, etc.
   - Appelle automatiquement le script de post-process/visualisation à la fin

2. **Post-process/visualisation** (script dédié)
   - Vérifie si le fichier `processedData` existe déjà
     - Si oui : affiche directement les graphiques
     - Sinon : calcule les données dérivées (FFT, THD, Vpp, etc.) à partir du `rawData`, sauvegarde le `processedData`, puis affiche les graphiques
   - Génère tous les graphiques d'analyse (THD, Vpp, amplitude fondamentale, fréquence fondamentale)

## Organisation des fichiers générés

- **JSON** : `{date}_Parameters_{suffix}.json` (paramètres de configuration uniquement)
- **CSV** : `{date}_rawData_{suffix}.csv` (mesures brutes)
- **CSV** : `{date}_processedData_{suffix}.csv` (résultats d'analyse, une ligne par gain)
- **Graphiques** : `{date}_processedData_{suffix}_thd_vs_gain.png`, etc.
- **Sous-dossier `spectrums`** (optionnel) : spectres FFT individuels pour chaque gain

## Flux de travail recommandé

1. **Acquisition** :
   - Lancer le script principal pour générer les fichiers bruts et paramètres
   - Le post-process/visualisation est appelé automatiquement
2. **Post-process/visualisation** :
   - Peut être relancé à tout moment sur un jeu de données existant (rawData ou processedData)
   - Permet de retraiter d'anciennes acquisitions sans instrument

## Avantages de la séparation

- **Lisibilité et maintenance** : chaque script a une responsabilité claire
- **Réutilisabilité** : retraitement facile, visualisation indépendante
- **Robustesse** : pas de dépendance matérielle pour le post-process
- **Automatisation** : chaînage ou traitement en lot facilité

## Dépendances

- numpy
- pandas
- matplotlib
- pathlib
- datetime
- re
- (modules spécifiques à votre matériel pour la communication DDS/oscilloscope)

## Exemple de lancement

```bash
python EFImagingBench_DDSAmplification_CaracterisationGain.py
```

## Auteur

*Votre nom / laboratoire / contact* 