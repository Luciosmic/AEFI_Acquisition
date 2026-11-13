# fake_adapter_motion_port_arcus_performax4ex — Intention

## Rationale

Mock de `IMotionPort` pour les tests applicatifs de `ScanApplicationService`, `MotionControlService` et `StepScanExecutor`. Permet d'exécuter des scans complets en test sans le hardware Arcus.

## Responsibility

- Implémenter `IMotionPort` en mémoire : `move_to()` enregistre la position et retourne un `motion_id`.
- Publier immédiatement `MotionCompleted` sur le bus après chaque `move_to()` (comportement synchrone simulé).
- `stop()` / `emergency_stop()` interrompent réellement le mouvement simulé en cours : ni `MotionCompleted`, ni `PositionUpdated` de la cible, ni position finale — le moteur reste où il a été arrêté (interpolation linéaire, rampe ignorée). Un double qui « finit » un mouvement arrêté valide à tort un consommateur qui compte sur l'arrêt (fly-scan : abandon de ligne sur pause/annulation).
- Exposer des spy attributes : `move_count`, `last_position`, etc. pour les assertions de test.

## Design

- **Placé dans `infrastructure/mocks/`** avec préfixe `adapter_mock_`.
- Publie des événements sur le bus pour permettre la synchronisation avec `StepScanExecutor`.
- Comportement par défaut : succès immédiat — peut être configuré pour simuler des échecs.
