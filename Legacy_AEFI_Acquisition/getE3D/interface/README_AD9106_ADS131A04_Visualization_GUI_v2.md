# Interface d'Acquisition AD9106/ADS131A04 (PyQt5)

Ce script lance l'interface graphique moderne pour piloter un banc d'acquisition AD9106/ADS131A04.

## Fonctionnalités principales
- **2 modes** : Temps Réel (exploration) et Export (mesures)
- **Affichage numérique** temps réel sur 8 canaux ADC, avec statistiques glissantes (moyenne, écart-type)
- **Visualisation graphique** (pyqtgraph) synchronisée
- **Export CSV** automatique en mode mesures
- **Réglages avancés** DDS/ADC accessibles dans un onglet dédié
- **Synchronisation centralisée** via AcquisitionManager

## Lancement
- Prérequis : Python 3.8+, PyQt5, pyqtgraph, numpy
- Commande :
```bash
python AD9106_ADS131A04_Visualization_GUI_v2.py
```

## Documentation détaillée
- Voir le fichier de tâches : `AD9106_ADS131A04_Visualization_GUI_tasks.md`

## Structure
- Architecture modulaire :
  - `AcquisitionManager` : gestion centralisée de l'acquisition et du buffer
  - Widgets PyQt5 pour la configuration, l'affichage, les contrôles et les réglages avancés
  - Communication hardware via SerialCommunicator (instancié automatiquement)

