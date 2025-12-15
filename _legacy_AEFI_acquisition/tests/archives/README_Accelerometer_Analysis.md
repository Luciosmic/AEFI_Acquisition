# Analyse de l'Accéléromètre LSM9D - Banc d'Imagerie EF

## 📋 Vue d'Ensemble

Ce répertoire contient les scripts d'analyse pour étudier le comportement de l'accéléromètre LSM9D dans le contexte du banc d'imagerie en champ électrique. L'objectif est de caractériser les performances du capteur et l'influence des mouvements du stage Arcus Performax sur les mesures.

## 🎯 Objectifs de l'Analyse

### 1. **Mesure du Niveau de Bruit** 🔇
- Caractériser le bruit intrinsèque de l'accéléromètre au repos
- Évaluer la stabilité des mesures dans le temps
- Déterminer la résolution effective du capteur

### 2. **Analyse Fréquentielle des Vibrations** 📊
- Étudier le spectre fréquentiel pendant les mouvements
- Identifier les fréquences de résonance du système
- Analyser l'impact des différentes vitesses de déplacement

### 3. **Influence de l'Accélération** 🚀
- Corréler les paramètres d'accélération du stage avec le signal mesuré
- Optimiser les profils de mouvement pour minimiser les vibrations
- Caractériser la réponse dynamique du système

## 📁 Structure des Scripts

### 🔧 `simple_acquisition_test.py`
**Script de base pour valider le système**

```bash
python simple_acquisition_test.py
```

**Fonctionnalités :**
- Connexion automatique au capteur LSM9D
- Configuration en mode ALL_SENSORS (20 Hz)
- Acquisition de données configurables (durée, port)
- Sauvegarde automatique en CSV et JSON
- Affichage de statistiques en temps réel

**Usage typique :**
- Test de connectivité
- Validation de la chaîne d'acquisition
- Mesures de bruit de référence

### 🔬 `accelerometer_analysis_script.py`
**Script complet d'analyse avec contrôle du stage**

```bash
python accelerometer_analysis_script.py
```

**Fonctionnalités :**
- Intégration complète LSM9D + Arcus Performax
- Menu interactif pour différents types d'expériences
- Synchronisation mouvement/acquisition
- Paramétrage avancé des profils de vitesse
- Analyse automatique des résultats

**Types d'expériences disponibles :**
1. **Mesure de bruit statique** - Système au repos
2. **Mouvement lent** - Analyse des basses fréquences  
3. **Mouvement rapide** - Caractérisation des hautes fréquences

## 📊 Format des Données de Sortie

### Structure des Fichiers

```
accelerometer_data/
├── experiment_type_YYYYMMDD_HHMMSS_001.csv
├── experiment_type_YYYYMMDD_HHMMSS_001_params.json
├── simple_test_YYYYMMDD_HHMMSS.csv
└── simple_test_YYYYMMDD_HHMMSS_params.json
```

### Format CSV
```csv
timestamp,time_relative,acc_x,acc_y,acc_z,mag_x,mag_y,mag_z,gyr_x,gyr_y,gyr_z,lidar
1701234567.123,0.000,-0.123,0.456,9.789,12.34,-5.67,23.45,0.12,-0.34,0.56,1234
```

**Colonnes :**
- `timestamp` : Timestamp Unix absolu
- `time_relative` : Temps relatif depuis le début (s)
- `acc_x/y/z` : Accélération 3 axes (m/s²)
- `mag_x/y/z` : Champ magnétique 3 axes (µT)
- `gyr_x/y/z` : Vitesse angulaire 3 axes (°/s)
- `lidar` : Distance LIDAR (mm)

### Format JSON (Paramètres)
```json
{
  "type": "movement_analysis",
  "description": "Mouvement lent pour analyse fréquentielle",
  "duration": 15.2,
  "timestamp_start": "2024-01-15T14:30:45.123456",
  "timestamp_end": "2024-01-15T14:31:00.456789",
  "lsm9d_mode": "ALL_SENSORS",
  "target_sampling_rate": 20,
  "actual_sampling_rate": 19.8,
  "actual_data_points": 302,
  "stage_movement": {
    "axis": "x",
    "initial_position": 1000,
    "target_position": 6000,
    "distance": 5000
  },
  "stage_parameters": {
    "ls": 10,
    "hs": 200,
    "acc": 100,
    "dec": 100
  },
  "movement_start_time": 1701234567.890,
  "movement_end_time": 1701234582.100,
  "actual_movement_duration": 14.21,
  "final_position": 5998
}
```

## ⚙️ Configuration et Prérequis

### Matériel Requis
- **Capteur LSM9D** connecté sur port série (défaut: COM5)
- **Contrôleur Arcus Performax 4EX** avec DLLs installées
- **Stage 2 axes** avec axes X et Y fonctionnels

### Dépendances Python
```bash
pip install pyserial numpy pylablib
```

### Configuration des Chemins
```python
# Dans les scripts
LSM9D_PORT = 'COM5'  # Adapter selon votre configuration
ARCUS_DLL_PATH = 'ArcusPerformaxPythonController/DLL64'
```

## 🚀 Guide d'Utilisation Rapide

### 1. Test Initial
```bash
# Vérifier la connectivité de base
python simple_acquisition_test.py
```
- Choisir durée : 10s pour test rapide
- Vérifier la génération des fichiers de données

### 2. Expérience Complète
```bash
# Lancer l'analyseur complet
python accelerometer_analysis_script.py
```
- **Option 1** : Mesure de bruit (30s) pour caractériser le niveau de base
- **Option 2** : Mouvement lent pour analyser les vibrations basse fréquence
- **Option 3** : Mouvement rapide pour les hautes fréquences

