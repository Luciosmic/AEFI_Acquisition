# PyMoDAQ - Système de Scanner pour Acquisitions Multi-Points

**Date d'analyse:** 2025-11-16  
**Fichiers analysés:**
- `src/pymodaq/utils/scanner/scanner.py`
- `src/pymodaq/utils/scanner/scan_factory.py`
- `src/pymodaq/utils/scanner/scanners/_1d_scanners.py`
- `src/pymodaq/extensions/daq_scan.py`

---

## 1. Vue d'Ensemble

### 1.1 Problème Résolu

**Context:** Pour effectuer des acquisitions automatisées sur plusieurs points (scans), il faut coordonner:
- Le mouvement d'un ou plusieurs actuateurs
- L'acquisition des détecteurs à chaque position
- La sauvegarde et visualisation des données

**Solution PyMoDAQ:** Un système de Scanner modulaire qui sépare:
1. **Le calcul des positions** (Scanner)
2. **L'orchestration du scan** (DAQScan)
3. **L'exécution** (Dashboard + Modules)

---

## 2. Architecture du Système de Scanner

### 2.1 Composants Principaux

```
┌────────────────────────────────────────────────────┐
│              DAQScan Extension                      │
│  Responsibility: Orchestrer l'exécution du scan    │
└──────────┬─────────────────────────────────────────┘
           │
           ├─── Scanner (configuration des positions)
           │    └── ScannerBase (implémentations)
           │
           ├─── ModulesManager (coordination)
           │    ├── Actuators: List[DAQ_Move]
           │    └── Detectors: List[DAQ_Viewer]
           │
           └─── H5Saver (persistence)

┌────────────────────────────────────────────────────┐
│                  Scanner                            │
│  Responsibility: Calculer les positions du scan    │
│  Rationale: Séparer calcul de l'exécution          │
└──────────┬─────────────────────────────────────────┘
           │
           └─── ScannerFactory
                └── ScannerBase (Abstract)
                    ├── Scan1D
                    │   ├── Linear
                    │   ├── Random
                    │   └── Sparse
                    ├── Scan2D
                    │   ├── Linear
                    │   ├── Spiral
                    │   └── Random
                    ├── TabularScanner
                    └── SequentialScanner
```

---

## 3. Scanner - Calcul des Positions

### 3.1 Classe Abstraite: ScannerBase

**Fichier:** `src/pymodaq/utils/scanner/scan_factory.py`

**Responsibility:** Définir le contrat pour calculer toutes les positions d'un scan avant son exécution.

**Rationale:** 
- Calcul préalable permet la validation
- Séparation du calcul et de l'exécution (SRP)
- Factory Pattern facilite l'extension (OCP)

---

### 3.2 Attributs Abstraits Obligatoires

```python
class ScannerBase(ScanParameterManager, metaclass=ABCMeta):
    """
    Tous les scanners doivent définir:
    """
    
    # Identifiants
    scan_type: str           # Ex: 'Scan1D', 'Scan2D', 'Tabular'
    scan_subtype: str        # Ex: 'Linear', 'Spiral', 'Random'
    
    # Configuration
    params: List[dict]       # Paramètres UI pour configurer le scan
    
    # Résultats calculés
    positions: np.ndarray    # Shape: (n_axes, n_steps)
                             # positions[axis_idx, step_idx] = position
    
    axes_unique: List[np.ndarray]  # Valeurs uniques pour chaque axe
    axes_indexes: np.ndarray       # Indexes dans axes_unique
    
    n_steps: int            # Nombre total de points
    n_axes: int             # Nombre d'actuateurs
    
    distribution: DataDistribution  # 'uniform' ou 'spread'
```

---

### 3.3 Structure des Positions

**Principe:** Le scanner calcule TOUTES les positions à l'avance dans un tableau numpy.

**Format:** `positions[axis_index, step_index]`

**Exemple - Scan 1D Linear:**
```python
# Scan de 0 à 1 avec step 0.2
# Positions calculées: [0, 0.2, 0.4, 0.6, 0.8, 1.0]

positions = np.array([[0, 0.2, 0.4, 0.6, 0.8, 1.0]])
# Shape: (1, 6)  → 1 axe, 6 steps

n_axes = 1
n_steps = 6
axes_unique = [np.array([0, 0.2, 0.4, 0.6, 0.8, 1.0])]
axes_indexes = np.array([[0, 1, 2, 3, 4, 5]])
```

