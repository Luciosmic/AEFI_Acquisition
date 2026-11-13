# electric_field_probe_acquisition_executor — Intention

## Rationale

`ElectricFieldProbeService` doit rester un délégateur mince (connect/disconnect
+ start/stop/is_running vers l'executor), pas porter la boucle
d'acquisition — mécanique d'exécution (thread, boucle, retry), donc
infrastructure. Même rôle que `AefiAcquisitionExecutor` pour le canal AEFI.

## Responsibility

- Implémenter `IElectricFieldProbeAcquisitionExecutor`.
- Faire tourner la boucle d'acquisition dans un thread daemon, best-effort :
  `max_duration_s`, publication de `FieldSampleAcquired`. Un délai interne
  fixe (`_SAMPLE_INTERVAL_S` = 50Hz, non configurable) protège le mode
  mock/fake (acquisition quasi instantanée) d'un flood de l'event bus / UI
  Qt, tout en restant réaliste : 50Hz mirrore le plafond physique de la
  sonde réelle (réponse de filtre la plus rapide ~33Hz à F1). Contre la
  sonde réelle, le round-trip série domine déjà et ce délai n'ajoute
  presque rien.
- Publier `ElectricFieldProbeReadingStarted` en entrée de boucle, avant même
  la première tentative de lecture — symétrique à `Stopped`/`Failed`.
- Tolérer jusqu'à `MAX_CONSECUTIVE_SAMPLE_FAILURES` (2) échecs consécutifs de
  `probe_port.acquire_sample()` avant de publier `ElectricFieldProbeReadingFailed`
  — la sonde Narda est connue pour être flaky (erreurs USB/série
  transitoires) ; un consommateur du flux (ex. un scan) n'a aucun moyen de
  relancer le worker après une seule mauvaise lecture.
- Publier `ElectricFieldProbeReadingStopped` en sortie de boucle (`finally`).

## Design

- Thread + `threading.Event` pour le stop flag, `join(timeout=2.0)` — même
  squelette que `AefiAcquisitionExecutor`.
- Pas de `update_config()` ni de `sample_rate_hz` : les deux canaux
  d'acquisition continue (AEFI et sonde) sont best-effort.
