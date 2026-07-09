# vector_3d (domain/value_objects/aefi_device) — Intention

## Rationale

Version locale du vecteur 3D dans le sous-espace `aefi_device/` — utilisée par les value objects propres à l'instrument AEFI (QuadSourceGeometry, AefiInteractionPair). Maintenir cette copie locale évite un import circulaire avec `domain/shared/`.

## Responsibility

- Représenter un vecteur 3D avec les opérations algébriques minimales nécessaires aux calculs géométriques AEFI.

## Design

- **`@dataclass(frozen=True)`**.
- Opérateurs `__sub__`, `__add__` pour les calculs de vecteur relatif dans `AefiDevice.get_interactions()`.
