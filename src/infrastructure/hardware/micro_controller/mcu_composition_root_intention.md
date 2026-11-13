---
type: point-de-composition::solidai-hexagonal
tldr: "Point de composition `mcu_composition_root` : Instancier `MCUSerialCommunicator`, `AD9106Controller`, `ADS131Controller`, et les adaptateurs correspondants."
code: ["[[src/infrastructure/hardware/micro_controller/mcu_composition_root.py]]"]
cause_de_changement: outil
cable:
  - "[[src/infrastructure/hardware/ad9106/ad9106_advanced_configurator/ad9106_advanced_configurator_intention]]"
  - "[[src/infrastructure/hardware/ad9106/adapter_excitation_configuration_ad9106/adapter_excitation_configuration_ad9106_intention]]"
  - "[[src/infrastructure/hardware/ads131a04/adapter_adc_oversampling_ads131a04/adapter_adc_oversampling_ads131a04_intention]]"
  - "[[src/infrastructure/hardware/ads131a04/adapter_aefi_acquisition_ads131a04/adapter_aefi_acquisition_ads131a04_intention]]"
  - "[[src/infrastructure/hardware/ads131a04/adapter_i_acquistion_port_ads131a04/adapter_i_acquistion_port_ads131a04_intention]]"
  - "[[src/infrastructure/hardware/ads131a04/ads131a04_advanced_configurator/ads131a04_advanced_configurator_intention]]"
  - "[[src/infrastructure/hardware/micro_controller/adapter_acquisition_averaging_mcu/adapter_acquisition_averaging_mcu_intention]]"
  - "[[src/infrastructure/hardware/micro_controller/adapter_lifecycle_mcu/adapter_lifecycle_mcu_intention]]"
  - "[[src/infrastructure/hardware/micro_controller/mcu_advanced_configurator/mcu_advanced_configurator_intention]]"
---
# mcu_composition_root — Intention

## Rationale

Point de composition des dépendances pour le sous-système MCU. Instancie le communicateur série, les controllers AD9106 et ADS131A04, et leurs adaptateurs, pour injection dans le composition root global.

## Responsibility

- Instancier `MCUSerialCommunicator`, `AD9106Controller`, `ADS131Controller`, et les adaptateurs correspondants.
- Retourner les adaptateurs prêts à l'injection (IExcitationPort, IAcquisitionPort, etc.).
- Résoudre la config de démarrage (`_load_and_apply_config()`) : pour chaque hardware (ADC,
  DDS, MCU), fusionner `*_default_config.json` + `*_last_config.json` via
  `hardware_config_resolution.resolve_config()` — en mémoire uniquement, aucune écriture
  disque ici — et transmettre le résultat à `MCULifecycleAdapter.set_config()`. L'application
  réelle (écriture hardware, persistance) n'a lieu que plus tard, à `initialize_all()`.

## Design

- **Module de composition** symétrique à `composition_root_arcus`.
- Utilisé depuis le composition root global (`main.py`).
- Injecte `self._ad9106_configurator` (pas seulement `event_bus`) dans `MCULifecycleAdapter` —
  c'est ce qui permet au boot de déléguer l'application DDS à
  `AD9106AdvancedConfigurator.apply_config()` (écrivain unique, voir son intention.md) plutôt
  que de dupliquer une écriture registre séparée.
