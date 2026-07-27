# Documentation Pylablib - Package Arcus

Source : https://pylablib.readthedocs.io/en/stable/.apidoc/pylablib.devices.Arcus.html

## Vue d'ensemble

Ce document présente la documentation complète du package `pylablib.devices.Arcus` pour le contrôle des platines de translation Arcus Performax.

---

## Informations pratiques sur get_full_info()

### Description
La méthode `get_full_info()` retourne un dictionnaire complet contenant toutes les informations de statut et configuration du contrôleur. Cette méthode est particulièrement utile pour diagnostiquer l'état du système.

### Exemple de sortie (Performax4EX)
```python
stage.get_full_info()
```

**Retourne :**
```python
{
    'limit_errors_enabled': False,                    # Erreurs de butée désactivées
    'enabled': [True, True, False, False],            # État activation par axe [X,Y,Z,U]
    'global_speed': 800,                              # Vitesse globale (Hz)
    'axis_speed': [0, 0, 0, 0],                      # Vitesse par axe (0 = utilise globale)
    'device_number': '4EX00',                        # Numéro du périphérique
    'baudrate': 9600,                                # Débit de communication
    'current_limit_errors': ['', '', '', ''],        # Erreurs de butée actuelles
    'position': [-15818, -27951, 0, 0],             # Positions actuelles en pulses
    'encoder': [0, 0, 0, 0],                        # Valeurs encodeur
    'current_speed': [0, 0, 0, 0],                  # Vitesses instantanées (Hz)
    'axis_status': [[], ['sw_minus_lim'], [], []],   # Statut par axe
    'moving': [False, False, False, False],          # État mouvement par axe
    'cls': 'Performax4EXStage',                      # Classe du contrôleur
    'conn': (0, None),                               # Info connexion (index, type)
    'axes': ['X', 'Y', 'Z', 'U'],                   # Noms des axes disponibles
    'device_info': (0, '4ex00', 'Performax USB', '...', '1589', 'a101')  # Info USB
}
```

### Interprétation des valeurs importantes

| Clé | Description | Valeurs possibles |
|-----|-------------|-------------------|
| `enabled` | État d'activation par axe | `[True/False, ...]` |
| `moving` | État de mouvement par axe | `[True/False, ...]` |
| `axis_status` | Statut détaillé par axe | `[]` = normal, `['sw_minus_lim']` = butée -, etc. |
| `current_limit_errors` | Erreurs de butée actives | `''` = pas d'erreur, `'+'` = butée +, `'-'` = butée - |
| `position` | Position actuelle en pulses | Entiers signés |
| `global_speed` | Vitesse globale en Hz | Entier positif |
| `axis_speed` | Vitesse par axe en Hz | `0` = utilise la vitesse globale |

---

## Sous-modules

### pylablib.devices.Arcus.base module

#### Exceptions

##### ArcusError
```python
exception pylablib.devices.Arcus.base.ArcusError
```
**Hérite de :** `DeviceError`

**Description :** Erreur générique Arcus

**Méthodes :**
- `add_note()` : Exception.add_note(note) – add a note to the exception
- `args`
- `with_traceback()` : Exception.with_traceback(tb) – set self.__traceback__ to tb and return self.

##### ArcusBackendError
```python
exception pylablib.devices.Arcus.base.ArcusBackendError(exc)
```
**Hérite de :** `ArcusError`, `DeviceBackendError`

**Description :** Erreur générique de communication backend Arcus

**Méthodes :**
- `add_note()` : Exception.add_note(note) – add a note to the exception
- `args`
- `with_traceback()` : Exception.with_traceback(tb) – set self.__traceback__ to tb and return self.

---

## pylablib.devices.Arcus.performax module

### Fonctions utilitaires

#### get_usb_device_info()
```python
pylablib.devices.Arcus.performax.get_usb_device_info(devid)
```
**Description :** Get info for the given device index (starting from 0).

**Retour :** tuple (index, serial, model, desc, vid, pid).

#### list_usb_performax_devices()
```python
pylablib.devices.Arcus.performax.list_usb_performax_devices()
```
**Description :** List all performax devices.

**Retour :** list of tuples (index, serial, model, desc, vid, pid), one per device.

---

## Classes principales

### GenericPerformaxStage

```python
class pylablib.devices.Arcus.performax.GenericPerformaxStage(idx=0, conn=None)
```
**Hérite de :** `IMultiaxisStage`

**Description :** Generic Arcus Performax translation stage.

