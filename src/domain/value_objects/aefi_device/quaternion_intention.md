# quaternion (domain/value_objects/aefi_device) — Intention

## Rationale

Version locale du quaternion dans `aefi_device/` — représente l'orientation du capteur dans le repère de la sonde AEFI. Co-localisé avec les value objects de l'instrument pour éviter les dépendances circulaires.

## Responsibility

- Stocker (w, x, y, z) et représenter une rotation 3D pour l'orientation du capteur.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans `QuadSourceGeometry.sensor_orientation` et exposé par `AefiDevice.get_orientation()`.
