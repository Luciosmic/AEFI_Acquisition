# transformation_service — Intention

## Rationale

Gérer les transformations de coordonnées entre le repère capteur et le repère source. Utilisé pour corriger l'orientation mécanique du capteur AEFI lors du post-traitement des mesures.

## Responsibility

- Définir les angles de rotation (θx, θy, θz) appliqués à chaque vecteur de mesure.
- Activer ou désactiver l'application de la transformation.
- Fournir les transformations directe (Capteur → Source) et inverse (Source → Capteur).
- Publier `SensorTransformationAnglesUpdated` sur `IDomainEventBus` lors de chaque changement d'angles.

## Design

- **Purement calculatoire** : repose sur `scipy.spatial.transform.Rotation` (ordre 'XYZ' extrinsèque, angles en degrés). Aucun port infrastructure dédié.
- **État interne** : angles courants (`_angles: np.ndarray`) + flag `_enabled`.
- **`IDomainEventBus` optionnel** : injecté au constructeur, peut être `None` (mode test sans bus).
- **`force_transform_sensor_to_source`** : bypass du flag `_enabled` pour les panneaux de référence.
