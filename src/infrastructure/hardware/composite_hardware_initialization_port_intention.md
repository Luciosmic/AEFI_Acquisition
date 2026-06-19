# composite_hardware_initialization_port — Intention

## Rationale

Implémentation composite de `IHardwareInitializationPort` qui délègue à plusieurs initialiseurs hardware (MCU, Arcus). Permet à `SystemStartupApplicationService` d'initialiser tous les périphériques via un seul appel sans connaître leur nombre ou leur type.

## Responsibility

- `initialize_all()` : appeler `initialize()` sur chaque adaptateur de lifecycle dans l'ordre correct (MCU d'abord, puis Arcus).
- `verify_all()` : vérifier la connectivité de tous les périphériques.
- `close_all()` : fermer toutes les connexions.

## Design

- **Pattern Composite** : la liste d'initialiseurs est injectée au constructeur.
- L'ordre d'initialisation est fixé par l'ordre dans la liste — MCU avant Arcus car l'ADC doit être prêt avant tout mouvement.
