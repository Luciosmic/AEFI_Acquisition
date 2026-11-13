# adapter_acquisition_averaging_mcu — Intention

## Rationale

`n_avg` a déjà un écrivain unique, `MCUAdvancedConfigurator` (onglet Hardware
Config), et l'OSR vit dans le shadow de registres de `ADS131Controller`. Sans
cet adaptateur, la caractérisation du débit dupliquerait l'écriture de
`mcu_last_config.json` — deux écrivains pour un même réglage.

## Responsibility

- Implémenter `IAcquisitionAveragingPort` : `get/set_n_avg` via le
  configurateur MCU, bornes `NAVG_MIN`/`NAVG_MAX`, OSR depuis
  `ads131_controller.memory_state["Oversampling_ratio"]`.
- Traduire les exceptions du configurateur (hors bornes, fichier non
  inscriptible) en `OperationResult.fail`.

## Design

- Construit par `MCUCompositionRoot` (propriété `acquisition_averaging`), qui
  possède le configurateur et le contrôleur.
- Un `n_avg` changé ici n'est pas reflété dans l'onglet Hardware Config tant
  qu'il n'est pas rechargé ; la caractérisation restaure de toute façon la
  valeur d'origine.
