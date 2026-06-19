# Transformation Service

## Rationale
Ce service applicatif gère les transformations de coordonnées entre le repère capteur et le repère source. Il est utilisé pour corriger l'orientation mécanique du capteur AEFI lors du post-traitement des mesures.

## Responsibility
- Définir les angles de rotation (θx, θy, θz) appliqués à chaque vecteur de mesure.
- Activer ou désactiver l'application de la transformation.
- Fournir les transformations directe (Capteur → Source) et inverse (Source → Capteur).
- Publier un événement domaine `SensorTransformationAnglesUpdated` lors de chaque changement d'angles.

## Design
- Repose sur `scipy.spatial.transform.Rotation` (ordre 'XYZ' extrinsèque, angles en degrés).
- État interne : angles courants + flag `_enabled`.
- Dépendance optionnelle à `IDomainEventBus` pour la publication d'événements.
- Aucun port infrastructure dédié : la transformation est purement calculatoire.
