# i_electric_field_probe_acquisition_executor — Intention

## Rationale

Abstraire la mécanique d'exécution de l'acquisition continue (thread, boucle,
retry) derrière un port pour que `ElectricFieldProbeService` reste un simple
délégateur, testable sans thread réel — même rôle que
`IAefiAcquisitionExecutor` pour le canal AEFI.

## Responsibility

- Déclarer `start(config: ElectricFieldProbeAcquisitionConfig, probe_port: IElectricFieldProbePort)`.
- Déclarer `stop()`.
- Déclarer `is_running() -> bool`.

## Design

- **Port outbound** dans `electric_field_probe_service/ports/`.
- Implémenté par `ElectricFieldProbeAcquisitionExecutor` dans `infrastructure/execution/`.
- La politique de retry (`MAX_CONSECUTIVE_SAMPLE_FAILURES`) est une règle
  applicative propre à la sonde Narda (connue pour être flaky) — elle vit
  dans l'implémentation infra de ce port, pas dans le contrat lui-même, et
  n'existe pas côté `AefiAcquisitionExecutor`.
- Pas de `update_config()` : l'acquisition est best-effort des deux côtés
  (AEFI et sonde), donc il n'y a plus de paramètre de rate à mettre à jour
  à chaud. Historique : `IAefiAcquisitionExecutor` avait un `update_config`
  qui n'était jamais relu par son worker (mort depuis l'origine) — les deux
  ports ont depuis convergé en retirant le concept entièrement plutôt que de
  le réparer.
