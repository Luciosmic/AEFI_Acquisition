# PyMoDAQ - Système de Plugins et Contrats d'Interface

**Date d'analyse:** 2025-11-16  
**Fichiers analysés:**
- `src/pymodaq/control_modules/move_utility_classes.py` (DAQ_Move_base)
- `src/pymodaq/control_modules/viewer_utility_classes.py` (DAQ_Viewer_base)
- `src/pymodaq/utils/daq_utils.py` (get_instrument_plugins)

---

## 1. Vue d'Ensemble du Système de Plugins

### 1.1 Principe Fondamental

PyMoDAQ utilise un **système de plugins basé sur les entry points Python** qui permet :
- D'ajouter du nouveau matériel sans modifier le code du framework (OCP)
- De découvrir automatiquement les plugins installés
- De maintenir une interface uniforme pour tous les instruments

### 1.2 Types de Plugins

| Type Plugin | Entry Point | Base Class | Usage |
|------------|-------------|------------|-------|
| Actuateurs | `pymodaq.instruments` | `DAQ_Move_base` | Contrôle de moteurs, stages, etc. |
| Détecteurs 0D | `pymodaq.instruments` | `DAQ_Viewer_base` | Acquisition de scalaires |
| Détecteurs 1D | `pymodaq.instruments` | `DAQ_Viewer_base` | Acquisition de spectres |
| Détecteurs 2D | `pymodaq.instruments` | `DAQ_Viewer_base` | Acquisition d'images |
| Détecteurs ND | `pymodaq.instruments` | `DAQ_Viewer_base` | Acquisition multidimensionnelle |
| Scanners | `pymodaq.scanners` | `ScannerBase` | Patterns de scan personnalisés |
| Extensions | `pymodaq.extensions` | - | Extensions du Dashboard |

---

## 2. Plugins Actuateurs (DAQ_Move_base)

### 2.1 Contrat d'Interface

**Fichier:** `src/pymodaq/control_modules/move_utility_classes.py`

**Classe abstraite:** `DAQ_Move_base(QObject)`

**Responsibility:** Fournir une interface standardisée pour contrôler un actuateur (moteur, stage, rotation, etc.)

**Rationale:** Abstraire le contrôle du matériel permet de changer d'équipement sans modifier le code de haut niveau (DIP).

---

### 2.2 Attributs de Classe Requis

```python
class DAQ_Move_MyActuator(DAQ_Move_base):
    """
    Attributs obligatoires de classe:
    """
    
    # Définit si le contrôleur gère plusieurs axes
    is_multiaxes: bool = False  # ou True
    
    # Si is_multiaxes=True, définir les noms des axes
    _axis_names: Union[list, Dict[str, int]] = ['X', 'Y', 'Z']
    # ou {'X': 0, 'Y': 1, 'Z': 2}
    
    # Paramètres de configuration du plugin (affichés dans l'UI)
    params = [
        {'title': 'Port COM:', 'name': 'com_port', 'type': 'str', 'value': 'COM1'},
        {'title': 'Baudrate:', 'name': 'baudrate', 'type': 'int', 'value': 9600},
        # ... autres paramètres
    ]
```

---

### 2.3 Attributs d'Instance Requis

```python
def __init__(self, parent, params_state):
    super().__init__(parent, params_state)
    
    # Obligatoire: L'objet représentant le hardware
    self.controller: Optional[HardwareController] = None
    
    # Automatiquement fourni par la base class:
    # self.settings: Parameter  # paramètres courants
    # self.current_value: DataActuator  # position courante
    # self.target_value: DataActuator   # position cible
```

---

### 2.4 Méthodes Abstraites OBLIGATOIRES

#### 2.4.1 `ini_stage()`

**Signature:**
```python
@abstractmethod
def ini_stage(self, controller: Optional[HardwareController] = None) -> tuple[str, bool]:
    """Initialize the hardware controller.
    
    Parameters
    ----------
    controller: Optional[HardwareController]
        - None si mode Master (crée le contrôleur)
        - Objet existant si mode Slave (partage le contrôleur)
    
    Returns
    -------
    info: str
        Message d'information sur l'initialisation
    initialized: bool
        True si succès, False sinon
    """
    pass
```

