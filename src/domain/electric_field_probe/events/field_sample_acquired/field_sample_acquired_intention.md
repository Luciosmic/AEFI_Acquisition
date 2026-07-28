# field_sample_acquired — Intention

## Rationale

Signaler qu'un nouvel échantillon de champ électrique est disponible, pour un
flux d'acquisition continue piloté par une `ElectricFieldProbe` — miroir de
`AefiVoltageSampleAcquired` mais côté `electric_field_probe`, pour
ne pas coupler ce contexte à `AefiVoltageMeasurement`.

## Responsibility

- Porter l'identifiant de la sonde source, l'identifiant d'acquisition,
  l'index de l'échantillon et la mesure (`FieldMeasurement`).
- Servir de battement de cœur pour l'indicateur "données reçues" côté UI.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Topic de publication : `"fieldsampleacquired"` (nom de classe en minuscules).