**Exemple - Scan 2D Linear:**
```python
# X: 0 to 2, step 1  → [0, 1, 2]
# Y: 0 to 1, step 0.5 → [0, 0.5, 1]
# Total: 3 × 3 = 9 points

positions = np.array([
    [0, 1, 2, 0, 1, 2, 0, 1, 2],  # X positions
    [0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1]  # Y positions
])
# Shape: (2, 9)  → 2 axes, 9 steps

n_axes = 2
n_steps = 9
axes_unique = [
    np.array([0, 1, 2]),      # X unique values
    np.array([0, 0.5, 1])     # Y unique values
]
```

---

### 3.4 Méthodes Abstraites Obligatoires

#### 3.4.1 `set_scan()`

**Signature:**
```python
@abstractmethod
def set_scan(self):
    """Calculate all scan positions from settings."""
    pass
```

**Responsibility:** Calculer `positions`, `axes_unique`, `axes_indexes`, `n_steps` depuis les paramètres.

**Contrat:**
- Lire les paramètres depuis `self.settings`
- Calculer le tableau `self.positions`
- Appeler `self.get_info_from_positions()` pour calculer les attributs dérivés

**Exemple - Scan1D Linear:**
```python
def set_scan(self):
    # Lire les paramètres
    start = self.settings['start']
    stop = self.settings['stop']
    step = self.settings['step']
    
    # Calculer les positions
    self.positions = mutils.linspace_step(start, stop, step)
    # Result: 1D array [start, start+step, ..., stop]
    
    # Calculer les infos dérivées
    self.get_info_from_positions(self.positions)
```

---

#### 3.4.2 `evaluate_steps()`

**Signature:**
```python
@abstractmethod
def evaluate_steps(self) -> int:
    """Quick evaluation of number of steps without full calculation."""
    pass
```

**Responsibility:** Estimer rapidement le nombre de points AVANT de calculer toutes les positions.

**Rationale:** Permet de valider qu'on ne dépasse pas les limites configurées.

**Exemple:**
```python
def evaluate_steps(self) -> int:
    # Estimation rapide sans calculer toutes les positions
    n_steps = int(np.abs((self.settings['stop'] - self.settings['start']) / 
                         self.settings['step']) + 1)
    return n_steps
```

---

#### 3.4.3 `set_units()`

**Signature:**
```python
@abstractmethod
def set_units(self):
    """Update settings units depending on actuators."""
    pass
```

**Responsibility:** Mettre à jour les unités affichées dans l'UI selon les actuateurs.

**Exemple:**
```python
def set_units(self):
    # Afficher les unités de l'actuateur si display_units=True
    for child in self.settings.children():
        child.setOpts(
            suffix='' if not self.display_units else self.actuators[0].units
        )
```

---

#### 3.4.4 `get_nav_axes()`

**Signature:**
```python
@abstractmethod
def get_nav_axes(self) -> List[Axis]:
    """Return axes for Navigator (visualization)."""
    pass
```

**Responsibility:** Créer les objets Axis pour la visualisation dans le Navigator.

**Exemple - Scan 1D:**
```python
def get_nav_axes(self) -> List[Axis]:
    return [Axis(
        label=f'{self.actuators[0].title}',
        units=f'{self.actuators[0].units}',
        data=np.squeeze(self.positions)
    )]
```

---

### 3.5 Méthodes Utilitaires Fournies

#### `get_info_from_positions(positions)`

Calcule automatiquement:
- `self.n_steps`
- `self.axes_unique`
- `self.axes_indexes`

**Usage:**
```python
def set_scan(self):
    self.positions = calculate_my_positions()
    self.get_info_from_positions(self.positions)  # Fait le reste !
```

---

## 4. Types de Scanners Implémentés

### 4.1 Scans 1D

#### Scan1D Linear

**Fichier:** `scanners/_1d_scanners.py`

**Configuration:**
```python
params = [
    {'title': 'Start:', 'name': 'start', 'type': 'float', 'value': 0.},
    {'title': 'Stop:', 'name': 'stop', 'type': 'float', 'value': 1.},
    {'title': 'Step:', 'name': 'step', 'type': 'float', 'value': 0.1}
]
```

**Algorithme:**
```python
positions = linspace_step(start, stop, step)
# Exemple: start=0, stop=1, step=0.2 → [0, 0.2, 0.4, 0.6, 0.8, 1.0]
```

---

#### Scan1D Random

**Variante:** Même que Linear mais shuffle les positions après calcul.

```python
positions = linspace_step(start, stop, step)
np.random.shuffle(positions)
```

---

#### Scan1D Sparse

**Configuration:**
```python
params = [
    {'title': 'Parsed string:', 'name': 'parsed_string', 
     'type': 'text', 'value': '0:0.1:1'}
]
```

