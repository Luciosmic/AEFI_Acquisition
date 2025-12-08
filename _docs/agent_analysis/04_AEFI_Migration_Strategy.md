# AEFI_Acquisition - Stratégie de Migration vers PyMoDAQ

**Date:** 2025-11-16  
**Context:** Migration de Legacy_AEFI_Acquisition vers une architecture basée sur PyMoDAQ  
**Objectif:** Construire un logiciel d'acquisition respectant SOLID, DDD et ADD

---

## 1. Analyse du Legacy AEFI_Acquisition

### 1.1 Structure Actuelle

```
Legacy_AEFI_Acquisition/
├── Agilent_DSOX2014/           # Contrôleur oscilloscope
├── ArcusPerformaxPythonController/  # Contrôleur moteur rotatif
├── LSM9D/                      # Contrôleur IMU
├── narda_probe/                # Contrôleur sonde Narda
├── getE3D/                     # Logique métier E-field avec Contrôleur E-Sensor et E-generator
├── EFImagingBench_App/         # Application principale
│   └── src/                    # Interface + orchestration
└── matlab_scripts/             # Algorithmes de calcul
```

---

### 1.2 Problèmes Identifiés

#### Architecture Bottom-Up (Problème Principal)

**Problème:** Le logiciel a été construit **en partant des contrôleurs** (couche basse) vers l'application (couche haute).

**Conséquences:**
- ❌ Violations de DIP (Dependency Inversion Principle)
- ❌ Couplage fort entre UI et hardware
- ❌ Logique métier dispersée dans les contrôleurs
- ❌ Difficile à tester unitairement
- ❌ Rigidité: changement de matériel = refonte majeure

**Exemple de violation DIP:**
```python
# MAUVAIS (Legacy)
class AcquisitionApp:
    def __init__(self):
        self.motor = ArcusPerformaxController()  # Dépendance concrète
        self.scope = AgilentDSOX2014()          # Dépendance concrète
        
    def run_scan(self):
        self.motor.move_to(angle)  # Appel direct au hardware
        self.scope.acquire()       # Appel direct au hardware
```

---

#### Logique d'Orchestration Non Réutilisable

**Problème:** Chaque application réimplémente:
- Gestion des scans multi-points
- Coordination actuateurs/détecteurs
- Sauvegarde des données
- Visualisation temps réel

**Impact:** 
- Duplication de code
- Bugs répétés
- Maintenance difficile

---

### 1.3 Points Forts à Conserver

✅ **Drivers matériels fonctionnels**
- `ArcusPerformaxPythonController` : contrôle moteur
- `Agilent_DSOX2014` : acquisition oscilloscope
- `narda_probe` : lecture sonde Narda
- `LSM9D` : IMU

✅ **Logique métier E-field (getE3D)**
- Algorithmes de calcul du champ électrique
- À isoler dans un module séparé

✅ **Algorithmes MATLAB**
- Calculs validés scientifiquement
- À intégrer comme post-traitement

---

## 2. Architecture Cible avec PyMoDAQ

### 2.1 Principe de Construction Top-Down

**Approche PyMoDAQ:** Construire **du haut vers le bas**

```
1. Domaine métier (Application Layer)
   ↓ dépend de
2. Abstractions (Control Modules)
   ↓ dépend de
3. Plugins (Adapters)
   ↓ dépend de
4. Hardware (Infrastructure)
```

**Avantages:**
- ✅ Respecte DIP
- ✅ Logique métier indépendante du hardware
- ✅ Testable par couches
- ✅ Changement de matériel = nouveau plugin uniquement

---

### 2.2 Architecture Cible AEFI

