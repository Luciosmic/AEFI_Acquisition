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
- Pas de `update_config()` : contrairement à `IAefiAcquisitionExecutor`
  (où `update_config` existe mais n'est jamais relu par le worker — mort
  depuis l'origine), `ElectricFieldProbeService.update_acquisition_parameters`
  a un vrai besoin de redémarrage (dt recalculé à l'entrée de boucle), donc
  il fait `stop()` puis `start(config, ...)` directement plutôt que de
  passer par une méthode d'update qui n'aurait jamais été appliquée.
