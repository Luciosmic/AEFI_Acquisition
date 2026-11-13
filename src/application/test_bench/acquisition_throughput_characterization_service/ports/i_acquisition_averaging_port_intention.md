# i_acquisition_averaging_port — Intention

## Rationale

`n_avg` vit dans `mcu_last_config.json`, relu par l'adaptateur ADC avant
chaque échantillon. Sans ce port, la caractérisation du débit écrirait ce
fichier elle-même : la couche application connaîtrait un chemin disque et un
format JSON, et ses tests modifieraient la configuration runtime réelle.

## Responsibility

- `get_n_avg()` / `set_n_avg(n)` : lire / appliquer le moyennage MCU.
- `get_n_avg_range()` : bornes acceptées par le MCU (1-127 aujourd'hui).
- `get_oversampling_ratio()` : l'OSR de l'ADC sous lequel la mesure est
  faite (enregistré avec le résultat, la courbe en dépend).
- `get_configuration_hardware_ids()` : les identifiants Hardware Advanced
  Config des réglages qu'il lit ou écrit (`mcu`, `ads131a04`) — verrouillés
  pendant la caractérisation. C'est l'adaptateur qui sait quels
  configurateurs portent `n_avg` et l'OSR, pas le use case.

## Design

- ABC pure, port sortant (Application → Infrastructure).
- Implémentations : `AdapterAcquisitionAveragingMcu` (configurateur MCU +
  contrôleur ADS131A04), `FakeAcquisitionAveragingPort` (en mémoire, tests).
- `set_n_avg` rend un `OperationResult` : un fichier non inscriptible est un
  échec attendu, pas une erreur de programmation.