```
┌────────────────────────────────────────────────────────┐
│           AEFI Application Layer                        │
│                                                         │
│  - AEFI_Dashboard (preset AEFI)                        │
│  - AEFI_Scan (scan rotatif + acquisition)             │
│  - AEFI_Analysis (post-traitement E-field)             │
└──────────────────┬─────────────────────────────────────┘
                   │ utilise (via abstractions)
                   │
┌──────────────────▼─────────────────────────────────────┐
│          PyMoDAQ Control Modules                        │
│  (Framework - À RÉUTILISER tel quel)                   │
│                                                         │
│  - Dashboard                                            │
│  - DAQ_Scan                                            │
│  - DAQ_Move (actuators)                                │
│  - DAQ_Viewer (detectors)                              │
│  - Scanner (multi-point patterns)                      │
│  - H5Saver (data persistence)                          │
└──────────────────┬─────────────────────────────────────┘
                   │ utilise (via plugin interfaces)
                   │
┌──────────────────▼─────────────────────────────────────┐
│        AEFI Plugins (À CRÉER)                          │
│  Package: pymodaq_plugins_aefi                         │
│                                                         │
│  - daq_move_ArcusPerformax      (rotation)            │
│  - daq_1Dviewer_AgilentDSOX2014 (oscilloscope)        │
│  - daq_0Dviewer_NardaEP601      (E-field probe)       │
│  - daq_0Dviewer_LSM9DS1         (IMU - optionnel)     │
└──────────────────┬─────────────────────────────────────┘
                   │ utilise
                   │
┌──────────────────▼─────────────────────────────────────┐
│      Hardware Drivers (RÉUTILISER Legacy)              │
│                                                         │
│  - ArcusPerformaxController (Legacy)                   │
│  - AgilentDSOX2014 (Legacy)                            │
│  - NardaEP601 (Legacy)                                 │
│  - LSM9DS1 (Legacy)                                    │
└────────────────────────────────────────────────────────┘
```

---

## 3. Plan de Migration

### 3.1 Phase 1: Création du Package de Plugins

#### Étape 1.1: Structure du package

```bash
mkdir -p pymodaq_plugins_aefi/src/pymodaq_plugins_aefi
cd pymodaq_plugins_aefi
```

**Structure:**
```
pymodaq_plugins_aefi/
├── pyproject.toml              # Configuration package
├── README.md
├── src/
│   └── pymodaq_plugins_aefi/
│       ├── __init__.py
│       │
│       ├── hardware/           # Drivers Legacy (réutilisés)
│       │   ├── __init__.py
│       │   ├── arcus_performax.py      # Copie de Legacy
│       │   ├── agilent_dsox2014.py     # Copie de Legacy
│       │   ├── narda_ep601.py          # Copie de Legacy
│       │   └── lsm9ds1.py              # Copie de Legacy
│       │
│       ├── daq_move_ArcusPerformax.py  # Plugin PyMoDAQ
│       ├── daq_1Dviewer_AgilentDSOX2014.py
│       ├── daq_0Dviewer_NardaEP601.py
│       └── daq_0Dviewer_LSM9DS1.py
│
└── tests/                      # Tests unitaires
    ├── test_arcus_plugin.py
    ├── test_agilent_plugin.py
    └── ...
```

---

#### Étape 1.2: Configuration pyproject.toml

```toml
[project]
name = "pymodaq_plugins_aefi"
version = "0.1.0"
description = "PyMoDAQ plugins for AEFI acquisition bench"
authors = [
    {name = "Luis", email = "your.email@example.com"}
]
dependencies = [
    "pymodaq>=5.0.0",
    "numpy",
    "pyvisa",  # Pour oscilloscope
    "pyserial",  # Pour Narda probe
]

[project.entry-points."pymodaq.instruments"]
aefi = "pymodaq_plugins_aefi"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

### 3.2 Phase 2: Création des Plugins

#### Plugin 1: Moteur Rotatif (Arcus Performax)

**Fichier:** `daq_move_ArcusPerformax.py`

```python
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    DataActuator,
    comon_parameters_fun,
)
from pymodaq_plugins_aefi.hardware.arcus_performax import ArcusPerformaxController

