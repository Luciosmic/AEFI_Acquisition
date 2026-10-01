# mcu_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour le seul paramètre MCU exposé
aujourd'hui : `n_avg` (nombre d'échantillons moyennés côté MCU avant retour, commande série
`m<n_avg>`). Pas de registre hardware à écrire — `n_avg` est relu en direct depuis
`mcu_last_config.json` par `ADS131A04Adapter.acquire_sample()` à chaque acquisition, donc
"appliquer" une config ici se résume à persister le fichier.

## Responsibility

- `get_parameter_specs()` : définir la spec `n_avg` (bornes `NAVG_MIN`/`NAVG_MAX` = 1-127) et
  la peupler avec l'état **résolu** (default+last, via
  `hardware_config_resolution.resolve_config()`) — pas le default seul, sinon le panel affiche
  une valeur (ex. 127) jamais réellement utilisée par l'acquisition.
- `apply_config(config)` / `save_config_as_default(config)` : valider `n_avg` puis écrire
  respectivement `mcu_last_config.json` / `mcu_default_config.json`.
- `get_n_avg()` : lecture directe de `mcu_last_config.json` (fallback 1) — c'est la méthode
  dont `ADS131A04Adapter.acquire_sample()` se sert (indirectement, via une relecture du même
  fichier) pour construire la commande `m<n_avg>`.
- `reset_to_default()` : pendant de `save_config_as_default()` — relit `n_avg` depuis le
  default **pur** (pas résolu) et délègue à `apply_config()`.

## Design

- `hardware_id = "mcu"`.
- Implémente `IHardwareAdvancedConfigurator`.
- Au boot, `MCUCompositionRoot` résout `mcu_default_config.json` + `mcu_last_config.json` et
  `MCULifecycleAdapter._configure_mcu()` réécrit le résultat dans `mcu_last_config.json` à la
  connexion — c'est ce qui fait qu'un `n_avg` sauvegardé comme default prend effet sans clic
  manuel sur "Apply".
