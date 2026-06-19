# mcu_composition_root — Intention

## Rationale

Point de composition des dépendances pour le sous-système MCU. Instancie le communicateur série, les controllers AD9106 et ADS131A04, et leurs adaptateurs, pour injection dans le composition root global.

## Responsibility

- Instancier `MCUSerialCommunicator`, `AD9106Controller`, `ADS131Controller`, et les adaptateurs correspondants.
- Retourner les adaptateurs prêts à l'injection (IExcitationPort, IAcquisitionPort, etc.).

## Design

- **Module de composition** symétrique à `composition_root_arcus`.
- Utilisé depuis le composition root global (`main.py`).