**Responsibility:** Initialiser la communication avec le matériel.

**Contrat:**
- Si `controller is None` → créer et initialiser `self.controller`
- Si `controller` fourni → utiliser `self.controller = controller`
- Retourner un message et un booléen de succès
- Lever une exception si erreur critique

**Exemple:**
```python
def ini_stage(self, controller=None):
    if controller is None:
        # Mode Master: créer le contrôleur
        self.controller = MyHardwareController()
        self.controller.connect(
            port=self.settings['com_port'],
            baudrate=self.settings['baudrate']
        )
        info = f"Connected to {self.settings['com_port']}"
    else:
        # Mode Slave: partager le contrôleur
        self.controller = controller
        info = "Using shared controller"
    
    # Configuration initiale
    self.controller.enable()
    initialized = True
    
    return info, initialized
```

---

#### 2.4.2 `get_actuator_value()`

**Signature:**
```python
@abstractmethod
def get_actuator_value(self) -> DataActuator:
    """Read the current position from hardware.
    
    Returns
    -------
    DataActuator
        La position courante avec unités
    """
    pass
```

**Responsibility:** Lire la position actuelle du matériel.

**Contrat:**
- Lire la position du `self.controller`
- Mettre à jour `self.current_value`
- Retourner un `DataActuator` avec la position et les unités
- Émettre la valeur via `self.emit_value()`

**Exemple:**
```python
def get_actuator_value(self):
    # Lire la position du matériel
    position = self.controller.get_position()
    
    # Mettre à jour la valeur courante
    self.current_value = DataActuator(
        data=position,
        units=self.units  # fourni par la base class
    )
    
    # Émettre vers l'UI
    self.emit_value(self.current_value)
    
    return self.current_value
```

---

#### 2.4.3 `move_abs()` 

**Signature:**
```python
def move_abs(self, value: Union[float, DataActuator]):
    """Move to an absolute position.
    
    Parameters
    ----------
    value: Union[float, DataActuator]
        Position cible absolue
    """
    pass
```

**Responsibility:** Déplacer l'actuateur à une position absolue.

**Contrat:**
- Convertir `value` en position cible
- Vérifier les limites avec `self.check_bound()`
- Envoyer la commande au `self.controller`
- **Appeler `self.move_done()` à la fin**

**Exemple:**
```python
def move_abs(self, value):
    # Convertir en DataActuator si nécessaire
    value = DataActuator(data=float(value))
    
    # Vérifier les limites
    value = self.check_bound(value)
    
    # Envoyer au matériel
    self.controller.move_to(value['data'])
    
    # Attendre la fin du mouvement (bloquant ou non-bloquant)
    while not self.controller.is_motion_done():
        QThread.msleep(10)
    
    # OBLIGATOIRE: signaler la fin
    self.move_done()
```

---

#### 2.4.4 `move_rel()`

**Signature:**
```python
def move_rel(self, value: Union[float, DataActuator]):
    """Move to a relative position.
    
    Parameters
    ----------
    value: Union[float, DataActuator]
        Déplacement relatif
    """
    pass
```

**Contrat:** Similaire à `move_abs()` mais avec position relative.

**Exemple:**
```python
def move_rel(self, value):
    value = DataActuator(data=float(value))
    current = self.get_actuator_value()
    target = current['data'] + value['data']
    self.move_abs(target)
```

---

#### 2.4.5 `move_home()`

**Signature:**
```python
def move_home(self):
    """Move to home position."""
    pass
```

**Contrat:** Effectuer la procédure de homing du matériel.

---

#### 2.4.6 `stop_motion()`

**Signature:**
```python
@abstractmethod
def stop_motion(self):
    """Stop the current motion immediately."""
    pass
```

**Contrat:**
- Arrêter immédiatement le mouvement
- Appeler `self.move_done()`

**Exemple:**
```python
def stop_motion(self):
    self.controller.stop()
    self.move_done()
```

---

#### 2.4.7 `close()`

