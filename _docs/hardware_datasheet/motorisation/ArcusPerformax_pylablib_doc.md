# Documentation Arcus Performax - Pylablib

## Vue d'ensemble

Arcus possède plusieurs contrôleurs et pilotes de moteurs, qui diffèrent principalement par leur nombre d'axes, leurs possibilités de communication et leur fonction de pilotage. Ils sont également distribués sous différents noms, par exemple Nippon Pulse America (NPA) ou Newmark Systems. 

Cependant, la nomenclature des modèles est la même :
- **4EX** : contrôleurs 4 axes avec connexion USB et RS485
- **2EX/2ED** : contrôleurs 2 axes avec connexions USB et RS485  
- **4ET** : contrôleurs 4 axes avec connexion Ethernet

La classe a été testée avec les contrôleurs 4EX et (partiellement) 2ED avec le mode de connectivité USB et RS-485, mais d'autres contrôleurs mentionnés ci-dessus devraient également fonctionner.

## Classes principales

Les principales classes d'appareils sont :

- `pylablib.devices.Arcus.Performax4EXStage` pour les contrôleurs 4 axes
- `pylablib.devices.Arcus.Performax2EXStage` pour les contrôleurs 2 axes  
- `pylablib.devices.Arcus.PerformaxDMXJSAStage` pour les contrôleurs simples à un seul axe (DMX-J-SA)

En plus d'un nombre d'axes différent, elles présentent plusieurs différences de syntaxe, donc l'une ne peut pas se substituer à l'autre.