class DAQ_Move_ArcusPerformax(DAQ_Move_base):
    """
    PyMoDAQ plugin for Arcus Performax rotation motor.
    
    Responsibility: Provide standardized interface for rotational motor control.
    Rationale: Abstract hardware details to allow PyMoDAQ orchestration.
    """
    
    _controller_units = "deg"  # Unités par défaut
    is_multiaxes = False       # Un seul axe
    
    params = [
        {'title': 'COM Port:', 'name': 'com_port', 'type': 'str', 'value': 'COM3'},
        {'title': 'Baudrate:', 'name': 'baudrate', 'type': 'int', 'value': 9600},
        {'title': 'Speed (deg/s):', 'name': 'speed', 'type': 'float', 'value': 10.0},
        {'title': 'Acceleration (deg/s²):', 'name': 'accel', 'type': 'float', 'value': 50.0},
    ] + comon_parameters_fun(is_multiaxes, [], master=True)
    
    def ini_attributes(self):
        """Initialize plugin attributes."""
        self.controller: ArcusPerformaxController = None
    
    def ini_stage(self, controller=None):
        """Initialize hardware connection.
        
        Preconditions: COM port available
        Postconditions: Controller connected and configured
        """
        if controller is None:
            # Master mode: create controller
            self.controller = ArcusPerformaxController()
            self.controller.connect(
                port=self.settings['com_port'],
                baudrate=self.settings['baudrate']
            )
            
            # Configure motion parameters
            self.controller.set_speed(self.settings['speed'])
            self.controller.set_acceleration(self.settings['accel'])
            
            # Home if needed
            if self.settings['main_settings', 'move_home']:
                self.controller.home()
            
            info = f"Connected to Arcus Performax on {self.settings['com_port']}"
            initialized = True
        else:
            # Slave mode (shouldn't happen for single-axis motor)
            self.controller = controller
            info = "Using shared controller"
            initialized = True
        
        return info, initialized
    
    def get_actuator_value(self):
        """Read current angle from motor.
        
        Returns: Current position in degrees
        """
        position_deg = self.controller.get_position()
        
        self.current_value = DataActuator(
            data=position_deg,
            units=self.units
        )
        
        self.emit_value(self.current_value)
        return self.current_value
    
    def move_abs(self, value):
        """Move to absolute angle.
        
        Preconditions: Motor initialized, value within bounds
        Postconditions: Motor at target angle
        """
        value = self.check_bound(DataActuator(data=float(value)))
        self.target_value = value
        
        # Send command to hardware
        self.controller.move_absolute(value['data'])
        
        # Wait for motion done (bloquant)
        self.poll_moving()
    
    def move_rel(self, value):
        """Move relative to current position."""
        current = self.get_actuator_value()
        target = current['data'] + float(value)
        self.move_abs(target)
    
    def move_home(self):
        """Home the motor."""
        self.controller.home()
        self.emit_status(ThreadCommand('Update_Status', ['Homing complete']))
        self.move_done()
    
    def stop_motion(self):
        """Emergency stop."""
        self.controller.stop()
        self.move_done()
    
    def close(self):
        """Close hardware connection."""
        if self.controller is not None:
            self.controller.disconnect()
    
    def commit_settings(self, param):
        """Update settings on the fly."""
        if param.name() == 'speed':
            self.controller.set_speed(param.value())
        elif param.name() == 'accel':
            self.controller.set_acceleration(param.value())
```

---

#### Plugin 2: Oscilloscope (Agilent DSOX2014)

**Fichier:** `daq_1Dviewer_AgilentDSOX2014.py`

```python
from pymodaq.control_modules.viewer_utility_classes import (
    DAQ_Viewer_base,
    main,
)
from pymodaq_data.data import DataFromPlugins, Axis as DataAxis
import numpy as np
from pymodaq_plugins_aefi.hardware.agilent_dsox2014 import AgilentDSOX2014

