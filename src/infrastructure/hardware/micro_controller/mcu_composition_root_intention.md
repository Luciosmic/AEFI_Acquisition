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
