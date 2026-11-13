# i_motion_control_output_port — Intention

## Rationale

Port de sortie du `MotionControlService` vers la UI pour notifier les changements de position et les erreurs de motion. Évite que le service appelle directement des widgets Qt.

## Responsibility

- Déclarer les méthodes de présentation liées à la motion : mise à jour de position, retour d'erreur de commande motion.

## Design

- **Port output** co-localisé dans `motion_control_service/`.
- Implémenté par `MotionPresenter` dans `interface/presenters/`.