class DAQ_1DViewer_AgilentDSOX2014(DAQ_Viewer_base):
    """
    PyMoDAQ plugin for Agilent DSOX2014 Oscilloscope.
    
    Responsibility: Provide standardized interface for waveform acquisition.
    Rationale: Abstract oscilloscope communication for PyMoDAQ integration.
    """
    
    params = [
        {'title': 'VISA Address:', 'name': 'visa_address', 'type': 'str', 
         'value': 'USB0::0x0957::0x1798::MY54321234::INSTR'},
        {'title': 'Channel:', 'name': 'channel', 'type': 'list', 
         'limits': ['CH1', 'CH2', 'CH3', 'CH4'], 'value': 'CH1'},
        {'title': 'Timebase (s):', 'name': 'timebase', 'type': 'float', 'value': 1e-3},
        {'title': 'V/div:', 'name': 'v_per_div', 'type': 'float', 'value': 1.0},
        {'title': 'Coupling:', 'name': 'coupling', 'type': 'list', 
         'limits': ['AC', 'DC'], 'value': 'DC'},
    ]
    
    def ini_detector(self, controller=None):
        """Initialize oscilloscope connection.
        
        Preconditions: VISA instrument accessible
        Postconditions: Scope configured and ready
        """
        if controller is None:
            self.controller = AgilentDSOX2014()
            self.controller.connect(self.settings['visa_address'])
            
            # Configure channel
            channel = self.settings['channel']
            self.controller.set_channel(
                channel=channel,
                coupling=self.settings['coupling'],
                v_per_div=self.settings['v_per_div']
            )
            
            # Configure timebase
            self.controller.set_timebase(self.settings['timebase'])
            
            self.emit_status(ThreadCommand('ini_detector', 
                                          log='Oscilloscope initialized'))
        else:
            self.controller = controller
    
    def grab_data(self, Naverage=1, **kwargs):
        """Acquire waveform from oscilloscope.
        
        Returns: 1D waveform data with time axis
        """
        # Trigger acquisition
        self.controller.single()
        
        # Wait for acquisition
        self.controller.wait_operation_complete()
        
        # Read waveform
        channel = self.settings['channel']
        time_data, voltage_data = self.controller.get_waveform(channel)
        
        # Average if requested
        if Naverage > 1:
            voltage_data = self._average_waveforms(voltage_data, Naverage)
        
        # Create PyMoDAQ data object
        data = DataFromPlugins(
            name=f'Scope_{channel}',
            data=[np.array(voltage_data)],
            dim='Data1D',
            labels=[f'{channel} Voltage'],
            x_axis=DataAxis(
                data=np.array(time_data),
                label='Time',
                units='s'
            )
        )
        
        # Emit data (OBLIGATOIRE)
        self.emit_data(data)
    
    def _average_waveforms(self, data, Naverage):
        """Software averaging."""
        averaged = np.array(data)
        for _ in range(Naverage - 1):
            self.controller.single()
            self.controller.wait_operation_complete()
            _, voltage = self.controller.get_waveform(self.settings['channel'])
            averaged += np.array(voltage)
        return averaged / Naverage
    
    def stop(self):
        """Stop acquisition."""
        self.controller.stop()
    
    def close(self):
        """Close connection."""
        if self.controller is not None:
            self.controller.disconnect()
    
    def commit_settings(self, param):
        """Update settings dynamically."""
        if param.name() == 'timebase':
            self.controller.set_timebase(param.value())
        elif param.name() == 'v_per_div':
            self.controller.set_channel(
                channel=self.settings['channel'],
                v_per_div=param.value()
            )

if __name__ == '__main__':
    main(__file__)
```

---

#### Plugin 3: Sonde Narda (EP601)

**Fichier:** `daq_0Dviewer_NardaEP601.py`

```python
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base
from pymodaq_data.data import DataFromPlugins
import numpy as np
from pymodaq_plugins_aefi.hardware.narda_ep601 import NardaEP601

