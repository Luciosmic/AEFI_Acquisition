# Contrôle de Platines - Bases Fondamentales

Source : https://pylablib.readthedocs.io/en/latest/devices/stages_basics.html#stages-basics
## Introduction

Ce guide présente les concepts fondamentaux pour contrôler les platines de positionnement avec pylablib. Presque toutes les platines implémentent les mêmes fonctionnalités de base pour le déplacement, l'arrêt, la mise à l'origine et l'interrogation du statut.

## Exemple de base

Voici un exemple typique d'utilisation d'une platine :

```python
stage = Thorlabs.KinesisMotor("27000001")  # connexion à la platine
stage.home()                               # mise à l'origine
stage.wait_for_home()                      # attente de la fin de la mise à l'origine
stage.move_by(1000)                        # déplacement de 1000 pas
stage.wait_move()                          # attente de la fin du mouvement
stage.jog("+")                             # démarrage d'un mouvement continu vers le positif
time.sleep(1.)                             # attente d'1 seconde
stage.stop()                               # arrêt du mouvement
stage.close()                              # fermeture de la connexion
```

> **Note** : Certaines platines peuvent ne pas avoir toutes ces fonctions (par exemple, pas de mise à l'origine), mais si elle est présente, elle fonctionne de manière similaire.

## Concepts de base

### Compteurs, encodeurs, mise à l'origine et commutateurs de fin de course

Les platines utilisent deux stratégies principales pour suivre la position :

#### 1. Comptage des pas

**Problème** : Une fois l'appareil mis sous tension, sa position est inconnue.

**Solution** : Procédure de mise à l'origine qui implique généralement :
- Déplacement vers une position prédéfinie
- Remise à zéro du compteur de pas à cette position
- Utilisation d'un **commutateur de fin de course** : commutateur physique situé à l'extrémité de la plage de déplacement

**Avantages et limitations :**
- **Moteurs pas-à-pas** : La taille de chaque pas est bien définie, donnant des résultats reproductibles
- **Platines piézo slip-stick** (Attocube, SmarAct, Picomotor) : Taille des pas intrinsèquement non fiable, dépendant de la charge, direction, position, température, etc.

#### 2. Lecture de position matérielle

Utilisée quand le comptage fiable est impossible (platines ou moteurs DC classiques) :

**Types de capteurs :**
- **Numérique (encodeur)** : plus simple, moins cher, plus fiable
- **Analogique** (résistif, capacitif, optique) : résolution plus élevée, fonctionne dans des environnements extrêmes (vide poussé, cryogénie)

**Fonctionnement :** Les contrôleurs utilisent une boucle de rétroaction pour contrôler en douceur la vitesse et la direction du mouvement.

### Pas et coordonnées réelles

**Unités internes :** Presque toutes les platines permettent le contrôle en pas moteur, pas d'encodeur ou autres unités internes.

**Conversion en unités réelles :** 
- Pas toujours simple ou parfois impossible
- Dépend du réducteur du moteur et du pas de vis (platines linéaires)
- Informations généralement dans le manuel du moteur ou de la platine de translation
- Parfois nécessite des calculs explicites

### Contrôle de vitesse

**Rampes de vitesse :** Dans de nombreux cas, la vitesse du moteur augmente et diminue linéairement plutôt qu'abruptement.

**Paramètres configurables :**
- **Vitesse de "croisière"** : généralement en pas/s
- **Accélération de rampe** : généralement en pas/s²

> **Note** : Parfois, des unités internes doivent être utilisées.

## Notes d'application et exemples

### Mouvement

#### Méthodes de mouvement standard

| Méthode | Description |
|---------|-------------|
| `move_to(position)` | Se déplace vers une position spécifiée |
| `move_by(distance)` | Se déplace d'une distance ou nombre de pas spécifié |
| `jog(direction)` | Mouvement continu dans une direction donnée jusqu'à arrêt ou butée |

**Équivalence :** Si les deux sont présentes, `stage.move_by(s)` et `stage.move_to(stage.get_position()+s)` donnent le même résultat.

#### Comportement asynchrone

> **Important** : Dans presque tous les cas, ces commandes sont **asynchrones** - elles initialisent simplement le mouvement et continuent immédiatement.

```python
# Exemple de comportement asynchrone
stage.move_by(1000)
print(stage.is_moving())  # True - la platine bouge, mais l'exécution continue
time.sleep(1.)
print(stage.is_moving())  # False - après 1s le mouvement est terminé
```

#### Arrêt du mouvement

- **Méthode** : `stop()`
- **Types d'arrêt** (selon les cas) :
  - **"Soft"** : avec rampe de décélération
  - **"Hard"** : arrêt immédiat

### Statut et synchronisation

Puisque les commandes de mouvement sont asynchrones, les appareils fournissent des méthodes de synchronisation :

#### Méthodes de vérification

| Méthode | Description |
|---------|-------------|
| `is_moving()` | Vérifie si la platine est actuellement en mouvement |
| `wait_move()` | Met en pause l'exécution jusqu'à la fin du mouvement |
| `get_status()` | Retourne l'état du mouvement, commutateurs de fin de course, erreurs possibles, etc. |
| `get_current_speed()` | Obtient la vitesse actuelle |

### Lecture de position

#### Méthode principale

Si une platine a une lecture de position (capteur matériel ou comptage de pas), elle est implémentée avec `get_position()`.

#### Gestion de la référence

```python
# Exemple d'utilisation de la référence de position
print(stage.get_position())          # 10000
stage.set_position_reference(20000)  # change la référence actuelle
print(stage.get_position())          # 20000 (réaction immédiate, pas de mouvement physique)
stage.move_to(21000)                 # déplacement de 1000 pas
```

> **Important** : `set_position_reference()` ne change que l'état du compteur interne et ne cause aucun mouvement de la platine.

### Sélection d'axe

#### Contrôleurs multi-axes

De nombreux contrôleurs supportent le contrôle simultané de plusieurs moteurs différents.

**Paramètres d'axe :**
- **Contrôle d'un seul moteur habituel** (TMCM1110, Thorlabs KDC101) : paramètre vers la fin de la liste, valeur par défaut
- **Contrôle multi-étages par défaut** (Attocube ANC350, Arcus Performax) : paramètre généralement en premier, doit être spécifié

**Valeur spéciale "all" :** 
- Action effectuée pour tous les axes
- Résultats retournés pour tous les axes (liste ou dictionnaire)

#### Étiquetage des axes

**Méthodes d'identification :**
- **Index** : commençant par 0 ou 1 (plus courant)
- **Étiquettes spécifiques** : par exemple, Arcus Performax utilise X, Y, Z et U

> **Référence** : La spécification exacte est donnée dans la description de classe spécifique.

### Mise à l'origine (Homing)

#### Nécessité

Comme mentionné ci-dessus, les platines nécessitent souvent une mise à l'origine pour obtenir des lectures de position absolue.

**Fréquence :** 
- Doit être effectuée à chaque mise sous tension de la platine
- Les paramètres de mise à l'origine persistent généralement entre les reconnexions

#### Implémentation

**Méthode principale :** `home()`

**Méthodes associées :**
- `is_homed()` : vérifie si la mise à l'origine a déjà été effectuée
- **Comportement par défaut** : `home()` ne s'exécute pas si `is_homed()` retourne `True`, sauf si forcé

#### Mise à l'origine manuelle

Certaines platines n'ont pas de méthode de mise à l'origine explicite mais peuvent être mises à l'origine manuellement :
1. Faire fonctionner la platine jusqu'au commutateur de fin de course
2. Définir la référence de position à 0
