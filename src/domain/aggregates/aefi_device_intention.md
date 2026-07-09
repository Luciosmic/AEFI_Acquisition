# aefi_device — Intention

## Rationale

Aggregate Root représentant l'instrument AEFI physique — sa géométrie de quadrant de sources et l'orientation de son capteur central. Centralise la logique de calcul des paires d'interaction Source→Capteur qui sont nécessaires pour le problème direct.

## Responsibility

- Stocker la géométrie du dispositif (`QuadSourceGeometry`) et son identifiant.
- Calculer les paires d'interaction `AefiInteractionPair` (vecteur relatif Source→Capteur) pour les quatre sources quadrant.
- Exposer l'orientation du capteur via `get_orientation() → Quaternion`.

## Design

- **`@dataclass(frozen=True)`** : l'instrument est immuable — ses paramètres géométriques ne changent pas en cours d'expérience.
- **Mapping `source_id → Quadrant`** fixé dans `get_interactions()` : S1=TOP_RIGHT, S2=TOP_LEFT, S3=BOTTOM_LEFT, S4=BOTTOM_RIGHT — convention AEFI.
- **Capteur en (0,0,0) dans le repère local** : simplification géométrique valide pour le problème direct.