class DAQ_0DViewer_NardaEP601(DAQ_Viewer_base):
    """
    PyMoDAQ plugin for Narda EP-601 E-field probe.
    
    Responsibility: Provide standardized interface for E-field measurements.
    """
    
    params = [
        {'title': 'COM Port:', 'name': 'com_port', 'type': 'str', 'value': 'COM4'},
        {'title': 'Baudrate:', 'name': 'baudrate', 'type': 'int', 'value': 115200},
        {'title': 'Measurement:', 'name': 'measurement', 'type': 'list', 
         'limits': ['E-field (V/m)', 'Power Density (W/m²)'], 
         'value': 'E-field (V/m)'},
    ]
    
    def ini_detector(self, controller=None):
        if controller is None:
            self.controller = NardaEP601()
            self.controller.connect(
                port=self.settings['com_port'],
                baudrate=self.settings['baudrate']
            )
            self.emit_status(ThreadCommand('ini_detector', 
                                          log='Narda probe initialized'))
        else:
            self.controller = controller
    
    def grab_data(self, Naverage=1, **kwargs):
        """Read E-field or power density value."""
        
        # Read measurement
        if self.settings['measurement'] == 'E-field (V/m)':
            value = self.controller.read_efield()
            label = 'E-field'
            units = 'V/m'
        else:
            value = self.controller.read_power_density()
            label = 'Power Density'
            units = 'W/m²'
        
        # Software averaging
        if Naverage > 1:
            values = [value]
            for _ in range(Naverage - 1):
                if self.settings['measurement'] == 'E-field (V/m)':
                    values.append(self.controller.read_efield())
                else:
                    values.append(self.controller.read_power_density())
            value = np.mean(values)
        
        # Create data object
        data = DataFromPlugins(
            name='Narda',
            data=[np.array([value])],
            dim='Data0D',
            labels=[label]
        )
        
        self.emit_data(data)
    
    def stop(self):
        pass
    
    def close(self):
        if self.controller is not None:
            self.controller.disconnect()
```

---

### 3.3 Phase 3: Création du Preset AEFI

**Fichier:** `aefi_rotational_scan.xml` (dans config PyMoDAQ)

Le preset définit la configuration du Dashboard:
- Modules actuateurs (moteur de rotation)
- Modules détecteurs (oscilloscope + Narda)
- Layout de l'interface

**À créer via l'interface Dashboard → Save Preset**

---

### 3.4 Phase 4: Extension AEFI (Optionnel)

Si besoin de logique métier spécifique (calcul E-field 3D, etc.):

**Fichier:** `aefi_efield_analysis.py`

```python
from pymodaq.extensions.daq_scan import DAQScan
import numpy as np

class AEFI_EFieldAnalysis:
    """
    Extension pour analyse champ électrique 3D.
    
    Responsibility: Calculate 3D E-field from scan data.
    Rationale: Separate domain logic from acquisition.
    """
    
    def __init__(self, daq_scan: DAQScan):
        self.daq_scan = daq_scan
    
    def calculate_efield_3d(self, scan_data):
        """
        Calculate 3D E-field from rotational scan.
        
        Preconditions: scan_data contains angle + E-field measurements
        Postconditions: Returns 3D E-field vector
        """
        # Votre logique métier ici
        # Peut réutiliser getE3D du Legacy
        pass
