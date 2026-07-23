# ui_config_store — Intention

## Rationale

Les panneaux Qt (`interface/widgets/panels/`) ne doivent pas faire d'I/O disque directement. Avant ce module, `ScanControlPanel` lisait/écrivait ses fichiers de config JSON lui-même (`json`, `os`, `shutil` importés dans le widget), seul cas de ce type dans `interface/`.

Placement dans `interface/logic/` et non `infrastructure/` : ces données (dernier dossier d'export utilisé, valeurs de formulaire) sont de la vue pure, sans concept domaine ni port applicatif — contrairement à la config hardware (`IHardwareAdvancedConfigurator`), qui passe par un port défini en `application/` et des adaptateurs en `infrastructure/hardware/` parce qu'elle configure un vrai périphérique physique. Construire un port+service applicatif pour un préférence de formulaire serait de la sur-ingénierie. Même logique que `interface/logic/coordinate_transformer.py` : utilitaire fin de la couche interface, pas de dépendance domaine, pas de protocole de service applicatif complet.

## Responsibility

- Charger la section `scan_config` depuis `.aefi_acquisition/configs/scan_default_config.json`.
- Charger/sauvegarder `.aefi_acquisition/configs/export_default_config.json`.
- Initialiser ce fichier runtime depuis le template versionné `config_templates/export_default_config.json` au premier lancement.
- Nommé `UIConfigStore` (pas `ScanUIConfigStore`) car destiné à porter d'autres préférences UI futures, pas seulement le scan/export.

## Design

- Classe simple, sans port ABC dédié : ce sont des préférences de vue (valeurs de formulaire), pas un concept du domaine — pas de logique métier, pas d'invariant à protéger.
- Retourne des `dict` vides en cas de fichier manquant ou JSON invalide ; le panel applique ses propres valeurs par défaut.
- Injectée dans `ScanControlPanel.__init__` avec une instance par défaut, pour rester rétro-compatible avec `ScanControlPanel()`.
