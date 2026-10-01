# electric_field_probe_reading_started — Intention

## Rationale

Modéliser le démarrage d'une lecture continue de la sonde electric field probe (NARDA EP-600) comme un fait immuable passé, symétrique à `ElectricFieldProbeReadingStopped`/`ElectricFieldProbeReadingFailed`. Son absence était un vrai trou : l'event audit log (`_system/self/event_store.md`) montrait des `Stopped` sans jamais de `Started` correspondant.

## Responsibility

- Signale qu'une lecture continue de la sonde a démarré.
- Porte l'identifiant de l'acquisition concernée (même `acquisition_id` que les événements `Stopped`/`Failed`/`FieldSampleAcquired` de la même lecture).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Nommé "Reading" et non "Acquisition" : rien n'est persisté par ce flux, c'est une lecture en direct.
- Placé dans `domain/electric_field_probe/events/` (et non `shared_kernel`) : c'est un événement propre à l'agrégat `ElectricFieldProbe`, au même titre que `FieldSampleAcquired`/`ElectricFieldProbeConnectionChanged` — il ne partage plus de classe générique avec le flux AEFI/MCU.
- Publié comme première instruction du worker, avant la boucle — symétrique à `Stopped`/`Failed` publiés dans son `finally`.