Il existe également une classe générique `pylablib.devices.Arcus.GenericPerformaxStage`, qui implémente uniquement les fonctions les plus basiques : communication ASCII avec l'appareil et méthodes de base telles que la demande de nom d'appareil. Elle peut être utilisée avec des étages Arcus nouveaux ou non actuellement pris en charge pour les contrôler directement en utilisant le langage de contrôle ASCII (généralement décrit dans le manuel de l'étage).

## Exigences logicielles

### Modes de communication

Le contrôleur dispose de plusieurs modes de communication : **USB**, **RS485** et **Ethernet**.

### Mode USB

Le mode USB nécessite un pilote fourni avec le logiciel d'exploitation :
- Arcus Drivers and Tools
- Performax Series Installer  
- Performax USB Setup

Tous sont obtenus sur le site Web d'Arcus. L'installation des trois semble être suffisante.

Une fois les pilotes USB appropriés installés, vous pouvez connecter l'appareil directement via son port USB et utiliser les DLL du fabricant `PerformaxCom.dll` et `SiUSBXp.dll` pour communiquer avec l'appareil. Elles peuvent être obtenues sur le site Web du fabricant et placées dans le dossier avec le script, ou dans le dossier System32 de Windows.

Si la DLL se trouve ailleurs, le chemin peut être spécifié en utilisant le paramètre de bibliothèque `devices/dlls/arcus_performax` :

```python
import pylablib as pll
pll.par["devices/dlls/arcus_performax"] = "path/to/dll"
from pylablib.devices import Arcus
stage = Arcus.Performax4EXStage()
```

> **⚠️ Avertissement**
> 
> Il semble y avoir des problèmes avec les appareils contrôlés par USB avec Python 3.6 qui entraînent des écritures hors limites, une corruption de mémoire et un comportement indéfini. Par conséquent, Python 3.7+ est requis pour travailler avec cet appareil.

### Mode RS-485

La connexion RS-485 ne nécessite aucun pilote ou DLL spécifique à l'appareil, mais elle a besoin d'un contrôleur RS-485 connecté au PC. Ces contrôleurs apparaissent généralement comme des ports COM virtuels et ne nécessitent généralement aucun pilote supplémentaire.

## Connexion

### Connexion USB

Lors de l'utilisation de la connexion USB, l'appareil est identifié par son index, en commençant par 0. Pour obtenir la liste de tous les appareils connectés, vous pouvez utiliser `Arcus.list_usb_performax_devices` :

```python
from pylablib.devices import Arcus

# Liste des appareils connectés
devices = Arcus.list_usb_performax_devices()
print(devices)
# [(0, '4ex01', 'Performax USB',
#  '\\\\?\\usb#vid_1589&pid_a101#4ex01#{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}', '1589', 'a101'),
#  (1, '4ex21', 'Performax USB',
#  '\\\\?\\usb#vid_1589&pid_a101#4ex21#{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}', '1589', 'a101')]

# Connexion aux appareils
stage1 = Arcus.Performax4EXStage()
stage2 = Arcus.Performax2EXStage(idx=1)

# Fermeture des connexions
stage1.close()
stage2.close()
```

### Connexion RS-485

Lors de l'utilisation de la connexion RS-485, vous devez spécifier le port série correspondant à votre connexion RS-485 et, éventuellement, son débit en bauds :

```python
# Connexion simple
stage = Arcus.Performax4EXStage(conn="COM5")

# Connexion avec débit spécifique
stage2 = Arcus.Performax4EXStage(conn=("COM5", 38400))
```

Le débit en bauds est de **9600** par défaut, qui est la valeur standard pour les contrôleurs. Cependant, il peut être modifié en utilisant la méthode `Performax4EXStage.set_baudrate()`, auquel cas vous devrez l'explicitement spécifier lors de la prochaine connexion.

En mode RS-485, le paramètre `idx` est toujours utilisé et spécifie le numéro d'appareil connecté à ce contrôleur. Par défaut, ce numéro est 0, et il peut être interrogé (en utilisant une connexion USB) via `Performax4EXStage.get_device_number()`. Il peut également être défini en utilisant `Performax4EXStage.set_device_number()`, bien que les changements ne prennent effet qu'après un cycle d'alimentation de l'appareil.

### Basculement entre modes

Pour basculer entre les modes de contrôle USB et RS-485, vous devez brancher ou débrancher la connexion USB. Il est fortement recommandé de faire un cycle d'alimentation de l'appareil après cela, sinon il pourrait cesser de répondre aux commandes RS-485.

## Fonctionnement

Ce contrôleur présente plusieurs caractéristiques et différences par rapport à la plupart des autres étages et curseurs :

### 1. Gestion multi-axes

- Les contrôleurs 4 axes et 2 axes sont intrinsèquement multi-axes, ils prennent donc toujours l'axe comme premier argument
- Les axes sont étiquetés avec les lettres :
  - **"x", "y"** pour une version 2 axes
  - **"x", "y", "z", "u"** pour une version 4 axes
- La liste de tous les axes est liée au contrôleur exact et peut être obtenue en utilisant `Performax4EXStage.get_all_axes()`
- Un contrôleur à axe unique ne prend pas d'argument d'axe

### 2. Activation/désactivation des axes

- Différents axes peuvent être activés et désactivés en utilisant `Performax4EXStage.enable_axis()`
- **Note importante** : les axes désactivés se comportent toujours de la même manière que les axes activés (leur position s'incrémente normalement lorsque `move_to` est appelé), mais le moteur ne bouge pas physiquement

### 3. Gestion des erreurs de limite

Dans la configuration par défaut du contrôleur, les erreurs de limite sont activées :

- **Comportement par défaut** : lorsqu'un seul axe atteint le commutateur de limite pendant le mouvement, il est mis dans un état d'erreur, ce qui arrête immédiatement cet axe et tous les autres
- **Récupération** : le mouvement de l'axe ne peut être repris qu'en appelant `Performax4EXStage.clear_limit_error()`
- **Comportement alternatif** : si les erreurs de limite sont désactivées, seul l'axe qui a atteint la limite est arrêté

**Contrôle des erreurs de limite :**
- Activation/désactivation : `Performax4EXStage.enable_limit_errors()`
- Vérification du statut : `Performax4EXStage.limit_errors_enabled()`

> **Note** : La classe désactive automatiquement les erreurs de limite lors de la connexion car le comportement par défaut est souvent indésirable.

### 4. Contrôleur simplifié (DMX-J-SA)

Le contrôleur simplifié à axe unique (DMX-J-SA) a toujours les erreurs de limite désactivées. Son comportement est spécifié différemment :
- Lors de la connexion, vous pouvez spécifier l'argument `autoclear` (True par défaut)
- Cela indique qu'avant chaque commande de mouvement, l'erreur de limite doit être automatiquement effacée

### 5. Entrées/sorties

Les contrôleurs disposent également d'entrées analogiques et numériques et de sorties numériques, qui peuvent être interrogées et définies avec les commandes correspondantes.

### 6. Support encodeur

- Le contrôleur a une option pour connecter un encodeur pour une lecture de position séparée
- Par défaut, toutes les commandes fonctionnent en mode de comptage de pas
- Les valeurs d'encodeur sont uniquement accessibles via :
  - `Performax4EXStage.get_encoder()`
  - `Performax4EXStage.set_encoder_reference()`
- Il existe un mode en boucle fermée appelé StepNLoop, mais il n'est actuellement pas pris en charge dans le code

### 7. Modes de mouvement

La commande de mouvement intégrée a 2 modes : **relatif** et **absolu**.

- Le code définit le mode absolu lors de la connexion et l'assume dans toutes les commandes
- **Important** : si le mode change pour une raison quelconque, les commandes de mouvement cesseront de fonctionner correctement