#### Paramètres d'initialisation

| Paramètre | Type | Description |
|-----------|------|-------------|
| `idx` | int | stage index; if using a USB connection, specifies a USB device index; if using RS485 connection, specifies device index on the bus |
| `conn` | varies | if not None, defines a connection to RS485 connection. Usually (e.g., for USB-to-RS485 adapters) this is a serial connection, which either a name (e.g., "COM1"), or a tuple (name, baudrate) (e.g., ("COM1", 9600)); if conn is None, assume direct USB connection and use the manufacturer-provided DLL |

#### Attributs

| Attribut | Description |
|----------|-------------|
| `Error` | alias of ArcusError |

#### Méthodes de connexion

| Méthode | Description |
|---------|-------------|
| `open()` | Open the connection to the stage |
| `close()` | Close the connection to the stage |
| `is_opened()` | Check if the device is connected |

#### Méthodes d'information

| Méthode | Description |
|---------|-------------|
| `get_device_info()` | Get the device info |
| `query(comm)` | Send a query to the stage and return the reply |
| `get_device_number()` | Get the device number used in RS-485 communications. Usually it is a string with the format similar to "4EX00". |
| `set_device_number(number, store=True)` | Get the device number used in RS-485 communications. number can be either a full device id (e.g., "4EX00"), or a single number between 0 and 99. In order for the change to take effect, the device needs to be power-cycled. If store==True, automatically store settings to the memory; otherwise, the settings will be lost unless store_defaults() is called at some point before the power-cycle. |

#### Méthodes de configuration

| Méthode | Description |
|---------|-------------|
| `store_defaults()` | Store some of the settings to the memory as defaults. Applies to device number, baudrate, limit error behavior, polarity, and some other settings. |
| `apply_settings(settings)` | Apply the settings. settings is the dict {name: value} of the device available settings. Non-applicable settings are ignored. |

#### Méthodes d'axes

| Méthode | Description |
|---------|-------------|
| `get_all_axes()` | Get the list of all available axes (taking mapping into account) |
| `remap_axes(mapping, accept_original=True)` | Rename axes to the new labels. mapping is the new axes mapping, which can be a list of new axes name (corresponding to the old axes in order returned by get_all_axes()), or a dictionary {alias: original} of the new axes aliases. |

#### Méthodes de variables/paramètres

| Méthode | Description |
|---------|-------------|
| `get_device_variable(key)` | Get the value of a settings, status, or full info parameter |
| `set_device_variable(key, value)` | Set the value of a settings parameter |
| `get_full_info(include=0)` | Get dict {name: value} containing full device information (including status and settings). include specifies either a list of variables (only these variables are returned), a priority threshold (only values with the priority equal or higher are returned), or "all" (all available variables). Since the lowest priority is -10, setting include=-10 queries all available variables, which is equivalent to include="all". |
| `get_full_status(include=0)` | Get dict {name: value} containing the device status (including settings). include specifies either a list of variables (only these variables are returned), a priority threshold (only values with the priority equal or higher are returned), or "all" (all available variables). Since the lowest priority is -10, setting include=-10 queries all available variables, which is equivalent to include="all". |
| `get_settings(include=0)` | Get dict {name: value} containing all the device settings. include specifies either a list of variables (only these variables are returned), a priority threshold (only values with the priority equal or higher are returned), or "all" (all available variables). Since the lowest priority is -10, setting include=-10 queries all available variables, which is equivalent to include="all". |

---

### Performax4EXStage

```python
class pylablib.devices.Arcus.performax.Performax4EXStage(idx=0, conn=None, enable=True)
```
**Hérite de :** `GenericPerformaxStage`

**Description :** Arcus Performax 4EX/4ET translation stage.

#### Paramètres d'initialisation

| Paramètre | Type | Description |
|-----------|------|-------------|
| `idx` | int | stage index; if using a USB connection, specifies a USB device index; if using RS485 connection, specifies device index on the bus |
| `conn` | varies | if not None, defines a connection to RS485 connection. Usually (e.g., for USB-to-RS485 adapters) this is a serial connection, which either a name (e.g., "COM1"), or a tuple (name, baudrate) (e.g., ("COM1", 9600)); if conn is None, assume direct USB connection and use the manufacturer-provided DLL |
| `enable` | bool | if True, enable all axes on startup |

#### Méthodes de communication

