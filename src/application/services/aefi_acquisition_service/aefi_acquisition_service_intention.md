# aefi_acquisition_service — Intention

## Rationale

Séparer la logique d'acquisition continue (streaming temps-réel) du scan 2D step-by-step. L'acquisition continue est utilisée pour la visualisation en direct (oscilloscope) indépendamment d'un scan. Un service dédié préserve la cohésion du `ScanApplicationService`.

## Responsibility

- Démarrer l'acquisition continue en transmettant la config et le port d'acquisition à `IAefiAcquisitionExecutor`.
- Arrêter l'acquisition en cours via `stop_acquisition()`.

## Design

- **Service intentionnellement minimal** : délègue entièrement à `IAefiAcquisitionExecutor`, sans état propre autre que la référence à l'exécuteur.
- **`IAcquisitionPort` injecté** : transmis à l'exécuteur à chaque démarrage pour éviter un couplage statique à un seul channel d'acquisition.
- **Best-effort, pas de rate** : le round-trip ADC (OSR × n_avg, configuré côté hardware avancé) domine le timing de plusieurs ordres de grandeur ; il n'y a donc pas de paramètre `sample_rate_hz` ni de mise à jour à la volée à porter ici.
