# PyMoDAQ - Vue d'ensemble de l'architecture

**Date d'analyse:** 2025-11-16  
**Version analysée:** PyMoDAQ 5.0.x  
**Analyste:** Agent d'analyse SOLID

---

## 1. Contexte et Objectif

PyMoDAQ (Modular Data Acquisition with Python) est un framework conçu pour simplifier l'acquisition de données expérimentales. Le projet vise à fournir une interface complète pour effectuer des mesures automatisées sans avoir à écrire une interface utilisateur pour chaque nouvelle expérience.

### 1.1 Objectifs du framework

1. **Dashboard Module** : Interface complète pour effectuer des mesures automatisées ou enregistrer des données
2. **Custom Apps** : Fourniture d'outils modulaires pour construire des applications personnalisées

---

## 2. Architecture Globale

### 2.1 Structure par couches

PyMoDAQ suit une architecture en couches qui respecte en grande partie les principes SOLID et DDD :

```
┌─────────────────────────────────────────────────────┐
│         DASHBOARD (Orchestration Layer)              │
│  - Preset management                                 │
│  - Module lifecycle management                       │
│  - Extension loading                                 │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │                         │
┌─────────▼─────────┐    ┌─────────▼──────────┐
│  CONTROL MODULES   │    │    EXTENSIONS      │
│                    │    │                    │
│  - DAQ_Move        │    │  - DAQ_Scan        │
│  - DAQ_Viewer      │    │  - DAQ_Logger      │
│                    │    │  - PID             │
└─────────┬──────────┘    │  - Bayesian Opt.   │
          │               └────────────────────┘
          │
┌─────────▼──────────────────────────────────────┐
│           PLUGIN SYSTEM                         │
│  Entry points based (pymodaq.instruments)       │
│  - Hardware abstraction                         │
│  - Actuator plugins (DAQ_Move_base)            │
│  - Detector plugins (DAQ_Viewer_base)          │
└─────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────┐
│      HARDWARE CONTROLLERS                       │
│  Implementations spécifiques au matériel        │
└─────────────────────────────────────────────────┘
```

---

## 3. Composants Principaux

### 3.1 Dashboard (Couche Orchestration)

**Fichier:** `src/pymodaq/dashboard.py`

**Responsibility:** Le Dashboard est le point d'entrée principal qui orchestre les modules de contrôle (actuateurs et détecteurs) et gère leur cycle de vie.

**Rationale:** Centraliser l'orchestration permet de séparer la logique métier de l'interface utilisateur et de gérer de manière cohérente les différents modules.

**Caractéristiques:**
- Utilise `ModulesManager` pour gérer les collections d'actuateurs et de détecteurs
- Utilise `PresetManager` pour charger/sauvegarder des configurations
- Charge dynamiquement les extensions via le système d'entry points
- Gère l'initialisation et la communication entre modules

**Relations principales:**
- Contient des listes de `DAQ_Move` (actuators_modules)
- Contient des listes de `DAQ_Viewer` (detector_modules)
- Crée et gère les extensions (`DAQ_Scan`, `DAQ_Logger`, etc.)

---

### 3.2 Control Modules (Couche Abstraction Hardware)

#### 3.2.1 DAQ_Move (Actuators)

**Fichier:** `src/pymodaq/control_modules/daq_move.py`

**Responsibility:** Module générique pour contrôler/piloter un actionneur (actuator). Fournit une interface standardisée pour déplacer des axes/moteurs indépendamment du matériel sous-jacent.

**Rationale:** Abstraire le contrôle des actuateurs permet de changer de matériel sans modifier le code de haut niveau.

**Caractéristiques:**
- Hérite de `ParameterControlModule`
- Utilise le pattern Factory via `ActuatorUIFactory` pour les différentes UIs
- Signaux principaux:
  - `move_done_signal`: émis quand l'actuateur a fini son mouvement
  - `current_value_signal`: émet la position courante
  - `bounds_signal`: émis quand les limites sont atteintes

**Architecture interne:**
```
DAQ_Move
  ├── UI Layer (ActuatorUIFactory)
  │   └── DAQ_Move_UI_Base (abstraite)
  │       ├── Original UI
  │       ├── Binary UI
  │       ├── Relative UI
  │       └── Simple UI
  │
  └── Hardware Layer
      └── DAQ_Move_Hardware (thread séparé)
          └── Plugin (DAQ_Move_base)
              └── Controller (matériel spécifique)
```

