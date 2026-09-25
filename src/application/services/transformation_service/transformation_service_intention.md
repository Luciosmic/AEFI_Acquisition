# transformation_service — Intention

## Rationale

Appliquer à chaque échantillon la transformation de coordonnées qui ramène la mesure dans le repère sources : `E_sources = P·E_sensor`, où `P = Rx(θx)·Ry(θy)·Rz(θz)` est la rotation de montage (elle amène le capteur, aligné sur le repère sources, jusqu'à son montage actuel). Le capteur mesure `E_sensor = Pᵀ·E_sources` ; la correction en est la transposée. Les angles d'essai (tâtonnement) s'appliquent aussi, en direct. Elle corrige l'orientation mécanique du capteur AEFI. Définition des repères et de P : `domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md`.

Les angles viennent de la calibration capteur (rotation active : dernière calibration pour la géométrie source courante, sinon angles idéaux). Avant, ils venaient d'un panneau séparé non persisté (Sensor Transformation), supprimé.

## Responsibility

- Suivre la rotation active : s'abonner à `activesensorrotationchanged` (publié par `SensorCalibrationService`) et mettre à jour les angles appliqués. Le composition root l'initialise au démarrage avec `SensorCalibrationService.get_active_rotation()`.
- Activer ou désactiver l'application de la transformation.
- Fournir la transformation de coordonnées (Capteur → Sources, `E_sources = P·E_sensor`) et la mesure (Sources → Capteur, `E_sensor = Pᵀ·E_sources`).
- Publier `SensorTransformationAnglesUpdated` sur `IDomainEventBus` lors de chaque changement d'angles.

## Design

- **Purement calculatoire** : repose sur `scipy.spatial.transform.Rotation` — `_rotation = from_euler('XYZ', …)` = P : majuscules = intrinsèque X→Y'→Z'', équivalent aux rotations autour des axes sources fixes appliquées Z puis Y puis X (angles en degrés). Pas d'inversion : les angles saisis sont les angles de montage tels quels. Attention : transposer n'équivaut pas à nier les angles (`Pᵀ = Rz(−θz)·Ry(−θy)·Rx(−θx)`). Aucun port infrastructure dédié.
- **État interne** : angles courants (`_angles: np.ndarray`) + flag `_enabled`.
- **`IDomainEventBus` optionnel** : injecté au constructeur, peut être `None` (mode test sans bus, pas d'abonnement).
- **`force_transform_sensor_to_source`** : bypass du flag `_enabled` pour les panneaux de référence.
