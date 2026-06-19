# Motion Control Service

## Rationale
Ce service applicatif expose les commandes de mouvement manuel (jog, absolu, homing, stop) à l'interface utilisateur. Il permet à l'opérateur de positionner le banc manuellement sans passer par le mécanisme de scan.

## Responsibility
- Exposer des commandes de déplacement : relatif (`move_relative`), absolu (`move_absolute`, `move_absolute_x`, `move_absolute_y`), homing (`home_x`, `home_y`, `home_xy`).
- Gérer l'arrêt normal (`stop`) et l'arrêt d'urgence (`emergency_stop`) avec publication de l'événement `EmergencyStopTriggered`.
- Maintenir une cible de position intermédiaire (`_last_target_position`) pour chaîner des mouvements successifs sans attendre le retour hardware.
- Fournir les limites des axes via `get_axis_limits`.

## Design
- Dépend uniquement de `IMotionPort` et `IDomainEventBus`, injectés au constructeur.
- Toutes les commandes retournent un `OperationResult` pour une gestion explicite des erreurs sans lever d'exception vers la couche interface.
- Le tracking de position intermédiaire est réinitialisé sur stop, home ou set_reference pour garantir la cohérence.
