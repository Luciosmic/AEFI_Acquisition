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

Le LIDAR est fixé sur la colonne et vise le sol ; il se déplace avec elle. Une barre de longueur L connue est posée à environ 1 m du sol. On l'aligne avec l'axe en la faisant frôler les sphères sur toute leur course le long de cet axe : l'alignement suit ainsi la trajectoire réelle, et l'erreur angulaire θ est minimisée. Le LIDAR mesure :

- au-dessus de la barre, il mesure une distance **courte** ;
- hors de la barre, il mesure une distance **longue**.

Le profil d(n), où n est la position moteur en incréments, est un créneau. Chaque front est le point où d franchit le seuil s = (d_haut + d_bas) / 2.

## Stratégie : repérer, puis encadrer à l'arrêt

Le moteur se pilote à l'incrément près. La mesure fine se fait donc **à l'arrêt**, sans synchronisation entre le LIDAR et le moteur.

1. **Repérage grossier** : un fly scan donne la position approximative des deux fronts et les plateaux d_haut et d_bas. La latence du LIDAR ne fait que décaler ce repérage. On élargit donc l'encadrement initial d'une marge v·τ.
2. **Affinage de chaque front** : on part de l'encadrement [a, b], où a est sur la barre et b hors barre.
   1. On se déplace au milieu.
   2. On attend la stabilisation.
   3. On fait la moyenne de k échantillons LIDAR.
   4. On classe le point : sur la barre, hors barre, ou indécidable.
   5. On resserre l'encadrement (dichotomie).
3. **Arrêt, à la limite de nos capacités** : l'encadrement fait 1 incrément, ou le point est indécidable (|d̄ − s| < k_σ·σ/√k). Le spot du LIDAR adoucit le front : près du seuil, c'est le bruit du LIDAR qui borne la résolution, pas le moteur.
4. **Résultat** : on obtient deux encadrements, [a₁, b₁] et [a₂, b₂], d'où :

       N = n₂ − n₁ ± (δ₁ + δ₂),   avec nᵢ = (aᵢ + bᵢ) / 2 et δᵢ = |bᵢ − aᵢ| / 2

       travel_per_motor_revolution_mm = L · full_steps_per_revolution · microsteps / N

   L'incertitude de N se propage à la transmission, en même temps que celle de L.

## Sources d'erreur

| Source | Effet |
|---|---|
| Latence du LIDAR | ne touche que le repérage grossier, absorbée par la marge : **sans effet** sur N |
| Jeu mécanique (backlash) | la dichotomie se fait en aller-retour, sans approche dans un sens imposé. Le jeu n'est pas compensé pour l'instant. Si l'encadrement devient incohérent ou l'écart X/Y suspect, ajouter une approche toujours dans le même sens. |
| Spot LIDAR (noyau symétrique) | le franchissement à 50 % reste centré sur le bord ; il élargit la zone indécidable |
| Unité LIDAR non vérifiée | seul le seuil compte : **sans effet** |
| Désalignement θ entre la barre et l'axe | biais ≈ θ² / 2 ; 1° donne 1,5·10⁻⁴. Le réglage où la barre frôle les sphères le rend négligeable. |

## Intégration au domaine

- **Domaine** (`domain/calibration/`, fonctions pures) :
  - l'**encadrement de front**, qui donne le prochain point de sonde et le critère d'arrêt ;
  - la **classification d'un point**, à partir de la moyenne, de l'écart-type et du seuil ;
  - le **delta d'incréments avec incertitude**, qui donne la transmission et son incertitude.
- **Port en incréments bruts** : avant la calibration, le mouvement en millimètres est refusé. Le seul chemin existant passe par le driver Arcus, avec un précédent dans `motion_timing_characterizer.py`.
- **Service applicatif** : enchaîne le fly scan grossier, l'affinage du front 1, l'affinage du front 2, puis rend le résultat avec son incertitude.
- **Grandeur écrite** : `travel_per_motor_revolution_mm`, via une nouvelle `MechanicalTransmissionCalibrationEntry`. `MotionConversionHandler` l'applique par l'événement `mechanicaltransmissioncalibrationentryadded`.

## Décisions (2026-10-15)

