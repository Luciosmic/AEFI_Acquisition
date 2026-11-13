# motion_control_service — Intention

## Rationale

Exposer des commandes de motion manuel (jog, absolu, homing) à la UI sans que la UI ne manipule le `IMotionPort` directement. Le service ajoute le clamping aux limites d'axe, le tracking de position cible et la publication de l'événement `EmergencyStopTriggered`.

## Responsibility

- Calculer la position cible pour les mouvements relatifs en prenant comme référence soit la dernière cible connue soit la position courante hardware.
- Clamp les positions cibles aux limites d'axe avant de commander le mouvement.
- Publier `EmergencyStopTriggered` sur le bus en cas d'arrêt d'urgence.
- Retourner un `OperationResult` (pas d'exception) pour chaque commande : la UI peut tester success/failure sans try/except.

## Design

- **`_last_target_position`** : tracking de la dernière cible envoyée pour éviter les lec­tures hardware inutiles dans les séquences de mouvements rapides (jog).
- **Toutes les commandes retournent `OperationResult[None, str]`** : interface explicitement non-exceptionnelle pour la UI.
- **`get_axis_limits`** : délègue au port avec fallback (1000, 1000) si le hardware ne répond pas — le fallback permissif évite de bloquer la UI.

- **Banc non calibré** : tant que le port n'a pas sa conversion mm/impulsion, `move_*` sont refusés par `MotionConversionUnavailable` (union `MotionControlError`) avant tout appel au port ; homing (impulsions sur les fins de course, nécessaire à la calibration de la transmission par barre), arrêt, arrêt d'urgence et préréglages de vitesse (impulsions) restent disponibles. `get_conversion_status()` dit ce qui manque et où le saisir.
- **Consigne en incréments** (`move_to_increments(x, y)`, `None` = axe laissé) : l'incrément est l'unité du contrôleur, la consigne ne dépend donc d'aucune conversion et reste utilisable sur un banc non calibré — c'est aussi ce qui permet de vérifier un facteur µm/incrément en commandant n incréments et en mesurant la distance. Passe par `IRawIncrementMotionPort` (injecté, optionnel). Refusée avant tout mouvement si négative (l'origine est la butée de homing) et, quand la conversion existe, au-delà de la course (`MotionCommandFailed` avec le détail). Sans conversion, seule la butée physique borne le haut de course. Remet à zéro la cible mémorisée du jog : le jog suivant relit la position matérielle.
