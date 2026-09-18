# hardware_config_resolution — Intention

## Rationale

Chaque hardware configurable (AD9106, ADS131A04, MCU) a deux fichiers JSON —
`*_default_config.json` (réglages usine) et `*_last_config.json` (dernier état
appliqué) — qui doivent être combinés en une seule config résolue, aussi bien
au démarrage (`MCUCompositionRoot`) que pour l'affichage des panels Hardware
Advanced Config (`get_parameter_specs()`). Avant ce module, chaque site
réimplémentait sa propre logique de fusion (parfois un `dict.update()`
superficiel qui écrasait des sous-dicts imbriqués entiers comme `channels`),
ce qui a permis à panel et hardware réel de diverger silencieusement.

## Responsibility

- Fournir une fonction de fusion pure et testée : `resolve_config(default,
  override)` — l'override gagne clé par clé, récursivement sur les dicts
  imbriqués, sans muter ses arguments.
- Fournir un petit helper d'I/O : `load_json_if_exists(path)`.

## Design

- Fonctions pures, sans état, sans dépendance à un hardware particulier.
- Utilisé pour la **lecture** (affichage panel) par `MCUCompositionRoot` (résolution
  default+last pour adc/dds/mcu au boot) et par `AD9106AdvancedConfigurator.get_parameter_specs()`
  / `MCUAdvancedConfigurator.get_parameter_specs()`.
- Utilisé pour l'**écriture** (read-modify-write, pas juste lecture) par
  `AD9106AdvancedConfigurator.apply_config()` / `save_config_as_default()` /
  `_enforce_dds1_dds2_link()`, et par `AdapterExcitationConfigurationAD9106.set_link_dds1_dds2()`
  — la base résolue sert de valeurs par défaut pour les clés absentes du dict reçu, pour ne
  jamais écraser à 0 un champ qu'un appelant partiel n'a pas mentionné.
- Un seul algorithme de fusion, une seule vérité entre tous ces sites.
