# adapter_adc_oversampling_ads131a04 — Intention

## Rationale

Le balayage de l'OSR doit écrire le registre de l'ADC puis le remettre. Le
configurateur avancé (`ADS131A04AdvancedConfigurator.apply_config`)
persisterait chaque valeur intermédiaire dans `ads131a04_last_config.json`,
comme si l'opérateur l'avait choisie ; un arrêt brutal laisserait alors un
OSR de balayage comme réglage de démarrage.

## Responsibility

- Implémenter `IAdcOversamplingPort` via `ADS131Controller.set_oversampling_ratio`
  (même écriture de registre que le configurateur, diviseur ICLK conservé),
  sans persistance.
- Lire l'OSR courant dans le shadow du contrôleur ; liste des OSR acceptés
  (datasheet, tableau 30) ; identifiant `ads131a04`.

## Design

- Construit par `MCUCompositionRoot` (propriété `adc_oversampling`), qui
  possède le contrôleur.
- ponytail: l'OSR « courant » est le shadow du contrôleur — le protocole MCU
  ne relit pas les registres. La mesure DRDY sert justement à vérifier que
  le registre écrit est appliqué.
- Testé avec un contrôleur simulé.
