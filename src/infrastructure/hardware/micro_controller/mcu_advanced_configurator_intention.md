# mcu_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour les paramètres MCU niveau firmware (baudrate, watchdog, timings de synchronisation). Expose ces paramètres avancés dans le panneau configuration avancée.

## Responsibility

- Définir les specs des paramètres MCU avancés.
- Appliquer et persister les configurations MCU.

## Design

- `hardware_id = "mcu"` (ou équivalent).
- Implémente `IHardwareAdvancedConfigurator`.
