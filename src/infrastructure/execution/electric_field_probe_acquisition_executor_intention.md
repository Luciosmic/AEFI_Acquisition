# electric_field_probe_acquisition_executor — Intention

## Rationale

`ElectricFieldProbeService` doit rester un délégateur mince (connect/disconnect
+ start/stop/is_running vers l'executor), pas porter la boucle
d'acquisition — mécanique d'exécution (thread, boucle, retry), donc
infrastructure. Même rôle que `AefiAcquisitionExecutor` pour le canal AEFI.

## Responsibility

- Implémenter `IElectricFieldProbeAcquisitionExecutor`.
- Faire tourner la boucle d'acquisition dans un thread daemon : rate control
  (`sample_rate_hz`), `max_duration_s`, publication de `FieldSampleAcquired`.
- Tolérer jusqu'à `MAX_CONSECUTIVE_SAMPLE_FAILURES` (2) échecs consécutifs de
  `probe_port.acquire_sample()` avant de publier `ContinuousAcquisitionFailed`
  — la sonde Narda est connue pour être flaky (erreurs USB/série
  transitoires) ; un consommateur du flux (ex. un scan) n'a aucun moyen de
  relancer le worker après une seule mauvaise lecture.
- Publier `ContinuousAcquisitionStopped` en sortie de boucle (`finally`).

## Design

- Thread + `threading.Event` pour le stop flag, `join(timeout=2.0)` — même
  squelette que `AefiAcquisitionExecutor`.
- Contrairement à `AefiAcquisitionExecutor`, pas de `update_config()` : voir
  `i_electric_field_probe_acquisition_executor_intention.md`.
