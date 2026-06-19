# transformation_service — Intention

## Rationale

Encapsuler les transformations de repère appliquées aux données de capteur (rotation du frame sensor, passage repère local → repère monde). Ces transformations sont une logique applicative qui coordonne les value objects domain `FrameRotation`, `Vector3D`, `Quaternion`.

## Responsibility

- Appliquer les transformations de repère aux mesures de champ électrique.
- Fournir une API claire pour la couche interface (panneau transformation capteur).

## Design

- **Service applicatif** : coordonne des value objects domain purs, pas de dépendance hardware.
- Publie des événements de transformation si les résultats doivent être broadcastés sur le bus.