```

---

## 4. Mapping Legacy → PyMoDAQ

| Composant Legacy | PyMoDAQ Équivalent | Action |
|-----------------|-------------------|--------|
| `ArcusPerformaxController` | `daq_move_ArcusPerformax` | Envelopper dans plugin |
| `AgilentDSOX2014` | `daq_1Dviewer_AgilentDSOX2014` | Envelopper dans plugin |
| `NardaEP601` | `daq_0Dviewer_NardaEP601` | Envelopper dans plugin |
| `LSM9DS1` | `daq_0Dviewer_LSM9DS1` | Envelopper dans plugin (optionnel) |
| `EFImagingBench_App` (orchestration) | `Dashboard + DAQScan` | **SUPPRIMER** (remplacé) |
| `getE3D` (logique E-field) | Extension `AEFI_EFieldAnalysis` | **EXTRAIRE** et isoler |
| `matlab_scripts` | Post-processing module | Intégrer comme traitement séparé |

---

## 5. Bénéfices de la Migration

### 5.1 Respect des Principes SOLID

| Principe | Avant (Legacy) | Après (PyMoDAQ) |
|----------|---------------|-----------------|
| **SRP** | ❌ Logique métier + hardware dans même classe | ✅ Plugins hardware séparés de l'orchestration |
| **OCP** | ❌ Changement matériel = refonte app | ✅ Nouveau plugin sans toucher au reste |
| **LSP** | ❌ Pas d'abstractions | ✅ Tous les plugins respectent interfaces |
| **ISP** | ❌ Interfaces trop larges | ✅ Interfaces minimales et ciblées |
| **DIP** | ❌ App dépend du hardware concret | ✅ App dépend d'abstractions |

---

### 5.2 Avantages Pratiques

✅ **Réutilisabilité**
- Orchestration scan fournie par PyMoDAQ
- Sauvegarde HDF5 automatique
- Visualisation temps réel

✅ **Testabilité**
- Plugins testables indépendamment
- Mock controllers pour tests unitaires
- CI/CD possible

✅ **Maintenabilité**
- Code isolé par responsabilité
- Documentation claire (Responsibility/Rationale)
- Évolution facilitée

✅ **Extensibilité**
- Ajout de nouveau matériel = nouveau plugin
- Pas de modification du core
- Extensions pour logique métier

---

## 6. Checklist de Migration

### Étape 1: Setup Initial
- [ ] Créer package `pymodaq_plugins_aefi`
- [ ] Configurer `pyproject.toml` avec entry points
- [ ] Copier drivers Legacy dans `hardware/`

### Étape 2: Plugin Actuateur
- [ ] Créer `daq_move_ArcusPerformax.py`
- [ ] Implémenter toutes les méthodes abstraites
- [ ] Tester standalone avec `if __name__ == '__main__':`
- [ ] Tests unitaires

### Étape 3: Plugins Détecteurs
- [ ] Créer `daq_1Dviewer_AgilentDSOX2014.py`
- [ ] Créer `daq_0Dviewer_NardaEP601.py`
- [ ] Optionnel: `daq_0Dviewer_LSM9DS1.py`
- [ ] Tester standalone
- [ ] Tests unitaires

### Étape 4: Intégration
- [ ] Installer package: `pip install -e pymodaq_plugins_aefi`
- [ ] Lancer Dashboard PyMoDAQ
- [ ] Vérifier plugins détectés
- [ ] Créer preset AEFI
- [ ] Tester scan simple

### Étape 5: Extension (Optionnel)
- [ ] Extraire logique métier `getE3D`
- [ ] Créer extension AEFI si nécessaire
- [ ] Intégration post-traitement MATLAB

### Étape 6: Documentation
- [ ] README du package
- [ ] Documentation plugins
- [ ] Guide utilisateur AEFI
- [ ] Exemples de scripts

---

## 7. Estimation Effort

| Phase | Durée Estimée | Priorité |
|-------|---------------|----------|
| Setup package | 2h | ⭐⭐⭐ |
| Plugin Arcus Performax | 1 jour | ⭐⭐⭐ |
| Plugin Agilent Scope | 1 jour | ⭐⭐⭐ |
| Plugin Narda Probe | 0.5 jour | ⭐⭐⭐ |
| Tests unitaires | 1 jour | ⭐⭐ |
| Intégration Dashboard | 0.5 jour | ⭐⭐⭐ |
| Extension E-field (optionnel) | 2-3 jours | ⭐ |
| Documentation | 1 jour | ⭐⭐ |
| **TOTAL** | **5-8 jours** | |

---

## 8. Risques et Mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Drivers Legacy incompatibles | Faible | Élevé | Tester standalone d'abord |
| Communication hardware échoue | Moyen | Élevé | Tests avec matériel réel dès début |
| Performance dégradée | Faible | Moyen | Benchmarking avant/après |
| Courbe d'apprentissage PyMoDAQ | Moyen | Moyen | Suivre tutoriels, exemples |

---

## 9. Prochaines Actions Immédiates

1. **Créer le package** `pymodaq_plugins_aefi`
2. **Copier les drivers** Legacy dans `hardware/`
3. **Commencer par plugin le plus simple** (Narda probe)
4. **Itérer**: Test → Fix → Next plugin

---

## 10. Conclusion

**Approach Legacy:** ❌ Bottom-Up (hardware → app)  
**Approach PyMoDAQ:** ✅ Top-Down (abstractions → plugins → hardware)

**Conformité SOLID:** TRÈS ÉLEVÉE avec PyMoDAQ

**Recommandation:** Migration complète vers PyMoDAQ pour bénéficier d'une architecture maintenable et extensible.

**ROI:** Le temps investi dans la migration sera rapidement rentabilisé par:
- Réduction du temps de développement futures features
- Facilité de maintenance
- Réutilisabilité du code
- Testabilité accrue

