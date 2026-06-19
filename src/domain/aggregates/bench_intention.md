# bench (TestBench) — Intention

## Rationale

Aggregate Root représentant le banc d'essai physique — colonnes de sources électriques, capteur cubique 3D, et associations source-capteur. Sépare la configuration géométrique logique du banc de ses pilotes hardware (qui vivent dans infrastructure/).

## Responsibility

- Stocker et mettre à jour la configuration géométrique : colonnes, capteur, associations.
- Exposer `configure_geometry()` comme unique point de mutation (un seul appel remet à zéro les interactions calculées).
- Fournir `recompute_interactions()` (placeholder) pour recalculer les paires `AefiInteractionPair` depuis la géométrie.

## Design

- **`@dataclass`** (non-frozen) : la configuration du banc peut être modifiée entre les expériences.
- **`_interactions` est privé** : exposé en lecture seule via `interactions` (copie défensive).
- **`recompute_interactions()` en placeholder** : marque explicitement le point d'extension pour implémenter la géométrie réelle.
