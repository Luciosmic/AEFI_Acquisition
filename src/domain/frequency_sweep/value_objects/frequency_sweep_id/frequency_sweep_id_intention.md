# frequency_sweep_id — Intention

## Rationale

Une mesure objet référencera son fond par identité. Avec des `UUID` bruts, l'identité d'un balayage et celle d'un scan ou d'un point sont interchangeables pour le vérificateur de types.

## Responsibility

- Typer l'identité d'un `FrequencySweep`.

## Design

- `NewType` sur `UUID` (convention `AefiPointId`) ; le cast se fait aux frontières du domaine : `FrequencySweepId(uuid4())`.