---

#### 3.2.2 DAQ_Viewer (Detectors)

**Fichier:** `src/pymodaq/control_modules/daq_viewer.py`

**Responsibility:** Module générique pour contrôler/piloter un détecteur. Fournit une interface standardisée pour acquérir des données (0D, 1D, 2D, ND).

**Rationale:** Abstraire l'acquisition des détecteurs permet d'utiliser différents types de capteurs de manière uniforme.

**Caractéristiques:**
- Hérite de `ParameterControlModule`
- Signaux principaux:
  - `grab_done_signal`: émis quand les données sont disponibles
  - `overshoot_signal`: émis si seuil dépassé
- Gère différents types de données (0D, 1D, 2D, ND)

---

### 3.3 Extensions (Couche Application)

#### 3.3.1 DAQ_Scan

**Fichier:** `src/pymodaq/extensions/daq_scan.py`

**Responsibility:** Coordonner des acquisitions automatisées de données de plusieurs détecteurs en fonction d'un ou plusieurs actuateurs.

**Rationale:** Séparer la logique de scan de l'acquisition permet de créer des patterns de scan complexes sans modifier les modules de base.

**Caractéristiques:**
- Dépend du Dashboard pour accéder aux modules
- Utilise `Scanner` pour définir les positions
- Utilise `ModulesManager` pour coordonner actuateurs et détecteurs
- Gère la sauvegarde via `H5Saver`

**Architecture du scan:**
```
DAQScan
  ├── Scanner (configuration des positions)
  │   ├── ScannerFactory
  │   └── ScannerBase (abstrait)
  │       ├── Linear1D, Linear2D
  │       ├── TabularScanner
  │       └── SequentialScanner
  │
  ├── ModulesManager (coordination)
  │   ├── Actuators (DAQ_Move list)
  │   └── Detectors (DAQ_Viewer list)
  │
  └── H5Saver (persistence)
```

---

### 3.4 Système de Scanner (Scan Multi-Points)

**Fichiers:** `src/pymodaq/utils/scanner/`

**Responsibility:** Calculer et gérer les positions pour les acquisitions multi-points selon différents patterns (linéaire, tabulaire, séquentiel).

**Rationale:** Séparer la génération des positions de scan de l'exécution permet d'ajouter facilement de nouveaux types de scans.

**Architecture:**

```
ScannerBase (Abstract)
  │
  ├── Attributs abstraits:
  │   ├── scan_type: str
  │   ├── scan_subtype: str
  │   ├── positions: np.ndarray (n_axes × n_steps)
  │   ├── axes_unique: List[np.ndarray]
  │   ├── axes_indexes: np.ndarray
  │   ├── n_steps: int
  │   └── n_axes: int
  │
  └── Implémentations concrètes:
      ├── Linear1DScanner
      ├── Linear2DScanner
      ├── TabularScanner
      └── SequentialScanner
```

**Principe de fonctionnement:**
1. Le Scanner calcule toutes les positions avant l'exécution
2. Les positions sont stockées dans un tableau numpy (axes × steps)
3. Le DAQScan itère sur ces positions et coordonne le mouvement + acquisition

---

### 3.5 Système de Plugins

**Fichier:** `src/pymodaq/utils/daq_utils.py` (fonction `get_instrument_plugins`)

**Responsibility:** Découvrir et charger dynamiquement les plugins d'instruments via les entry points Python.

**Rationale:** L'utilisation d'entry points permet d'ajouter du nouveau matériel sans modifier le code du framework (Open/Closed Principle).

**Mécanisme:**

```python
# Entry points dans pyproject.toml:
[project.entry-points.'pymodaq.instruments']
plugin_name = 'pymodaq_plugins_xxx'

# Découverte automatique:
discovered_plugins = get_entrypoints(group='pymodaq.instruments')
```

**Types de plugins:**
- `pymodaq.instruments` : plugins d'instruments (actuateurs, détecteurs)
- `pymodaq.extensions` : extensions du dashboard
- `pymodaq.scanners` : types de scanners personnalisés
- `pymodaq.models` : modèles pour PID ou autres

---

## 4. Analyse SOLID

### 4.1 Single Responsibility Principle (SRP) ✅

**Respect:** ÉLEVÉ

- Dashboard : orchestration uniquement
- DAQ_Move : contrôle d'actuateurs uniquement
- DAQ_Viewer : acquisition de données uniquement
- Scanner : calcul de positions uniquement
- ModulesManager : gestion de collections de modules

