# continuous_acquisition_service — Intention

## Rationale

Séparer la logique d'acquisition continue (streaming temps-réel) du scan 2D step-by-step. L'acquisition continue est utilisée pour la visualisation en direct (oscilloscope) indépendamment d'un scan. Un service dédié préserve la cohésion du `ScanApplicationService`.

## Responsibility

- Démarrer l'acquisition continue en transmettant la config et le port d'acquisition à `IContinuousAcquisitionExecutor`.
- Arrêter l'acquisition en cours via `stop_acquisition()`.
- Mettre à jour les paramètres à la volée sans interrompre l'acquisition (`update_acquisition_parameters`).

## Design

- **Service intentionnellement minimal** : délègue entièrement à `IContinuousAcquisitionExecutor`, sans état propre autre que la référence à l'exécuteur.
- **`IAcquisitionPort` injecté** : transmis à l'exécuteur à chaque démarrage pour éviter un couplage statique à un seul channel d'acquisition.
- **Validation différée** : TODO explicite pour la validation basique (sample_rate > 0) — le design accepte une croissance future sans modification d'interface.