### 3. Exemple de Session Type
```
🔬 ANALYSEUR D'ACCÉLÉROMÈTRE LSM9D - BANC D'IMAGERIE EF
================================================================================
🔧 Initialisation des systèmes...
📡 Connexion au capteur LSM9D sur COM5...
✅ Capteur LSM9D connecté et configuré en mode ALL_SENSORS
🎮 Initialisation du contrôleur Arcus...
✅ Contrôleur Arcus initialisé

🎯 Menu des expériences disponibles:
1. Mesure de bruit statique (30s)
2. Analyse avec mouvement lent  
3. Analyse avec mouvement rapide
4. Quitter

Choisissez une expérience (1-4): 1

🔇 Début de la mesure de bruit - Mesure de bruit - système au repos
   Durée: 30.0s
📊 Acquisition démarrée - Fichier: noise_measurement_20241215_143045_001
⏳ Acquisition en cours (30.0s)...
   📊 Temps restant: 25.0s
   📊 Temps restant: 20.0s
   📊 Temps restant: 15.0s
   📊 Temps restant: 10.0s
   📊 Temps restant: 5.0s
📊 Acquisition terminée - 589 points collectés
💾 Données sauvegardées:
   📄 CSV: accelerometer_data/noise_measurement_20241215_143045_001.csv
   ⚙️  JSON: accelerometer_data/noise_measurement_20241215_143045_001_params.json
```

## 📈 Analyse des Résultats

### Outils Recommandés pour l'Analyse

#### Python/Jupyter
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Charger les données
df = pd.read_csv('accelerometer_data/experiment.csv')

# Analyse temporelle
plt.figure(figsize=(12, 8))
plt.subplot(3,1,1)
plt.plot(df['time_relative'], df['acc_x'])
plt.title('Accélération X vs Temps')

# Analyse fréquentielle
f, Pxx = signal.welch(df['acc_x'], fs=20)  # 20 Hz sampling
plt.subplot(3,1,2)
plt.semilogy(f, Pxx)
plt.title('Densité Spectrale - Accélération X')

# Analyse statistique
print(f"Écart-type Acc X: {df['acc_x'].std():.6f}")
print(f"Bruit RMS: {np.sqrt(np.mean(df['acc_x']**2)):.6f}")
```

#### MATLAB
```matlab
% Charger les données
data = readtable('accelerometer_data/experiment.csv');

% Analyse fréquentielle
[pxx, f] = pwelch(data.acc_x, [], [], [], 20);
loglog(f, pxx);
title('Densité Spectrale - Accélération X');

% Calcul du bruit
noise_level = std(data.acc_x);
fprintf('Niveau de bruit: %.6f m/s²\n', noise_level);
```

### Métriques d'Évaluation

#### 1. Niveau de Bruit (Système au Repos)
- **Écart-type σ** des mesures d'accélération
- **Bruit RMS** calculé sur toute la durée
- **Densité spectrale** pour identifier les fréquences parasites

#### 2. Analyse Dynamique (Avec Mouvement)
- **Fréquences de résonance** identifiées dans le spectre
- **Amplitude des vibrations** en fonction de la vitesse
- **Corrélation** entre profil d'accélération et vibrations mesurées

#### 3. Performance Globale
- **Rapport signal/bruit** pour différents régimes
- **Stabilité temporelle** des mesures
- **Reproductibilité** entre expériences similaires

## 🔍 Dépannage

### Problèmes Courants

#### ❌ Erreur de Connexion LSM9D
```
❌ Échec de connexion au capteur LSM9D
```
**Solutions :**
- Vérifier que le port COM5 est correct
- S'assurer que le capteur est alimenté
- Fermer autres applications utilisant le port série

#### ❌ Erreur DLL Arcus
```
❌ Erreur lors de l'initialisation: DLL not found
```
**Solutions :**
- Vérifier le chemin vers `ArcusPerformaxPythonController/DLL64`
- S'assurer que pylablib est installé
- Redémarrer Python après installation des DLLs

#### ❌ Homing Requis
```
❌ Homing requis pour l'axe X. Utilisez home('x') d'abord.
```
**Solutions :**
- Le script lance automatiquement le homing si nécessaire
- Vérifier que les butées de fin de course sont connectées
- S'assurer que l'axe peut se déplacer librement

### Validation des Résultats

#### Test de Cohérence
```python
# Vérifier la cohérence des données
assert len(timestamps) == len(accelerometer_data)
assert actual_sampling_rate > 15  # Au moins 15 Hz
assert abs(target_position - final_position) < 100  # Précision ±100 steps
```

#### Validation Physique
- L'accélération Z doit être proche de 9.81 m/s² (gravité)
- Les niveaux de bruit doivent être cohérents entre expériences
- Les fréquences identifiées doivent être reproductibles

## 📚 Documentation Complémentaire

### Références Techniques
- **LSM9D Backend** : `LSM9D/README_LSM9D_PYTHON.md`
- **Contrôleur Arcus** : `ArcusPerformaxPythonController/README.md`
- **Documentation LSM9DS1** : Spécifications du capteur

### Scripts Connexes
- **Interface graphique** : Pour visualisation temps réel
- **Analyse post-traitement** : Scripts MATLAB/Python dédiés
- **Calibration** : Procédures de calibration des capteurs

---

**Développé pour l'analyse des vibrations du banc d'imagerie EF** 🔬✨ 