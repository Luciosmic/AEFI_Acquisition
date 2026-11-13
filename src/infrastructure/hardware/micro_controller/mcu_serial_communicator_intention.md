---
type: atome::solidai-atome
tldr: "Couche de communication série bas-niveau avec le microcontrôleur (protocole custom sur USB-UART)."
code: ["[[src/infrastructure/hardware/micro_controller/mcu_serial_communicator.py]]", "[[src/infrastructure/hardware/micro_controller/adapter_acquisition_averaging_mcu/adapter_acquisition_averaging_mcu.py]]", "[[src/infrastructure/hardware/micro_controller/adapter_lifecycle_mcu/adapter_lifecycle_mcu.py]]", "[[src/infrastructure/hardware/micro_controller/hardware_config_resolution.py]]", "[[src/infrastructure/hardware/micro_controller/mcu_advanced_configurator/mcu_advanced_configurator.py]]", "[[src/infrastructure/hardware/micro_controller/mcu_composition_root.py]]"]
cause_de_changement: outil
---
# mcu_serial_communicator — Intention

## Rationale

Couche de communication série bas-niveau avec le microcontrôleur (protocole custom sur USB-UART). Isole la gestion du port série (pyserial), les retries et le parsing des trames dans une classe dédiée pour que les controllers AD9106 et ADS131A04 ne manipulent pas directement le port série.

## Responsibility

- Ouvrir/fermer le port série.
- Envoyer des commandes et recevoir les réponses avec gestion des timeouts.
- Implémenter le protocole de trame MCU (header, checksum, etc.).

## Design

- **Couche de transport pure** : pas de logique domain, pas de publication d'événements.
- Utilisé par `AD9106Controller` et `ADS131Controller` qui délèguent les IO série à ce communicateur.
