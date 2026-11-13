---
type: evenement-de-domaine::solidai-ddd
tldr: "Signale qu'une lecture continue de la sonde s'est arrêtée, normalement ou après un échec."
code: ["[[src/domain/electric_field_probes/events/electric_field_probe_reading_stopped/electric_field_probe_reading_stopped.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/electric_field_probes/electric_field_probe_intention]]"
---
# electric_field_probe_reading_stopped — Intention

## Rationale

Modéliser l'arrêt (normal ou après échec) d'une lecture continue de la sonde electric field probe (NARDA EP-600) comme un fait immuable passé.

Renomme et remplace l'ancien `ContinuousAcquisitionStopped`, qui était une classe générique partagée entre le flux AEFI/MCU (ADS131A04) et le flux electric field probe (NARDA) — les deux flux ont maintenant chacun leurs propres événements typés.

## Responsibility

- Signale qu'une lecture continue de la sonde s'est arrêtée, normalement ou après un échec.
- Porte l'identifiant de l'acquisition concernée.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Nommé "Reading" et non "Acquisition" : rien n'est persisté par ce flux, c'est une lecture en direct.
- Placé dans `domain/electric_field_probes/events/` : événement propre à l'agrégat `ElectricFieldProbe`, plus de classe générique partagée avec le flux AEFI/MCU.
