# i_system_lifecycle_output_port — Intention

## Rationale

Port de sortie vers la UI pour notifier les étapes de démarrage/arrêt du système. Sans ce port, les services lifecycle devraient appeler directement des widgets Qt ou logger uniquement, sans feedback visuel.

## Responsibility

- Déclarer `present_startup_started(message)`, `present_initialization_step(subsystem, status)`, `present_error(message)`, `present_startup_completed(success, errors)`.
- Déclarer `present_shutdown_started()`, `present_shutdown_completed(success, errors)`.

## Design

- **Port outbound (output)** dans `system_lifecycle_service/`.
- Implémenté par `PresenterSystemLifecycle` dans `interface/ui_system_lifecycle/`.
