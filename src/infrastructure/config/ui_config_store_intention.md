# ui_config_store — Intention

## Rationale

Les panneaux Qt (`interface/widgets/panels/`) ne doivent pas faire d'I/O disque directement — c'est la responsabilité de `infrastructure/`. Avant ce module, `ScanControlPanel` lisait/écrivait ses fichiers de config JSON lui-même (`json`, `os`, `shutil` importés dans le widget), seul cas de ce type dans `interface/`. `UIConfigStore` centralise cette persistance de préférences UI (pas de config hardware, déjà couvertes par les `*_advanced_configurator.py`).

## Responsibility

- Charger la section `scan_config` depuis `.aefi_acquisition/configs/scan_default_config.json`.
- Charger/sauvegarder `.aefi_acquisition/configs/export_default_config.json`.
- Initialiser ce fichier runtime depuis le template versionné `config_templates/export_default_config.json` au premier lancement.
- Nommé `UIConfigStore` (pas `ScanUIConfigStore`) car destiné à porter d'autres préférences UI futures, pas seulement le scan/export.

## Design

- Classe simple, sans port ABC dédié : ce sont des préférences de vue (valeurs de formulaire), pas un concept du domaine — pas de logique métier, pas d'invariant à protéger.
- Retourne des `dict` vides en cas de fichier manquant ou JSON invalide ; le panel applique ses propres valeurs par défaut.
- Injectée dans `ScanControlPanel.__init__` avec une instance par défaut, pour rester rétro-compatible avec `ScanControlPanel()`.
