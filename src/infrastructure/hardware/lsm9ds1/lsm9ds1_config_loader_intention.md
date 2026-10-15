# lsm9ds1_config_loader — Intention

## Rationale

Le port COM et le débit de la carte étaient des constantes codées en dur dans
le driver : changer de port physique demandait de modifier du code, et rien ne
disait à un lecteur du JSON ce que valait chaque nombre. Le fichier
`config_templates/lsm9ds1_config.json` porte ces paramètres avec leur unité
inline (UCUM) et un `schema_version` ; ce chargeur les lit et refuse une
version qu'il ne comprend pas plutôt que de deviner.

## Responsibility

- `load_lsm9ds1_config(path)` : lit le JSON et renvoie `Lsm9ds1Config` gelé
  (`com_port`, `baudrate`, `channels`, `rate_hz`).
- Refuser un `schema_version` inconnu (`ValueError`), un nom de capteur
  inconnu, une cadence hors {25, 50, 100}, une clé obligatoire manquante.

## Design

- Pur côté domaine/application : lit un fichier, n'a aucun effet de bord.
- Le fichier runtime vit dans `.aefi_acquisition/configs/` (amorcé depuis
  `config_templates/` par le `ConfigBootstrapper`).
- Ne touche pas à `additional_sensors_config.json` : c'est un autre chemin
  (lecture via l'ADC), sans rapport avec la carte série.
