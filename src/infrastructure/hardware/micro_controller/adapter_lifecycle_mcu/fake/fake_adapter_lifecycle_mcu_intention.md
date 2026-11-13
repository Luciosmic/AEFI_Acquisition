---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_adapter_lifecycle_mcu` : Implémenter `initialize_all()`, `verify_all()`, `close_all()` comme no-ops."
code: ["[[src/infrastructure/hardware/micro_controller/adapter_lifecycle_mcu/fake/fake_adapter_lifecycle_mcu.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/system_lifecycle_service/ports/i_hardware_initialization_port_intention]]"]
double_de: "[[src/infrastructure/hardware/micro_controller/adapter_lifecycle_mcu/adapter_lifecycle_mcu_intention]]"
---
# fake_adapter_lifecycle_mcu — Intention

## Rationale

Mock de `IHardwareInitializationPort` pour les tests de `SystemStartupApplicationService` et `SystemShutdownApplicationService` sans hardware.

## Responsibility

- Implémenter `initialize_all()`, `verify_all()`, `close_all()` comme no-ops.
- Configurable pour simuler des échecs d'initialisation.

## Design

- **`infrastructure/mocks/`** avec préfixe `adapter_mock_`.
- `verify_all()` retourne `True` par défaut, configurable pour retourner `False` dans les tests d'échec.