| Méthode | Description |
|---------|-------------|
| `get_baudrate()` | Get current baud rate |
| `set_baudrate(baudrate, store=True)` | Set current baud rate. Acceptable values are 9600 (default), 19200, 38400, 57600, and 115200. In order for the change to take effect, the device needs to be power-cycled. If store==True, automatically store settings to the memory; otherwise, the settings will be lost unless store_defaults() is called at some point before the power-cycle. |

#### Méthodes de configuration

| Méthode | Description |
|---------|-------------|
| `enable_absolute_mode(enable=True)` | Set absolute motion mode |
| `enable_limit_errors(enable=True, autoclear=True)` | Enable limit errors. If on, reaching limit switch on an axis puts it into an error state, which immediately stops this an all other axes; any further motion command on this axis will raise an error (it is still possible to restart motion on other axes); the axis motion can only be resumed by calling clear_limit_error(). If off, the limited axis still stops, but the other axes are unaffected. If autoclear==True and enable==False, also clear the current limit errors on all exs. |
| `limit_errors_enabled()` | Check if global limit errors are enabled. If on, reaching limit switch on an axis puts it into an error state, which immediately stops this an all other axes; any further motion command on this axis will raise an error (it is still possible to restart motion on other axes); the axis motion can only be resumed by calling clear_limit_error(). If off, the limited axis still stops, but the other axes are unaffected. |

#### Méthodes d'activation des axes

| Méthode | Description |
|---------|-------------|
| `is_enabled(axis='all')` | Check if the axis output is enabled |
| `enable_axis(axis='all', enable=True)` | Enable axis output. If the output is disabled, the steps are generated by the controller, but not sent to the motors. |

#### Méthodes de position

| Méthode | Description |
|---------|-------------|
| `get_position(axis='all')` | Get the current axis pulse position |
| `set_position_reference(axis, position=0)` | Set the current axis pulse position as a reference. Re-calibrate the pulse position counter so that the current position is set as position (0 by default). |

#### Méthodes d'encodeur

| Méthode | Description |
|---------|-------------|
| `get_encoder(axis='all')` | Get the current axis encoder value |
| `set_encoder_reference(axis, position=0)` | Set the current axis encoder value as a reference. Re-calibrate the encoder counter so that the current position is set as position (0 by default). |

#### Méthodes de mouvement

| Méthode | Description |
|---------|-------------|
| `move_to(axis, position)` | Move a given axis to a given position |
| `move_by(axis, steps=1)` | Move a given axis for a given number of steps |
| `jog(axis, direction)` | Jog a given axis in a given direction. direction can be either "-" (negative) or "+" (positive). The motion continues until it is explicitly stopped, or until a limit is hit. |
| `stop(axis='all', immediate=False)` | Stop motion of a given axis. If immediate==True make an abrupt stop; otherwise, slow down gradually. |
| `home(axis, direction, home_mode)` | Home the given axis using a given home mode. direction can be "+" or "-" The mode can be "only_home_input", "only_home_input_lowspeed", "only_limit_input", "only_zidx_input", or "home_and_zidx_input". For meaning, see Arcus PMX manual. |

#### Méthodes de vitesse

| Méthode | Description |
|---------|-------------|
| `get_global_speed()` | Get the global speed setting (in Hz); overridden by a non-zero axis speed |
| `get_axis_speed(axis='all')` | Get the individual axis speed setting (in Hz); 0 means that the global speed is used |
| `set_global_speed(speed)` | Set the global speed setting (in Hz); overridden by a non-zero axis speed |
| `set_axis_speed(axis, speed)` | Set the individual axis speed setting (in Hz); 0 means that the global speed is used |
| `get_current_axis_speed(axis='all')` | Get the instantaneous speed (in Hz) |

#### Méthodes de statut et synchronisation

| Méthode | Description |
|---------|-------------|
| `get_status_n(axis='all')` | Get the axis status as an integer |
| `get_status(axis='all')` | Get the axis status as a set of string descriptors |
| `is_moving(axis='all')` | Check if a given axis is moving |
| `wait_move(axis, timeout=None, period=0.05)` | Wait until motion is done |

#### Méthodes de gestion des erreurs

| Méthode | Description |
|---------|-------------|
| `check_limit_error(axis='all')` | Check if the axis hit limit errors. Return "" (not errors), "+" (positive limit error) or "-" (negative limit error). |
| `clear_limit_error(axis='all')` | Clear axis limit errors |

#### Méthodes d'entrées/sorties