- **Base** : on fusionne `feature/inertial-sensor-panel` (le LIDAR) dans `develop`, puis on crée la branche de calibration depuis `develop`.
- **Homing** : il est autorisé sans conversion. Il travaille en incréments sur les fins de course. Cela solde aussi la dette « homing refusé ».
- **Grandeur** : `travel_per_motor_revolution_mm`.
- **Axes** : on mesure X puis Y, l'un après l'autre. Le domaine garde une transmission commune : on écrit la moyenne des deux, et l'écart X/Y est affiché à l'opérateur, jamais masqué. Une transmission par axe ne viendra que si l'écart mesuré la justifie.
- **Recalibration** : une nouvelle entrée doit s'appliquer sans redémarrage.
- **Exclusion avec le scan** : la calibration et le scan s'excluent mutuellement, car tous deux pilotent les moteurs. Une calibration pendant un scan n'a aucun sens physique. La conversion n'est jamais reportée à la fin d'un scan.
- **Stratégie** : repérage par fly scan, puis affinage pas à pas par encadrement (voir plus haut).
- **Sens d'approche** : aller-retour libre pendant la dichotomie. On n'impose pas de sens pour l'instant.
- **Flux LIDAR** : la calibration le démarre et l'arrête elle-même. Si le panneau du capteur diffuse déjà ce flux, la calibration refuse de démarrer, par erreur typée et visible : le port série ne doit avoir qu'un seul propriétaire.
- **Placement** : le LIDAR est fixé sur la colonne. La barre est alignée en frôlant les sphères sur toute leur course.
- **Étendue du fly scan** : de butée à butée sur l'axe. La barre tient entièrement dans la course, avec un plateau hors barre de chaque côté. L'opérateur n'a rien à placer.

- **Paramètres de l'affinage** : le temps de stabilisation, le nombre k d'échantillons par point et le facteur k_σ sont réglables dans l'interface. Les valeurs initiales sont à ajuster sur le banc.
- **Écriture** : uniquement sur un clic « Enregistrer » de l'opérateur, une fois les deux axes mesurés. Jamais automatique.

## Plan de développement

Branche `feature/bar-lidar-calibration`. Un commit par étape, tests verts avant chaque commit.

1. **Domaine pur** (`domain/calibration/`) :
   - l'encadrement de front (prochain point de sonde, critère d'arrêt) ;
   - la classification d'un point (sur la barre, hors barre, indécidable) ;
   - le delta d'incréments avec son incertitude, qui donne la transmission et son incertitude ;
   - la moyenne X/Y et leur écart.
2. **Port en incréments bruts et adaptateur Arcus**, avec un fake :
   - aller à une position en incréments ;
   - lire la position ;
   - fixer la vitesse ;
   - attendre l'arrêt ;
   - homing ;
   - aller jusqu'à la butée opposée, détectée par les fins de course physiques du banc.
3. **Service applicatif `bar_transmission_calibration_service`** :
   - `measure_axis(axe, L, réglages)` : démarrer le flux LIDAR (refus si le panneau le diffuse déjà), homing, fly scan de butée à butée, plateaux et seuil, encadrements grossiers élargis d'une marge, affinage des deux fronts, résultat avec son incertitude, arrêt du flux ;
   - `record(mesure X, mesure Y)` : nouvelle `MechanicalTransmissionCalibrationEntry` avec la moyenne, puis l'événement `mechanicaltransmissioncalibrationentryadded`.
4. **Recalibration sans redémarrage** : `MotionConversionHandler` applique une nouvelle entrée quand aucun scan ne tourne, et journalise son refus sinon.
5. **Interface** : un onglet « Transmission (barre) » dans le panneau Calibration :
   - la position en **incréments moteur**, en direct, comme l'affichage actuel en mm. Elle reste disponible même quand le banc n'est pas calibré, y compris pendant la calibration ;
   - L et les réglages ;
   - Mesurer X, puis une invite pour repositionner la barre, puis Mesurer Y ;
   - les encadrements, N ± δ et la transmission ± son incertitude pour chaque axe ;
   - l'écart X/Y ;
   - le bouton Enregistrer.
6. **Mode mock** : un faux LIDAR qui rend un créneau selon la position du faux contrôleur, branché dans `main_mock.py`.
