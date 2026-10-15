---
in_graph: false
vault_ref: "0_inbox/EVENT - 2026-10-15_calibration-transmission-lidar.md"
generated: 2026-10-15
---

# Calibration de la transmission par barre et LIDAR

## Problème

Le banc convertit les millimètres en impulsions moteur via `microns_per_pulse`, aujourd'hui **dérivé** d'une valeur mécanique théorique :

    µm/impulsion = 1000 · travel_per_motor_revolution_mm / (full_steps_per_revolution · microsteps)

`full_steps_per_revolution` et `microsteps` sont des réglages exacts. `travel_per_motor_revolution_mm` (poulie, courroie, vis) est la seule inconnue physique : on la suppose, on ne la mesure pas. Une erreur de x % sur elle donne une erreur de x % sur toute la cartographie.

## Mesure

Une barre de longueur L connue est posée à environ 1 m du sol, alignée avec un axe de balayage. Le LIDAR vise vers le bas :

- au-dessus de la barre, il mesure une distance **courte** ;
- hors de la barre, il mesure une distance **longue**.

Un balayage de l'axe à vitesse constante donne un profil en créneau d(n), où n est la position moteur en impulsions.

## Estimation

1. Seuil : s = (d_haut + d_bas) / 2, à partir des médianes des deux plateaux.
2. Fronts : n₁ et n₂, positions où d franchit s, obtenues par interpolation linéaire entre les deux échantillons qui encadrent le franchissement.
3. N = |n₂ − n₁| ;
   `microns_per_pulse = 1000 · L / N` ;
   donc `travel_per_motor_revolution_mm = L · full_steps_per_revolution · microsteps / N`.

## Ce qui s'annule et ce qui reste

Le résultat ne dépend que d'une **différence** de deux fronts franchis dans le même sens, pendant le même balayage, à la même vitesse. Tout décalage commun disparaît :

| Source | Effet sur N |
|---|---|
| Latence du LIDAR (horodatage côté PC) | décalage v·τ identique aux deux fronts : **s'annule** |
| Taille du spot LIDAR (noyau symétrique) | les deux fronts à 50 % restent centrés : **s'annule** |
| Jeu mécanique (backlash) | un seul sens de balayage : **s'annule** |
| Unité LIDAR non vérifiée | seul le seuil compte : **sans effet** |
| Échantillonnage (25 Hz) | ≈ v / f par front ; à 2 mm/s, 0,08 mm, soit 1·10⁻⁴ pour L = 1 m |
| Désalignement θ entre la barre et l'axe | biais ≈ θ² / 2 ; 1° donne 1,5·10⁻⁴ |

Contraintes de protocole :

- franchir les deux fronts **hors des rampes d'accélération**, avec une marge avant et après la barre ;
- balayer lentement ;
- ne balayer que dans **un seul sens**.

## Intégration au domaine

- **Grandeur écrite** : `travel_per_motor_revolution_mm`, via une nouvelle `MechanicalTransmissionCalibrationEntry`. On mesure l'inconnue réelle sans modifier le calcul de `microns_per_pulse`. `MotionConversionHandler` applique l'entrée par l'événement `mechanicaltransmissioncalibrationentryadded`.
- **Domaine** : un service pur (`domain/calibration/`) qui prend les couples (n, d) et L, et rend N et la transmission. Il échoue par erreur typée si le nombre de fronts trouvés n'est pas exactement 2.
- **Œuf et poule** : avant la calibration, le mouvement en millimètres est refusé. Le balayage doit donc piloter l'axe **en impulsions brutes**. Le seul chemin existant est le driver Arcus, avec un précédent dans `motion_timing_characterizer.py`.
- **Association position/distance** : le LIDAR n'est pas synchronisé avec le moteur. On interroge la position en impulsions et on interpole n à l'horodatage de chaque échantillon LIDAR, comme le fait le fly-scan avec `_sweep_line`.

## Décisions (2026-10-15)

- **Base** : on fusionne `feature/inertial-sensor-panel` (le LIDAR) dans `develop`, puis on crée la branche de calibration depuis `develop`.
- **Homing** : il est autorisé sans conversion. Il travaille en impulsions sur les fins de course. Cela solde aussi la dette « homing refusé ».
- **Grandeur** : `travel_per_motor_revolution_mm`, écrite via une nouvelle entrée de calibration.
- **Axes** : on mesure X puis Y, l'un après l'autre. Le domaine garde une transmission commune : on écrit la moyenne des deux, et l'écart X/Y est affiché à l'opérateur, jamais masqué. Une transmission par axe ne viendra que si l'écart mesuré la justifie.
- **Recalibration** : une nouvelle entrée doit s'appliquer sans redémarrage, sinon la calibration d'un banc déjà calibré reste inopérante jusqu'au prochain lancement.