**Observation:** Chaque classe a une responsabilité claire et documentée.

---

### 4.2 Open/Closed Principle (OCP) ✅

**Respect:** ÉLEVÉ

- Le système de plugins permet d'ajouter du nouveau matériel sans modifier le code existant
- Les Scanners utilisent le pattern Factory pour ajouter de nouveaux types de scans
- Les UIs d'actuateurs utilisent également un Factory pattern
- Les extensions sont chargées dynamiquement via entry points

**Observation:** Le framework est conçu pour l'extension.

---

### 4.3 Liskov Substitution Principle (LSP) ✅

**Respect:** ÉLEVÉ

- Tous les plugins héritent de `DAQ_Move_base` ou `DAQ_Viewer_base`
- Les Scanners héritent de `ScannerBase`
- Les interfaces sont respectées par les implémentations

**Observation:** Les abstractions sont bien définies et les substitutions fonctionnent.

---

### 4.4 Interface Segregation Principle (ISP) ✅

**Respect:** MOYEN-ÉLEVÉ

- Les bases classes définissent des interfaces claires
- Certaines classes ont beaucoup de méthodes (Dashboard), mais cela semble justifié par leur rôle d'orchestration

**Observation:** Globalement respecté, quelques interfaces pourraient être plus ségrégées.

---

### 4.5 Dependency Inversion Principle (DIP) ✅

**Respect:** ÉLEVÉ

- Les modules de haut niveau (Dashboard, DAQScan) dépendent d'abstractions (DAQ_Move, DAQ_Viewer)
- Les plugins implémentent des interfaces abstraites (DAQ_Move_base, DAQ_Viewer_base)
- Le système de plugins évite les dépendances directes vers le matériel

**Observation:** Le framework utilise bien l'inversion de dépendances.

---

## 5. Flux d'Exécution d'un Scan

```
1. Dashboard initialise actuateurs et détecteurs
   ↓
2. User lance DAQ_Scan extension
   ↓
3. DAQScan récupère les modules depuis Dashboard
   ↓
4. Scanner calcule toutes les positions (n_steps)
   ↓
5. Pour chaque step:
   a. DAQScan commande les actuateurs (DAQ_Move)
   b. Attend la fin du mouvement (move_done_signal)
   c. Commande l'acquisition (DAQ_Viewer.grab())
   d. Attend les données (grab_done_signal)
   e. Sauvegarde les données (H5Saver)
   f. Affiche les données (Navigator)
   ↓
6. Fin du scan, sauvegarde finale
```

---

## 6. Points d'Extension pour AEFI_Acquisition

### 6.1 Approche Recommandée

**Ne PAS** créer des plugins pour votre matériel Legacy  
**MAIS** créer une extension DAQScan personnalisée ou utiliser l'existante

**Rationale:**
- Le système de scan multi-points existe déjà
- Le système de coordination actuateurs/détecteurs existe déjà
- Il suffit de créer des plugins pour votre matériel spécifique

### 6.2 Plugins à Créer

1. **Plugin Actuator (Arcus Performax)**
   - Hériter de `DAQ_Move_base`
   - Implémenter le contrôle du moteur rotatif

2. **Plugin Detector (Oscilloscope + Narda)**
   - Hériter de `DAQ_Viewer_base`
   - Type: `daq_1Dviewer` ou `daq_0Dviewer`
   - Implémenter l'acquisition synchronisée

3. **Scanner personnalisé (optionnel)**
   - Si besoin de patterns de scan spécifiques
   - Hériter de `ScannerBase`

### 6.3 Réutilisation

- ✅ Utiliser `DAQ_Scan` tel quel
- ✅ Utiliser `Dashboard` tel quel
- ✅ Utiliser `H5Saver` pour la persistance
- ✅ Créer des plugins pour votre matériel uniquement

---

## 7. Conclusion

**Architecture:** PyMoDAQ suit une architecture modulaire et extensible qui respecte largement les principes SOLID et DDD.

**Conformité SOLID:** ÉLEVÉE (4.5/5)

**Recommandation:** Utiliser PyMoDAQ comme base pour AEFI_Acquisition en créant des plugins pour le matériel spécifique plutôt que de reconstruire l'orchestration.

**Prochaines étapes:**
1. Analyser en détail le système de plugins
2. Créer un template de plugin pour le matériel AEFI
3. Identifier les dépendances du code Legacy à migrer


