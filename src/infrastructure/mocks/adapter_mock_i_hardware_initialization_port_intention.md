# adapter_mock_i_hardware_initialization_port — Intention

## Rationale

Mock de `IHardwareInitializationPort` pour les tests de `SystemStartupApplicationService` et `SystemShutdownApplicationService` sans hardware.

## Responsibility

- Implémenter `initialize_all()`, `verify_all()`, `close_all()` comme no-ops.
- Configurable pour simuler des échecs d'initialisation.

## Design

- **`infrastructure/mocks/`** avec préfixe `adapter_mock_`.
- `verify_all()` retourne `True` par défaut, configurable pour retourner `False` dans les tests d'échec.
