# Continuous Acquisition Service

## Rationale
Ce service applicatif gère le mode d'acquisition continue (sans scan spatial), utilisé pour la surveillance temps-réel du signal ou la vérification du bon fonctionnement de l'ADC avant un scan.

## Responsibility
- Démarrer une acquisition continue avec une configuration donnée (`start_acquisition`).
- Arrêter l'acquisition en cours (`stop_acquisition`).
- Mettre à jour les paramètres d'acquisition à la volée sans interruption (`update_acquisition_parameters`).

## Design
- Service intentionnellement minimal : délègue entièrement l'exécution à `IContinuousAcquisitionExecutor` (infrastructure).
- Reçoit également `IAcquisitionPort` pour le passer à l'executor, qui gère le thread d'acquisition.
- La validation des paramètres est prévue mais non encore implémentée (TODO commenté dans le code).
