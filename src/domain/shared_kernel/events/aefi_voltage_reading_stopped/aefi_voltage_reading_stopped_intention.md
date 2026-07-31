# aefi_voltage_reading_stopped — Intention

## Rationale

Modéliser l'arrêt (normal ou après échec) d'une lecture continue de tension AEFI comme un fait immuable passé, pour permettre à la UI et aux services de réagir sans dépendance directe sur l'exécuteur.

Renomme et remplace l'ancien `ContinuousAcquisitionStopped`, qui était une classe générique partagée entre le flux AEFI/MCU (ADS131A04) et le flux electric field probe (NARDA) — les deux flux ont maintenant chacun leurs propres événements typés, plus de classe partagée distinguée seulement par le topic de publication.

## Responsibility

- Signale qu'une lecture continue de tension AEFI s'est arrêtée, normalement ou après un échec.
- Porte l'identifiant de l'acquisition concernée.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Nommé "Reading" et non "Acquisition" : rien n'est persisté par ce flux, c'est une lecture en direct.
- Séparé des `scan_events` pour préserver la cohésion sémantique : scan = mesure positionnée, lecture continue = stream brut.
