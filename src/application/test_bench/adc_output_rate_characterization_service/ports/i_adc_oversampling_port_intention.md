# i_adc_oversampling_port — Intention

## Rationale

Balayer l'OSR exige d'écrire le registre de l'ADC puis de le remettre ; sans
port, le use case manipulerait le contrôleur ADS131A04 et ses codes de
registre. Passer par le configurateur avancé persisterait au contraire chaque
valeur intermédiaire comme réglage de l'opérateur.

## Responsibility

- `get_oversampling_ratio()` / `set_oversampling_ratio(osr)` : lire / écrire
  l'OSR dans le registre, sans persistance.
- `get_allowed_oversampling_ratios()` : les OSR acceptés par la puce
  (datasheet, tableau 30).
- `get_configuration_hardware_id()` : l'identifiant Hardware Advanced Config
  de l'ADC, verrouillé pendant le balayage.

## Design

- ABC pure, port sortant. Implémentations : `AdapterAdcOversamplingAds131a04`
  (contrôleur ADS131A04 du MCU), `FakeAdcOversamplingPort` (en mémoire).
- L'OSR « courant » est celui du shadow du contrôleur (le registre n'est pas
  relisible par le protocole MCU) : dette consignée dans l'adaptateur.