| Méthode | Description |
|---------|-------------|
| `get_analog_input(channel)` | Get voltage (in V) at a given input (starting with 1) |
| `get_digital_input(channel)` | Get value (0 or 1) at a given digital input (1 through 8) |
| `get_digital_input_register()` | Get all 8 digital inputs as a single 8-bit integer |
| `get_digital_output(channel)` | Get value (0 or 1) at a given digital output (1 through 8) |
| `get_digital_output_register()` | Get all 8 digital inputs as a single 8-bit integer |
| `set_digital_output(channel, value)` | Set value (0 or 1) at a given digital output (1 through 8) |
| `set_digital_output_register(value)` | Set all 8 digital inputs as a single 8-bit integer |

#### Méthodes de configuration

| Méthode | Description |
|---------|-------------|
| `enable_absolute_mode(enable=True)` | Set absolute motion mode |

#### Méthodes d'activation

| Méthode | Description |
|---------|-------------|
| `is_enabled()` | Check if the output is enabled |
| `enable_axis(enable=True)` | Enable output. If the output is disabled, the steps are generated by the controller, but not sent to the motors. |

#### Méthodes de position

| Méthode | Description |
|---------|-------------|
| `get_position()` | Get the current pulse position |
| `set_position_reference(position=0)` | Set the current pulse position as a reference. Re-calibrate the pulse position counter so that the current position is set as position (0 by default). |

#### Méthodes de mouvement

| Méthode | Description |
|---------|-------------|
| `move_to(position)` | Move to a given position |
| `move_by(steps=1)` | Move for a given number of steps |
| `jog(direction)` | Jog in a given direction. direction can be either "-" (negative) or "+" (positive). The motion continues until it is explicitly stopped, or until a limit is hit. |
| `stop(immediate=False)` | Stop motion. If immediate==True make an abrupt stop; otherwise, slow down gradually. |
| `home(direction, home_mode)` | Home using a given home mode. direction can be "+" or "-" The mode can be "only_home_input", "only_home_input_lowspeed", or "only_limit_input". For meaning, see Arcus PMX manual. |

#### Méthodes de vitesse

| Méthode | Description |
|---------|-------------|
| `get_axis_speed()` | Get the speed setting (in Hz) |
| `set_axis_speed(speed)` | Set the speed setting (in Hz) |

#### Méthodes de statut et synchronisation

| Méthode | Description |
|---------|-------------|
| `get_status_n()` | Get the status as an integer |
| `get_status()` | Get the status as a set of string descriptors |
| `is_moving()` | Check if motor is moving |
| `wait_move(timeout=None, period=0.05)` | Wait until motion is done |

#### Méthodes de gestion des erreurs

| Méthode | Description |
|---------|-------------|
| `check_limit_error()` | Check if the motor hit limit errors. Return "" (not errors), "+" (positive limit error) or "-" (negative limit error). |
| `clear_limit_error()` | Clear limit error |

#### Méthodes d'entrées/sorties

| Méthode | Description |
|---------|-------------|
| `get_digital_input(channel)` | Get value (0 or 1) at a given digital input (1 through 5) |
| `get_digital_input_register()` | Get all 5 digital inputs as a single 5-bit integer |
| `get_digital_output(channel)` | Get value (0 or 1) at a given digital output (1 through 2) |
| `get_digital_output_register()` | Get all 2 digital outputs as a single 2-bit integer |
| `set_digital_output(channel, value)` | Set value (0 or 1) at a given digital output (1 through 2) |
| `set_digital_output_register(value)` | Set all 2 digital inputs as a single 2-bit integer |

---

## Résumé des méthodes de vitesse disponibles

Basé sur cette documentation complète, voici les méthodes disponibles pour contrôler la vitesse :

### Pour Performax4EX et Performax2EX :

| Méthode | Description | Unité |
|---------|-------------|--------|
| `get_global_speed()` | Obtenir la vitesse globale | Hz |
| `set_global_speed(speed)` | Définir la vitesse globale | Hz |
| `get_axis_speed(axis='all')` | Obtenir la vitesse par axe | Hz |
| `set_axis_speed(axis, speed)` | Définir la vitesse par axe | Hz |
| `get_current_axis_speed(axis='all')` | Obtenir la vitesse instantanée | Hz |

> **Note importante :** Cette documentation ne mentionne pas de méthodes spécifiques pour l'accélération dans le package Arcus. L'accélération pourrait être contrôlée via les méthodes génériques `get_device_variable()` et `set_device_variable()` ou via des commandes ASCII directes avec `query()`.

