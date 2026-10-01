# aefi_voltage_reading_started — Intention

## Rationale

Modéliser le démarrage d'une lecture continue de tension AEFI comme un fait immuable passé, symétrique à `AefiVoltageReadingStopped`/`AefiVoltageReadingFailed`. Son absence était un vrai trou : l'event audit log (`_system/self/event_store.md`) montrait des `Stopped` sans jamais de `Started` correspondant — aucun événement de démarrage n'existait avant, pour aucun exécuteur.

## Responsibility

- Signale qu'une lecture continue de tension AEFI a démarré.
- Porte l'identifiant de l'acquisition concernée (même `acquisition_id` que les événements `Stopped`/`Failed`/`AefiVoltageSampleAcquired` de la même lecture).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Nommé "Reading" et non "Acquisition" : rien n'est persisté par ce flux (pas de sauvegarde), c'est une lecture en direct — "Acquisition" suggérait à tort qu'on gardait quelque chose.
- Publié comme première instruction du worker, avant la boucle — symétrique à `Stopped`/`Failed` publiés dans son `finally`.
