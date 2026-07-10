# electric_field_probe_acquisition_executor — Intention

## Rationale

Implémentation concrète de `IElectricFieldProbeAcquisitionExecutor`, miroir de
`ContinuousAcquisitionExecutor` mais découplée de `VoltageMeasurement` : le
contexte `electric_field_probe` n'a pas de notion in-phase/quadrature, donc
son propre événement `FieldSampleAcquired` évite de forcer un mensonge de
type sur l'événement partagé.

## Responsibility

- Démarrer une boucle d'acquisition à `sample_rate_hz` dans un thread séparé,
  via `IElectricFieldProbePort.acquire_sample()`.
- Publier `FieldSampleAcquired` à chaque échantillon (topic
  `"fieldsampleacquired"`) — sert de battement de cœur au voyant "données
  reçues" côté UI.
- Réutiliser `ContinuousAcquisitionStopped`/`ContinuousAcquisitionFailed`
  (génériques, ne portent que `acquisition_id`/`reason`) sous des topics
  dédiés (`"electricfieldprobeacquisition{stopped,failed}"`) pour ne pas
  interférer avec les abonnements du presenter lock-in existant.
- Arrêter proprement la boucle sur `stop()` (thread daemon + flag d'arrêt).

## Design

- Copie quasi-exacte de `ContinuousAcquisitionExecutor` — même stratégie
  thread + `threading.Event`, volontairement dupliquée plutôt que
  généralisée : les deux executors n'ont en commun que la mécanique de
  boucle, pas le type de mesure qu'ils publient.