**Signature:**
```python
@abstractmethod
def close(self):
    """Close the hardware connection."""
    pass
```

**Contrat:** Fermer proprement la connexion matérielle.

**Exemple:**
```python
def close(self):
    if self.controller is not None:
        self.controller.disconnect()
```

---

### 2.5 Méthodes Utilitaires Fournies

#### `emit_status(status: ThreadCommand)`
Émettre un statut vers l'UI

#### `emit_value(pos: DataActuator)`
Émettre la position courante

#### `move_done(position: Optional[DataActuator] = None)`
**IMPORTANT:** À appeler à la fin de chaque mouvement

#### `check_bound(position: DataActuator) -> DataActuator`
Vérifier et clipper la position dans les limites

---

### 2.6 Signaux Disponibles

```python
# Dans la base class:
move_done_signal = Signal(DataActuator)  # Émis automatiquement par move_done()
```

---

### 2.7 Configuration Multi-Axes

Pour un contrôleur gérant plusieurs axes (ex: XYZ stage):

```python
class DAQ_Move_XYZStage(DAQ_Move_base):
    is_multiaxes = True
    _axis_names = {'X': 0, 'Y': 1, 'Z': 2}
    
    def __init__(self, parent, params_state):
        super().__init__(parent, params_state)
        # self.axis est fourni automatiquement par la base class
        # Contient l'identifiant de l'axe (0, 1 ou 2)
```

**Convention:**
- Un plugin **Master** crée le contrôleur
- Les plugins **Slave** partagent le même contrôleur
- Tous ont le même `controller_id` dans les settings

---

## 3. Plugins Détecteurs (DAQ_Viewer_base)

### 3.1 Contrat d'Interface

**Fichier:** `src/pymodaq/control_modules/viewer_utility_classes.py`

**Classe abstraite:** `DAQ_Viewer_base(QObject)`

**Responsibility:** Fournir une interface standardisée pour acquérir des données depuis un détecteur.

---

### 3.2 Attributs de Classe Requis

```python
class DAQ_0DViewer_MyDetector(DAQ_Viewer_base):
    """
    Le nom de classe DOIT commencer par:
    - DAQ_0DViewer_ pour scalaires
    - DAQ_1DViewer_ pour spectres
    - DAQ_2DViewer_ pour images
    - DAQ_NDViewer_ pour multidimensionnel
    """
    
    # Paramètres de configuration
    params = [
        {'title': 'Address:', 'name': 'address', 'type': 'str', 'value': '192.168.1.1'},
        {'title': 'Sampling Rate:', 'name': 'sample_rate', 'type': 'int', 'value': 1000},
        # ... autres paramètres
    ]
```

---

### 3.3 Méthodes Abstraites OBLIGATOIRES

#### 3.3.1 `ini_detector()`

**Signature:**
```python
@abstractmethod
def ini_detector(self, controller=None):
    """Initialize the detector hardware.
    
    Parameters
    ----------
    controller: Optional
        Contrôleur partagé si mode multi-détecteur
    
    Returns
    -------
    None
        Mais doit lever une exception si erreur
    """
    pass
```

**Responsibility:** Initialiser la communication avec le détecteur.

**Contrat:**
- Créer ou utiliser `self.controller`
- Configurer le matériel
- Initialiser `self.data_shape` si connu

**Exemple:**
```python
def ini_detector(self, controller=None):
    if controller is None:
        # Mode Master
        self.controller = MyDetectorController()
        self.controller.connect(self.settings['address'])
    else:
        # Mode Slave
        self.controller = controller
    
    # Configuration
    self.controller.set_sampling_rate(self.settings['sample_rate'])
    
    # Pour un détecteur 1D, définir la forme des données
    self.data_shape = (1024,)  # 1024 points
    
    self.emit_status(ThreadCommand('ini_detector', log='Detector initialized'))
```

---

#### 3.3.2 `grab_data()`

**Signature:**
```python
@abstractmethod
def grab_data(self, Naverage=1, **kwargs):
    """Acquire data from the detector.
    
    Parameters
    ----------
    Naverage: int
        Nombre de moyennes demandées (peut être ignoré si hardware averaging)
    **kwargs
        Arguments optionnels (live, wait_time, etc.)
    """
    pass
```

