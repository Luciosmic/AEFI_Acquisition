# aefi_voltage_reading_failed — Intention

## Rationale

Modéliser l'échec d'une boucle de lecture continue de tension AEFI (exception) comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

Renomme et remplace l'ancien `ContinuousAcquisitionFailed`, qui était une classe générique partagée entre le flux AEFI/MCU (ADS131A04) et le flux electric field probe (NARDA) — les deux flux ont maintenant chacun leurs propres événements typés.

## Responsibility

- Signale qu'une lecture continue de tension AEFI a échoué suite à une exception.
- Porte l'identifiant de l'acquisition et la raison de l'échec.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Nommé "Reading" et non "Acquisition" : rien n'est persisté par ce flux, c'est une lecture en direct.
- Séparé des `scan_events` pour préserver la cohésion sémantique : scan = mesure positionnée, lecture continue = stream brut.
