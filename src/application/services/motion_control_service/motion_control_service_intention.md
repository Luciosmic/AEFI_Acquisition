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