**Responsibility:** Acquérir les données du détecteur.

**Contrat:**
- Acquérir les données du `self.controller`
- Créer des objets `DataFromPlugins` (0D/1D/2D/ND)
- **Émettre via `self.emit_data(data)`**
- Gérer le moyennage si nécessaire

**Exemple pour détecteur 0D:**
```python
def grab_data(self, Naverage=1, **kwargs):
    # Acquérir depuis le matériel
    value = self.controller.read()
    
    # Créer l'objet de données
    data = DataFromPlugins(
        name='MyDetector',
        data=[np.array([value])],  # Liste de numpy arrays
        dim='Data0D',
        labels=['Voltage']
    )
    
    # Émettre les données (OBLIGATOIRE)
    self.emit_data(data)
```

**Exemple pour détecteur 1D:**
```python
def grab_data(self, Naverage=1, **kwargs):
    # Acquérir un spectre
    spectrum = self.controller.read_spectrum()
    
    # Créer l'objet avec axe X
    data = DataFromPlugins(
        name='Spectrum',
        data=[np.array(spectrum)],
        dim='Data1D',
        labels=['Intensity'],
        x_axis=DataAxis(
            data=np.linspace(0, 1000, len(spectrum)),
            label='Wavelength',
            units='nm'
        )
    )
    
    self.emit_data(data)
```

---

#### 3.3.3 `stop()`

**Signature:**
```python
@abstractmethod
def stop(self):
    """Stop the current acquisition."""
    pass
```

**Contrat:** Arrêter l'acquisition en cours.

---

#### 3.3.4 `close()`

**Signature:**
```python
@abstractmethod
def close(self):
    """Close the detector connection."""
    pass
```

---

### 3.4 Méthodes Optionnelles

#### `commit_settings(param)`
Appelée quand un paramètre change dans l'UI.

```python
def commit_settings(self, param):
    if param.name() == 'sample_rate':
        self.controller.set_sampling_rate(param.value())
```

#### `roi_select(roi_info, ind_viewer)`
Appelée quand une ROI est sélectionnée (détecteurs 2D).

---

### 3.5 Signaux Disponibles

```python
# Fournis par la base class (ne PAS redéfinir):
data_grabed_signal = Signal(list)  # Émis automatiquement par emit_data()
```

---

### 3.6 Mode Live

PyMoDAQ supporte deux modes d'acquisition:

**Mode Snap:** Acquisition unique
**Mode Live:** Acquisition continue

Pour supporter le mode live:

```python
class DAQ_1DViewer_MyDetector(DAQ_Viewer_base):
    live_mode_available = True  # Attribut de classe
    
    def grab_data(self, Naverage=1, live=False, **kwargs):
        if live:
            # Acquisition continue
            self.controller.start_continuous()
            while self.controller.data_available():
                data = self.controller.get_latest_data()
                self.emit_data(self.format_data(data))
                if kwargs.get('wait_time', 0) > 0:
                    QThread.msleep(kwargs['wait_time'])
        else:
            # Acquisition unique
            data = self.controller.acquire_once()
            self.emit_data(self.format_data(data))
```

---

## 4. Entry Points et Découverte

### 4.1 Configuration dans pyproject.toml

Pour créer un plugin PyMoDAQ, le fichier `pyproject.toml` doit contenir:

```toml
[project.entry-points."pymodaq.instruments"]
my_plugin = "pymodaq_plugins_myplugin"

# Optionnel: autres types d'extensions
[project.entry-points."pymodaq.scanners"]
my_scanner = "pymodaq_plugins_myplugin.scanners"
```

---

### 4.2 Structure de Package Recommandée

```
pymodaq_plugins_myplugin/
├── pyproject.toml
├── src/
│   └── pymodaq_plugins_myplugin/
│       ├── __init__.py
│       ├── daq_move_MyActuator.py      # Plugin actuateur
│       ├── daq_0Dviewer_MyDetector.py  # Plugin détecteur 0D
│       └── hardware/
│           └── my_hardware_driver.py   # Driver bas niveau
```

