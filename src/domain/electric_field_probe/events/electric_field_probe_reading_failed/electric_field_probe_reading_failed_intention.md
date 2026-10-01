# electric_field_probe_reading_failed — Intention

## Rationale

Modéliser l'échec d'une boucle de lecture continue de la sonde electric field probe (NARDA EP-600, exception) comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

Renomme et remplace l'ancien `ContinuousAcquisitionFailed`, qui était une classe générique partagée entre le flux AEFI/MCU (ADS131A04) et le flux electric field probe (NARDA).

## Responsibility

- Signale qu'une lecture continue de la sonde a échoué suite à une exception.
- Porte l'identifiant de l'acquisition et la raison de l'échec.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Nommé "Reading" et non "Acquisition" : rien n'est persisté par ce flux, c'est une lecture en direct.
- Placé dans `domain/electric_field_probe/events/` : événement propre à l'agrégat `ElectricFieldProbe`, plus de classe générique partagée avec le flux AEFI/MCU.
