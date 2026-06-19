# scan_dtos — Intention

## Rationale

Définir les contrats de communication entre la UI et les services applicatifs sous forme de dataclasses immuables. Les DTOs évitent que les objets domain (agrégats, value objects) ne fuient dans la couche interface, ce qui protège les invariants domain et simplifie la sérialisation.

## Responsibility

- `Scan2DConfigDTO` : transporte les paramètres de scan saisis par l'utilisateur (zone, nb points, pattern, délais, averaging).
- `ExportConfigDTO` : spécifie le format et le chemin d'export des résultats.
- `ScanStatusDTO` : snapshot en lecture seule de l'état courant d'un scan (pour la query `get_status()`).

## Design

- **`@dataclass(frozen=True)`** : immuabilité garantie, hashable, pas d'effets de bord.
- Les champs utilisent uniquement des primitives Python ou des types standard — aucun import domain.
- `ScanStatusDTO.progress_percentage` est calculé côté service, pas recalculé dans la UI.