---

### 4.3 Découverte Automatique

Au démarrage, PyMoDAQ:

```python
# Dans __init__.py du framework:
get_instrument_plugins()  # Découvre tous les plugins

# Mécanisme:
discovered_plugins = get_entrypoints(group='pymodaq.instruments')
for entry in discovered_plugins:
    module = entry.load()  # Charge le module
    # Scanne pour les classes DAQ_Move_* et DAQ_*Viewer_*
```

---

## 5. Conformité SOLID des Plugins

### 5.1 Single Responsibility (SRP) ✅

**Respect:** ÉLEVÉ
- Chaque plugin = un instrument
- Séparation claire entre driver (controller) et plugin

### 5.2 Open/Closed (OCP) ✅

**Respect:** ÉLEVÉ
- Ajout de plugins sans modifier le framework
- Entry points permettent l'extension

### 5.3 Liskov Substitution (LSP) ✅

**Respect:** ÉLEVÉ
- Tous les plugins respectent leur contrat de base class
- Substitution transparente

### 5.4 Interface Segregation (ISP) ✅

**Respect:** ÉLEVÉ
- Interfaces minimales et ciblées
- Méthodes optionnelles clairement séparées

### 5.5 Dependency Inversion (DIP) ✅

**Respect:** ÉLEVÉ
- Framework dépend des abstractions (base classes)
- Pas de dépendance directe vers le matériel

---

## 6. Checklist pour Créer un Plugin

### Plugin Actuateur (DAQ_Move)

- [ ] Hériter de `DAQ_Move_base`
- [ ] Définir `is_multiaxes` et `_axis_names` si nécessaire
- [ ] Définir `params` pour la configuration
- [ ] Implémenter `ini_stage(controller=None)`
- [ ] Implémenter `get_actuator_value()`
- [ ] Implémenter `move_abs(value)`
- [ ] Implémenter `move_rel(value)`
- [ ] Implémenter `move_home()`
- [ ] Implémenter `stop_motion()`
- [ ] Implémenter `close()`
- [ ] Appeler `self.move_done()` après chaque mouvement
- [ ] Configurer entry point dans `pyproject.toml`

### Plugin Détecteur (DAQ_Viewer)

- [ ] Nommer la classe `DAQ_XDViewer_*` (X = 0, 1, 2 ou N)
- [ ] Hériter de `DAQ_Viewer_base`
- [ ] Définir `params` pour la configuration
- [ ] Implémenter `ini_detector(controller=None)`
- [ ] Implémenter `grab_data(Naverage=1, **kwargs)`
- [ ] Implémenter `stop()`
- [ ] Implémenter `close()`
- [ ] Appeler `self.emit_data()` dans `grab_data()`
- [ ] Optionnel: `commit_settings()` pour changements dynamiques
- [ ] Optionnel: `live_mode_available = True` si supporté
- [ ] Configurer entry point dans `pyproject.toml`

---

## 7. Prochaines Étapes pour AEFI_Acquisition

### 7.1 Plugins à Créer

1. **pymodaq_plugins_aefi**
   - `daq_move_ArcusPerformax` : contrôle du moteur rotatif
   - `daq_1Dviewer_AgilentDSOX2014` : acquisition oscilloscope
   - `daq_0Dviewer_NardaProbe` : acquisition sonde Narda
   - `daq_0Dviewer_LSM9DS1` : IMU (optionnel)

### 7.2 Réutilisation du Code Legacy

- ✅ Réutiliser les drivers bas niveau existants comme `controller`
- ✅ Envelopper dans les plugins PyMoDAQ
- ✅ Supprimer toute la logique d'orchestration (remplacée par Dashboard/DAQScan)

---

## 8. Conclusion

**Système de Plugins:** Très bien conçu, respecte les principes SOLID

**Contrats d'Interface:** Clairs et bien documentés

**Recommandation:** Créer des plugins AEFI en suivant les patterns établis plutôt que de réinventer l'orchestration.