**Syntaxe:**
- `start:step:stop` → range linéaire
- `value` → point unique
- Séparer par `,` ou nouvelle ligne

**Exemples:**
- `0:0.2:1` → `[0, 0.2, 0.4, 0.6, 0.8, 1.0]`
- `0:0.2:1,5` → `[0, 0.2, 0.4, 0.6, 0.8, 1.0, 5]`
- `0:0.2:1,5:1:7` → `[0, 0.2, 0.4, 0.6, 0.8, 1.0, 5, 6, 7]`

---

### 4.2 Scans 2D

#### Scan2D Linear

**Configuration:**
```python
params = [
    {'title': 'Start axis 1:', 'name': 'start_axis_1', ...},
    {'title': 'Stop axis 1:', 'name': 'stop_axis_1', ...},
    {'title': 'Step axis 1:', 'name': 'step_axis_1', ...},
    {'title': 'Start axis 2:', 'name': 'start_axis_2', ...},
    {'title': 'Stop axis 2:', 'name': 'stop_axis_2', ...},
    {'title': 'Step axis 2:', 'name': 'step_axis_2', ...},
]
```

**Pattern:** Grille rectangulaire (mesh grid)

```
(0,2) ---- (1,2) ---- (2,2)
  |          |          |
(0,1) ---- (1,1) ---- (2,1)
  |          |          |
(0,0) ---- (1,0) ---- (2,0)
```

---

#### Scan2D Spiral

**Pattern:** Spirale partant du centre

---

### 4.3 Tabular Scanner

**Fichier:** `scanners/tabular.py`

**Concept:** Positions définies dans un tableau éditable.

**Usage:** Quand les positions ne suivent pas un pattern régulier.

**Exemple:**
```
Step | Axis1 | Axis2 | Axis3
-----|-------|-------|-------
  0  |  0.0  |  1.5  |  0.0
  1  |  0.5  |  2.0  |  0.1
  2  |  1.0  |  1.0  |  0.3
```

---

### 4.4 Sequential Scanner

**Concept:** Enchaîner plusieurs scans différents.

**Usage:** 
- Scan rapide puis scan fin
- Différentes régions d'intérêt

---

## 5. ScannerFactory - Pattern Factory

### 5.1 Enregistrement

**Mécanisme:**
```python
@ScannerFactory.register()
class Scan1DLinear(Scan1DBase):
    scan_type = 'Scan1D'
    scan_subtype = 'Linear'
    ...
```

**Effet:**
- Auto-enregistre le scanner
- Disponible via `scanner_factory.get('Scan1D', 'Linear')`

---

### 5.2 Utilisation

```python
from pymodaq.utils.scanner.scan_factory import ScannerFactory

factory = ScannerFactory()

# Lister les types disponibles
scan_types = factory.scan_types()  
# → ['Scan1D', 'Scan2D', 'Tabular', 'Sequential']

subtypes = factory.scan_sub_types('Scan1D')
# → ['Linear', 'Random', 'Sparse']

# Créer un scanner
scanner = factory.get(
    'Scan1D', 
    'Linear', 
    actuators=[my_actuator],
    display_units=True
)
```

---

## 6. Classe Scanner - Wrapper UI

**Fichier:** `src/pymodaq/utils/scanner/scanner.py`

**Responsibility:** Interface utilisateur pour configurer un scanner et gérer son cycle de vie.

**Rationale:** Séparer la logique de calcul (ScannerBase) de la gestion UI (Scanner).

---

### 6.1 Attributs Principaux

```python
class Scanner(QObject, ParameterManager):
    scanner_updated_signal = Signal()
    
    def __init__(self, parent_widget, actuators):
        self._scanner: ScannerBase = None  # Instance du scanner concret
        self.actuators: List[DAQ_Move] = actuators
```

---

### 6.2 Workflow

```
1. User sélectionne actuateurs
   ↓
2. User choisit scan_type et scan_subtype
   ↓
3. Scanner crée l'instance ScannerBase via Factory
   ↓
4. User configure les paramètres (start, stop, step, etc.)
   ↓
5. User clique "Calculate positions"
   ↓
6. scanner.set_scan() → calcule toutes les positions
   ↓
7. Positions disponibles via scanner.positions
```

---

### 6.3 Méthodes Principales

#### `set_scanner()`
Crée l'instance ScannerBase via la Factory

#### `set_scan()`
Lance le calcul des positions

#### `get_scan_info() -> ScanInfo`
Retourne un objet résumant le scan:
```python
ScanInfo(
    Nsteps=100,
    positions=positions_array,
    axes_indexes=indexes_array,
    axes_unique=[unique_values_axis1, unique_values_axis2],
    selected_actuators=['X', 'Y']
)
```

