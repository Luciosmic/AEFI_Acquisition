# Structure du Projet

Le projet EFImagingBench_App suit une architecture modulaire organisée pour faciliter le développement, la maintenance et l'extensibilité du système de contrôle de banc d'acquisition.

## Arborescence

```
EFImagingBench_App/
├── archives/                           # Anciennes versions et sauvegardes
├── config/                            # Fichiers de configuration
├── docs/                              # Documentation du projet
├── examples/                          # Exemples d'utilisation et scripts démo
├── src/                              # Code source principal
│   ├── core/                         # Fonctionnalités centrales
│   │   ├── AD9106_ADS131A04_ElectricField_3D/
│   │   └── ArcusPerforma4EXStage/
│   ├── data_processing/              # Traitement et analyse des données
│   │   ├── EFImagingBench_exportCSV.py
│   │   └── EFImagingBench_filters.py
│   ├── gui/                          # Interface utilisateur
│   │   └── EFImagingBench_GUI.py
│   ├── utils/                        # Utilitaires et fonctions helpers
│   ├── EFImagingBench_metaManager_tasks.py  # Gestionnaire de tâches
│   └── EFImagingBench_metaManager.py        # Gestionnaire principal
├── tests/                            # Tests unitaires et d'intégration
└── setup.py                          # Configuration d'installation
```

## Description des Modules

### 📁 `src/core/`
Contient les modules de contrôle des instruments spécialisés :
- **`AD9106_ADS131A04_ElectricField_3D/`** : Contrôle du générateur de signaux AD9106 et de l'ADC ADS131A04 pour l'imagerie 3D de champs électriques
- **`ArcusPerforma4EXStage/`** : Interface avec les platines de positionnement Arcus Performax 4EX

### 📁 `src/data_processing/`
Modules dédiés au traitement et à l'analyse des données expérimentales :
- **`EFImagingBench_exportCSV.py`** : Export des données vers différents formats (CSV, Excel, HDF5)
- **`EFImagingBench_filters.py`** : Filtrage numérique, compensation d'amplitude et de phase, traitement du signal

### 📁 `src/gui/`
Interface graphique utilisateur :
- **`EFImagingBench_GUI.py`** : Interface principale pour le contrôle interactif du banc d'acquisition

### 📁 `src/utils/`
Fonctions utilitaires partagées, configuration des logs, validateurs et fonctions helper.

### 📁 Gestionnaires Principaux
- **`EFImagingBench_metaManager.py`** : Gestionnaire principal coordonnant l'ensemble des modules
- **`EFImagingBench_metaManager_tasks.py`** : Système de gestion des tâches et de la planification des expériences

### 📁 `config/`
Fichiers de configuration pour les instruments, paramètres d'expériences et données de calibration.

### 📁 `examples/`
Scripts d'exemple démontrant l'utilisation des différents modules et fonctionnalités.

### 📁 `tests/`
Suite de tests pour assurer la qualité et la fiabilité du code (tests unitaires, d'intégration et de validation matérielle).

## Principe de Modularité

Cette architecture permet :
- **Extensibilité** : Ajout facile de nouveaux instruments dans `core/`
- **Réutilisabilité** : Modules indépendants réutilisables dans d'autres projets
- **Maintenabilité** : Séparation claire des responsabilités
- **Testabilité** : Chaque module peut être testé indépendamment