# hardware_configuration_service — Intention

## Rationale

Fournir un point d'entrée unique à la couche UI pour découvrir et configurer les périphériques hardware avancés, sans que la UI ne connaisse les implémentations concrètes (Arcus, MCU, AD9106, ADS131A04). Ce service agrège les `IHardwareAdvancedConfigurator` injectés depuis le composition root.

## Responsibility

- Lister les identifiants de tous les périphériques configurables (`list_hardware_ids`).
- Exposer le nom affichable et les specs de paramètres par périphérique (`get_hardware_display_name`, `get_parameter_specs`).
- Router les configurations utilisateur vers le bon adaptateur (`apply_config`, `save_config_as_default`, `reset_to_default`).

## Design

- **Collection d'`IHardwareAdvancedConfigurator`** indexée par `hardware_id` dans un dictionnaire : routing O(1).
- **Aucune logique métier** : ce service est un pur dispatcher applicatif. Les règles de validation hardware restent dans les adaptateurs.
- **`get_parameter_specs` appelle `type(provider).get_parameter_specs()`** : garantit l'appel de la méthode de classe statique même si l'instance est passée par injection.

## Propriétaire unique par matériel (2026-10-02)

- `take_control(hardware_id, controller)` / `release_control` : un use case peut
  tenir la configuration avancée d'un matériel (la caractérisation du débit tient
  `mcu` — n_avg — et `ads131a04` — OSR). Pendant ce temps, `apply_config`,
  `save_config_as_default` et `reset_to_default` sont refusés
  (`OperationResult.fail`), et `HardwareConfigurationControlChanged` permet au
  panneau Hardware Advanced Config de griser les champs et d'afficher le pilote.
- Le use case écrit lui-même via son port (`IAcquisitionAveragingPort`), pas via
  ce service : le verrou ne bloque que les modifications manuelles.
- ponytail: `ad9106_dds` n'est pas encore tenu par les pilotes de l'excitation
  (scan, calibration automatique) — l'onglet DDS peut toujours écrire les
  registres pendant un scan. Même mécanisme à brancher.