#### `positions_at(index) -> DataToExport`
Extrait les positions des actuateurs pour un step donné.

---

## 7. Intégration avec DAQScan

**Fichier:** `src/pymodaq/extensions/daq_scan.py`

### 7.1 Utilisation du Scanner

```python
class DAQScan:
    def __init__(self, dashboard):
        # Créer le scanner
        self.scanner = Scanner(
            actuators=self.modules_manager.actuators
        )
        
        # Connecter les signaux
        self.scanner.scanner_updated_signal.connect(self.prepare_scan)
    
    def run_scan(self):
        # Obtenir les infos du scan
        scan_info = self.scanner.get_scan_info()
        n_steps = scan_info.Nsteps
        
        # Pour chaque point
        for step_index in range(n_steps):
            # 1. Obtenir les positions cibles
            target_positions = self.scanner.positions_at(step_index)
            
            # 2. Déplacer les actuateurs
            self.move_actuators(target_positions)
            
            # 3. Attendre fin de mouvement
            self.wait_move_done()
            
            # 4. Acquérir les données
            data = self.grab_detectors()
            
            # 5. Sauvegarder
            self.save_data(step_index, target_positions, data)
```

---

## 8. Flux Complet d'un Scan

```
┌─────────────────────────────────────────────────┐
│ 1. Configuration (User)                         │
│    - Sélectionner actuateurs                    │
│    - Choisir scan type/subtype                  │
│    - Configurer paramètres                      │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 2. Calcul Positions (Scanner)                   │
│    - scanner.set_scan()                         │
│    - Calcul du tableau positions[axes, steps]   │
│    - Validation nombre de steps                 │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 3. Lancement Scan (DAQScan)                     │
│    FOR step_index in range(n_steps):            │
│      a. Lire positions[step_index]              │
│      b. Déplacer actuateurs                     │
│      c. Attendre move_done_signal               │
│      d. Trigger acquisition (grab())            │
│      e. Attendre grab_done_signal               │
│      f. Sauvegarder données (H5Saver)           │
│      g. Afficher (Navigator)                    │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│ 4. Sauvegarde Finale                            │
│    - Fermeture fichier HDF5                     │
│    - Métadonnées du scan                        │
└─────────────────────────────────────────────────┘
```

---

## 9. Créer un Scanner Personnalisé

### 9.1 Template

```python
from pymodaq.utils.scanner.scan_factory import ScannerBase, ScannerFactory
from pymodaq_data.data import Axis, DataDistribution
import numpy as np

@ScannerFactory.register()
class ScanCustom(ScannerBase):
    """My custom scanner pattern."""
    
    # Obligatoire: identifiants
    scan_type = 'Custom'
    scan_subtype = 'MyPattern'
    
    # Obligatoire: nombre d'axes
    n_axes = 2  # ou 1, 3, etc.
    
    # Obligatoire: distribution
    distribution = DataDistribution['uniform']  # ou 'spread'
    
    # Obligatoire: paramètres UI
    params = [
        {'title': 'Param1:', 'name': 'param1', 'type': 'float', 'value': 0.},
        {'title': 'Param2:', 'name': 'param2', 'type': 'int', 'value': 10},
    ]
    
    def __init__(self, actuators=None, display_units=True, **_ignored):
        super().__init__(actuators=actuators, display_units=display_units)
    
    def set_scan(self):
        """Calculate positions based on params."""
        # Lire params
        param1 = self.settings['param1']
        param2 = self.settings['param2']
        
        # Calculer positions
        # Shape DOIT être (n_axes, n_steps)
        x_positions = ... # array of length n_steps
        y_positions = ... # array of length n_steps
        
        self.positions = np.array([x_positions, y_positions])
        
        # Calcul automatique des attributs dérivés
        self.get_info_from_positions(self.positions)
    
    def evaluate_steps(self) -> int:
        """Quick estimate of number of steps."""
        # Estimation rapide SANS calculer toutes les positions
        return self.settings['param2']
    
    def set_units(self):
        """Set units on parameters."""
        for child in self.settings.children():
            # Utiliser les unités des actuateurs si display_units=True
            if child.name() == 'param1':
                child.setOpts(suffix='' if not self.display_units 
                             else self.actuators[0].units)
    
    def get_nav_axes(self) -> List[Axis]:
        """Return axes for Navigator."""
        return [
            Axis(label=f'{self.actuators[0].title}',
                 units=f'{self.actuators[0].units}',
                 data=self.positions[0]),
            Axis(label=f'{self.actuators[1].title}',
                 units=f'{self.actuators[1].units}',
                 data=self.positions[1])
        ]
```

