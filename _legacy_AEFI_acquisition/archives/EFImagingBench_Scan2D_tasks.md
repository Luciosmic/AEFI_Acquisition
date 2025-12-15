# EFImagingBench_Scan2D : Tâches de développement pour un script de scan 2D minimal

Ce document liste les étapes nécessaires pour réaliser un script Python minimal permettant un balayage 2D avec acquisition, en utilisant les modules existants pour le contrôle moteur (Arcus Performax 4EX) et l'acquisition (AD9106/ADS131A04).

---

## 1. Initialisation des modules

### 1.1. Importer et initialiser le contrôleur de moteurs (EFImagingStageController)
- Importer la classe `EFImagingStageController` depuis le module controller.
- Le chemin des DLL et les paramètres de vitesse par défaut sont maintenant intégrés dans la classe.
- Instancier le contrôleur simplement :

```python
from controller.EFImagingBench_Controller_ArcusPerformax4EXStage import EFImagingStageController
stage = EFImagingStageController()  # Utilise le chemin DLL et les vitesses par défaut internes
```

_Complexité : 2_

### 1.2. Importer et initialiser le module d'acquisition AD9106/ADS131A04
- Importer la classe de communication série (ex : `SerialCommunicator`).
- Initialiser la connexion sur le port série voulu (ex : "COM10").
- Vérifier le succès de la connexion.

```python
from instruments.AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator
acq = SerialCommunicator()
success, msg = acq.connect("COM10")
if not success:
    raise RuntimeError(f"Erreur de connexion acquisition : {msg}")
```

_Complexité : 3_

---

## 2. Homing des axes

### 2.1. Effectuer le homing de l'axe X
- Appeler la méthode `home('x')` du contrôleur.
- Attendre la fin du mouvement avec `wait_move('x', timeout=30)`.

```python
stage.home('x')
stage.wait_move('x', timeout=30)
```
_Complexité : 2_

### 2.2. Effectuer le homing de l'axe Y
- Même principe que pour X.

```python
stage.home('y')
stage.wait_move('y', timeout=30)
```
_Complexité : 2_

### 2.3. Vérifier que les deux axes sont bien "homés" avant de continuer
- Utiliser `is_axis_homed('x')` et `is_axis_homed('y')`.
- Lever une erreur si un axe n'est pas homé.

```python
if not (stage.is_axis_homed('x') and stage.is_axis_homed('y')):
    raise RuntimeError("Homing non effectué sur X ou Y. Impossible de continuer.")
```
_Complexité : 2_

---

## 3. Configuration du balayage
- **3.1. Définir le nombre de lignes (x_nb) pour le scan en X**  
  _Complexité : 1_
- **3.2. Définir la longueur de balayage en X et Y (x_length, y_length)**  
  _Complexité : 1_
- **3.3. Définir la vitesse de déplacement sur Y (y_speed)**  
  _Complexité : 1_
- **3.4. Définir la fréquence d'échantillonnage (sampling_rate)**  
  _Complexité : 1_

## 4. Balayage 2D et acquisition
- **4.1. Pour chaque ligne X :**
    - **4.1.1. Se déplacer à la position de départ de la ligne (X, Y=0)**  
      _Complexité : 2_
    - **4.1.2. Démarrer l'acquisition**  
      _Complexité : 3_
    - **4.1.3. Déplacer l'axe Y à vitesse constante sur toute la longueur**  
      _Complexité : 3_
    - **4.1.4. Acquérir les données synchronisées pendant le déplacement**  
      _Complexité : 5_
    - **4.1.5. Enregistrer la position X courante et la vitesse Y mesurée**  
      _Complexité : 3_
    - **4.1.6. Stocker les données d'acquisition pour la ligne**  
      _Complexité : 2_
    - **4.1.7. (Optionnel) Attendre la fin du mouvement avant de passer à la ligne suivante**  
      _Complexité : 2_
    - **4.1.8. (Optionnel) Remonter Y à 0 ou faire un "zigzag"**  
      _Complexité : 3_

## 5. Sauvegarde et post-traitement
- **5.1. Sauvegarder les données brutes (acquisition + positions + vitesses) dans un fichier (ex: CSV, HDF5, etc.)**  
  _Complexité : 2_
- **5.2. (Optionnel) Générer un log de la configuration et des paramètres du scan**  
  _Complexité : 2_

## 6. Sécurité et gestion des erreurs
- **6.1. Gérer les erreurs de communication avec les moteurs**  
  _Complexité : 4_
- **6.2. Gérer les erreurs d'acquisition**  
  _Complexité : 4_
- **6.3. S'assurer que les axes ne sortent pas des limites physiques**  
  _Complexité : 3_

---

**Légende complexité** :
- 1-2 : Très simple (quelques lignes, peu de logique)
- 3-4 : Simple à modéré (utilisation d'API, gestion de base)
- 5-6 : Modéré à technique (synchronisation, gestion de flux de données)
- 7-8 : Technique/avancé (traitement temps réel, robustesse élevée)
- 9-10 : Très complexe (optimisation, multithreading, sécurité critique) 