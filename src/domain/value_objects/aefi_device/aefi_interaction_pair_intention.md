# aefi_interaction_pair — Intention

## Rationale

Value object représentant la paire Source→Capteur avec le vecteur relatif entre eux. C'est l'unité atomique de calcul du problème direct AEFI : pour chaque paire, on calcule la contribution au champ électrique mesuré.

## Responsibility

- Stocker `source_id: str`, `sensor_id: str`, `relative_vector: Vector3D` (vecteur de la source vers le capteur).

## Design

- **`@dataclass(frozen=True)`** : les paires sont des faits géométriques immuables.
- Produit par `AefiDevice.get_interactions()` et `TestBench.recompute_interactions()`.
- Utilisé par `AefiPhysicsEngine` pour calculer la réponse du champ.