---

## 10. Analyse SOLID du Système Scanner

### 10.1 Single Responsibility Principle ✅

**Respect:** ÉLEVÉ

- **ScannerBase:** Calcul des positions uniquement
- **Scanner:** Gestion UI et lifecycle uniquement  
- **DAQScan:** Orchestration scan uniquement
- **Factory:** Création d'instances uniquement

**Observation:** Séparation très claire des responsabilités.

---

### 10.2 Open/Closed Principle ✅

**Respect:** ÉLEVÉ

- Ajout de nouveaux types de scans via héritage et `@register()`
- Aucune modification du code existant nécessaire
- Factory Pattern facilite l'extensibilité

**Observation:** Système conçu pour l'extension.

---

### 10.3 Liskov Substitution Principle ✅

**Respect:** ÉLEVÉ

- Tous les scanners respectent le contrat `ScannerBase`
- Substitution transparente via la Factory
- Pas de violations détectées

---

### 10.4 Interface Segregation Principle ✅

**Respect:** ÉLEVÉ

- Interface minimale et cohérente
- Méthodes abstraites nécessaires et suffisantes
- Pas de méthodes inutiles imposées

---

### 10.5 Dependency Inversion Principle ✅

**Respect:** ÉLEVÉ

- DAQScan dépend de l'abstraction `Scanner`
- Scanner dépend de l'abstraction `ScannerBase`
- Pas de dépendance vers des implémentations concrètes

---

## 11. Pertinence pour AEFI_Acquisition

### 11.1 Cas d'Usage AEFI

**Besoin:** Scan rotatif du moteur Arcus Performax avec acquisition multi-points.

**Correspondance:**
- **Scan1D Linear** : parfait pour rotation incrémentale
- **Scan1D Sparse** : utile pour angles spécifiques non réguliers
- **TabularScanner** : si positions calculées depuis un algorithme externe

---

### 11.2 Utilisation Directe

✅ **Le système de Scanner est DIRECTEMENT utilisable pour AEFI**

**Pas besoin de créer un scanner custom** SAUF si:
- Pattern de scan très spécifique (spiral, adaptatif, etc.)
- Calcul de positions externe (MATLAB, algorithme spécifique)

**Recommandation:** Utiliser `Scan1D Linear` tel quel pour commencer.

---

### 11.3 Si Scanner Personnalisé Nécessaire

**Exemple - Scan Rotatif Optimisé:**

```python
@ScannerFactory.register()
class ScanRotational(Scan1DBase):
    """Rotational scan with acceleration profiles."""
    
    scan_subtype = 'Rotational'
    
    params = [
        {'title': 'Start angle (deg):', 'name': 'start_angle', 
         'type': 'float', 'value': 0.},
        {'title': 'Stop angle (deg):', 'name': 'stop_angle', 
         'type': 'float', 'value': 360.},
        {'title': 'Angular step (deg):', 'name': 'angular_step', 
         'type': 'float', 'value': 10.},
        {'title': 'Optimize trajectory:', 'name': 'optimize', 
         'type': 'bool', 'value': True},
    ]
    
    def set_scan(self):
        start = self.settings['start_angle']
        stop = self.settings['stop_angle']
        step = self.settings['angular_step']
        
        # Positions de base
        positions = np.arange(start, stop + step, step)
        
        # Optimisation optionnelle
        if self.settings['optimize']:
            positions = self.optimize_trajectory(positions)
        
        self.positions = positions
        self.get_info_from_positions(self.positions)
    
    def optimize_trajectory(self, positions):
        """Optimize for minimum back-and-forth."""
        # Votre algorithme d'optimisation
        return positions
```

---

## 12. Conclusion

**Architecture Scanner:** Excellente séparation des responsabilités

**Conformité SOLID:** TRÈS ÉLEVÉE (5/5)

**Extensibilité:** Factory Pattern rend l'ajout de nouveaux scanners trivial

**Recommandation AEFI:**
1. ✅ Utiliser `Scan1D Linear` pour scans rotatifs standard
2. ✅ Créer un scanner custom SEULEMENT si nécessaire
3. ✅ Le système est prêt à l'emploi pour vos besoins

---

## 13. Prochaines Étapes

1. ✅ Système Scanner bien compris
2. → Créer plugins pour matériel AEFI
3. → Utiliser DAQScan tel quel
4. → Si besoin: créer scanner custom pour patterns spécifiques


