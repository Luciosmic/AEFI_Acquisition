# Documentation complète de l'API myCobot - Elephant Robotics

## Table des matières
1. [Introduction](#introduction)
2. [API Générale (7.2_API.html)](#api-générale)
3. [Contrôle des Angles (7.3_angle.html)](#contrôle-des-angles)
4. [Contrôle des Coordonnées (7.3_coord.html)](#contrôle-des-coordonnées)
5. [Exemples pratiques](#exemples-pratiques)

---

## Introduction

Cette documentation compile toutes les informations de l'API myCobot d'Elephant Robotics, basée sur les sections officielles :
- [7.2_API.html](https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.2_API.html)
- [7.3_angle.html](https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.3_angle.html)
- [7.3_coord.html](https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.3_coord.html)

L'API est compatible avec Python 2 et Python 3.5+.

---

## API Générale (7.2_API.html)

### 1. Statut Général

#### 1.1 `power_on()`
- **Fonction** : Allumer le robot
- **Valeur de retour** : None

#### 1.2 `power_off()`
- **Fonction** : Éteindre le robot
- **Valeur de retour** : None

#### 1.3 `is_power_on()`
- **Fonction** : Vérifier si le robot est allumé
- **Valeur de retour** :
  - `1` : Allumé
  - `0` : Éteint
  - `-1` : Erreur

#### 1.4 `release_all_servos()`
- **Fonction** : Relâcher tous les servos
- **Valeur de retour** : None

#### 1.5 `is_controller_connected()`
- **Fonction** : Vérifier la connexion avec le contrôleur
- **Valeur de retour** :
  - `1` : Connecté
  - `0` : Non connecté
  - `-1` : Erreur

### 2. Mode MDI et Opérations

#### 2.1 `get_angles()`
- **Fonction** : Obtenir les angles de tous les joints
- **Valeur de retour** : Liste des angles (degrés)

#### 2.2 `send_angle(joint_id, angle, speed)`
- **Fonction** : Envoyer un angle à un joint spécifique
- **Paramètres** :
  - `joint_id` (int) : 1-6
  - `angle` (float) : Angle en degrés
  - `speed` (int) : Vitesse 0-100
- **Valeur de retour** : None

#### 2.3 `send_angles(angles, speed)`
- **Fonction** : Envoyer des angles à tous les joints
- **Paramètres** :
  - `angles` (list) : Liste de 6 angles en degrés
  - `speed` (int) : Vitesse 0-100
- **Valeur de retour** : None

#### 2.4 `get_coords()`
- **Fonction** : Obtenir les coordonnées actuelles
- **Valeur de retour** : Liste [x, y, z, rx, ry, rz]

#### 2.5 `send_coord(coord_id, coord, speed)`
- **Fonction** : Envoyer une coordonnée spécifique
- **Paramètres** :
  - `coord_id` (int) : 1-6 (x,y,z,rx,ry,rz)
  - `coord` (float) : Valeur de la coordonnée
  - `speed` (int) : Vitesse 0-100
- **Valeur de retour** : None

#### 2.6 `send_coords(coords, speed, mode)`
- **Fonction** : Envoyer toutes les coordonnées
- **Paramètres** :
  - `coords` (list) : [x, y, z, rx, ry, rz]
  - `speed` (int) : Vitesse 0-100
  - `mode` (int) : Mode de mouvement
- **Valeur de retour** : None

### 3. Mode JOG

#### 3.1 `jog_angle(joint_id, direction, speed)`
- **Fonction** : Contrôle JOG par angle
- **Paramètres** :
  - `joint_id` (int) : 1-6
  - `direction` (int) : 0=décroître, 1=croître
  - `speed` (int) : 0-100

#### 3.2 `jog_coord(coord_id, direction, speed)`
- **Fonction** : Contrôle JOG par coordonnée
- **Paramètres** :
  - `coord_id` (int) : 1-6
  - `direction` (int) : 0=décroître, 1=croître
  - `speed` (int) : 0-100

#### 3.3 `jog_stop()`
- **Fonction** : Arrêter le mouvement JOG
- **Valeur de retour** : None

#### 3.4 `pause()`
- **Fonction** : Mettre en pause
- **Valeur de retour** : None

#### 3.5 `resume()`
- **Fonction** : Reprendre le mouvement
- **Valeur de retour** : None

#### 3.6 `stop()`
- **Fonction** : Arrêter le mouvement
- **Valeur de retour** : None

#### 3.7 `is_paused()`
- **Fonction** : Vérifier si en pause
- **Valeur de retour** :
  - `1` : En pause
  - `0` : Pas en pause
  - `-1` : Erreur

### 4. Contrôle des Servos

#### 4.1 `set_encoder(joint_id, encoder)`
- **Fonction** : Définir la valeur d'encodeur d'un joint
- **Paramètres** :
  - `joint_id` (int) : 1-6
  - `encoder` (int) : 0-4096

#### 4.2 `get_encoder(joint_id)`
- **Fonction** : Obtenir la valeur d'encodeur d'un joint
- **Paramètres** : `joint_id` (int) : 1-6
- **Valeur de retour** : Valeur d'encodeur 0-4096

#### 4.3 `set_encoders(encoders, speed)`
- **Fonction** : Définir les encodeurs de tous les joints
- **Paramètres** :
  - `encoders` (list) : Liste de 6 valeurs d'encodeur
  - `speed` (int) : Vitesse 0-100

#### 4.4 `get_encoders()`
- **Fonction** : Obtenir tous les encodeurs
- **Valeur de retour** : Liste des encodeurs

### 5. Contrôle des Entrées/Sorties

#### 5.1 `set_pin_mode(pin_no, pin_mode)`
- **Fonction** : Définir le mode d'une broche
- **Paramètres** :
  - `pin_no` (int) : Numéro de broche
  - `pin_mode` (int) : 0=entrée, 1=sortie, 2=entrée_pullup

#### 5.2 `set_digital_output(pin_no, pin_signal)`
- **Fonction** : Définir la sortie numérique d'une broche
- **Paramètres** :
  - `pin_no` (int) : Numéro de broche
  - `pin_signal` (int) : 0/1

#### 5.3 `get_digital_input(pin_no)`
- **Fonction** : Lire l'entrée numérique d'une broche
- **Paramètres** : `pin_no` (int) : Numéro de broche
- **Valeur de retour** : Valeur du signal

### 6. Contrôle de la Pince

#### 6.1 `is_gripper_moving()`
- **Fonction** : Vérifier si la pince bouge
- **Valeur de retour** :
  - `0` : Ne bouge pas
  - `1` : Bouge
  - `-1` : Erreur

#### 6.2 `set_gripper_state(flag, speed)`
- **Fonction** : Définir l'état de la pince
- **Paramètres** :
  - `flag` (int) : 0=ouvrir, 1=fermer
  - `speed` (int) : Vitesse 0-100

#### 6.3 `get_gripper_value()`
- **Fonction** : Obtenir la valeur de la pince
- **Valeur de retour** : Valeur de la pince

#### 6.4 `set_gripper_value(value, speed)`
- **Fonction** : Définir la valeur de la pince
- **Paramètres** :
  - `value` (int) : 0-100
  - `speed` (int) : Vitesse 0-100

### 7. Contrôle Socket

#### 7.1 `MyCobotSocket(ip, port)`
- **Fonction** : Initialiser la connexion socket
- **Paramètres** :
  - `ip` (str) : Adresse IP
  - `port` (int) : Port (généralement 9000)

### 8. Utilitaires

#### 8.1 `utils.get_port_list()`
- **Fonction** : Obtenir la liste de tous les ports série
- **Valeur de retour** : Liste des ports série

#### 8.2 `utils.detect_port_of_basic()`
- **Fonction** : Détecter automatiquement le port du Basic M5
- **Valeur de retour** : Port détecté (str) ou None

---

## Contrôle des Angles (7.3_angle.html)

### Introduction
Le contrôle par angles permet de commander directement les articulations du robot en spécifiant les angles de chaque joint.

### Fonctions principales

#### `get_angles()`
- **Description** : Récupère les angles actuels de tous les joints
- **Retour** : Liste de 6 angles en degrés
- **Exemple** :
```python
angles = mc.get_angles()
print(f"Angles actuels: {angles}")
```

#### `send_angle(joint_id, angle, speed)`
- **Description** : Envoie un angle spécifique à un joint
- **Paramètres** :
  - `joint_id` : Numéro du joint (1-6)
  - `angle` : Angle en degrés
  - `speed` : Vitesse (0-100)
- **Exemple** :
```python
mc.send_angle(1, 90, 50)  # Joint 1 à 90° à vitesse 50
```

#### `send_angles(angles, speed)`
- **Description** : Envoie des angles à tous les joints simultanément
- **Paramètres** :
  - `angles` : Liste de 6 angles
  - `speed` : Vitesse (0-100)
- **Exemple** :
```python
mc.send_angles([0, 0, 0, 0, 0, 0], 50)  # Position zéro
```

### Exemples pratiques

#### Mouvement de base
```python
from pymycobot.mycobot import MyCobot
import time

mc = MyCobot("COM9", 115200)

# Aller à la position zéro
mc.send_angles([0, 0, 0, 0, 0, 0], 50)
time.sleep(3)

# Mouvement personnalisé
mc.send_angles([0, 30, -30, 0, 0, 0], 50)
time.sleep(3)

# Retour à zéro
mc.send_angles([0, 0, 0, 0, 0, 0], 50)
```

#### Contrôle joint par joint
```python
# Mouvement séquentiel des joints
for joint in range(1, 7):
    mc.send_angle(joint, 45, 30)
    time.sleep(1)
    mc.send_angle(joint, 0, 30)
    time.sleep(1)
```

---

## Contrôle des Coordonnées (7.3_coord.html)

### Introduction
Le contrôle par coordonnées permet de commander le robot en spécifiant la position et l'orientation de l'effecteur final dans l'espace cartésien.

### Système de coordonnées
- **X, Y, Z** : Position en mm
- **RX, RY, RZ** : Orientation en degrés (angles d'Euler)

### Fonctions principales

#### `get_coords()`
- **Description** : Récupère les coordonnées actuelles
- **Retour** : Liste [x, y, z, rx, ry, rz]
- **Exemple** :
```python
coords = mc.get_coords()
print(f"Position actuelle: {coords}")
```

#### `send_coord(coord_id, coord, speed)`
- **Description** : Envoie une coordonnée spécifique
- **Paramètres** :
  - `coord_id` : 1=X, 2=Y, 3=Z, 4=RX, 5=RY, 6=RZ
  - `coord` : Valeur de la coordonnée
  - `speed` : Vitesse (0-100)
- **Exemple** :
```python
mc.send_coord(1, 200, 50)  # X = 200mm
```

#### `send_coords(coords, speed, mode)`
- **Description** : Envoie toutes les coordonnées
- **Paramètres** :
  - `coords` : Liste [x, y, z, rx, ry, rz]
  - `speed` : Vitesse (0-100)
  - `mode` : Mode de mouvement
- **Exemple** :
```python
mc.send_coords([200, 0, 200, 0, 0, 0], 50, 0)
```

### Exemples pratiques

#### Mouvement en coordonnées
```python
from pymycobot.mycobot import MyCobot
import time

mc = MyCobot("COM9", 115200)

# Position de départ
mc.send_coords([160, 0, 160, 0, 0, 0], 50, 0)
time.sleep(3)

# Mouvement vers une nouvelle position
mc.send_coords([200, 100, 200, 0, 0, 0], 50, 0)
time.sleep(3)

# Retour à la position de départ
mc.send_coords([160, 0, 160, 0, 0, 0], 50, 0)
```

#### Contrôle d'une coordonnée spécifique
```python
# Déplacer seulement en X
mc.send_coord(1, 250, 50)  # X = 250mm
time.sleep(2)
mc.send_coord(1, 160, 50)  # Retour à X = 160mm
```

---

## Exemples pratiques

### Script complet de démonstration
```python
from pymycobot.mycobot import MyCobot
import time

# Initialisation
mc = MyCobot("COM9", 115200)

print("Début de la démonstration myCobot")

# 1. Test des lumières RGB
print("Test des lumières RGB...")
for i in range(3):
    mc.set_color(255, 0, 0)  # Rouge
    time.sleep(1)
    mc.set_color(0, 255, 0)  # Vert
    time.sleep(1)
    mc.set_color(0, 0, 255)  # Bleu
    time.sleep(1)

# 2. Test des angles
print("Test des mouvements par angles...")
# Position zéro
mc.send_angles([0, 0, 0, 0, 0, 0], 50)
time.sleep(3)

# Mouvement personnalisé
mc.send_angles([0, 45, -45, 0, 0, 0], 50)
time.sleep(3)

# Retour à zéro
mc.send_angles([0, 0, 0, 0, 0, 0], 50)
time.sleep(3)

# 3. Test des coordonnées
print("Test des mouvements par coordonnées...")
# Position de départ
mc.send_coords([160, 0, 160, 0, 0, 0], 50, 0)
time.sleep(3)

# Mouvement vers une nouvelle position
mc.send_coords([200, 100, 200, 0, 0, 0], 50, 0)
time.sleep(3)

# Retour à la position de départ
mc.send_coords([160, 0, 160, 0, 0, 0], 50, 0)
time.sleep(3)

print("Démonstration terminée")
```

### Gestion d'erreurs
```python
try:
    # Vérifier la connexion
    if mc.is_controller_connected():
        print("Robot connecté")
        
        # Obtenir les angles actuels
        angles = mc.get_angles()
        print(f"Angles actuels: {angles}")
        
        # Mouvement sécurisé
        mc.send_angles([0, 0, 0, 0, 0, 0], 30)  # Vitesse réduite
        
except Exception as e:
    print(f"Erreur: {e}")
```

---

## Notes importantes

1. **Sécurité** : Toujours vérifier l'espace de travail avant de faire bouger le robot
2. **Vitesse** : Commencer avec des vitesses faibles (20-30) pour les tests
3. **Limites** : Respecter les limites d'angles et de coordonnées du robot
4. **Connexion** : Vérifier la connexion avec `is_controller_connected()` avant les mouvements
5. **Firmware** : S'assurer que le firmware est correctement installé (mode transpondeur)

---

*Documentation compilée à partir des sources officielles Elephant Robotics*
*Dernière mise à jour : Décembre 2024*

