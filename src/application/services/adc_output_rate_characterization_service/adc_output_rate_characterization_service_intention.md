# adc_output_rate_characterization_service — Intention

## Rationale

L'ODR de l'ADC a été mesurée une première fois (2026-10-02) par un script
hors de l'application, application fermée : il a fallu fermer le logiciel
de mesure pour libérer le port série, et rien ne garantissait que l'OSR du
registre était celui des mesures précédentes. Un OSR changé depuis
Hardware Advanced Config n'avait d'ailleurs jamais été vérifié comme
réellement appliqué par la puce. Sans ce use case dans l'application, la
grandeur la plus structurante de la chaîne d'acquisition (elle fixe la
durée d'un moyennage et les zéros du filtre de moyennage) reste une
mesure ad hoc, perdue avec son script.

## Responsibility

- `start_characterization(request)` :
  - valider la requête (voie 1-4, rapport de sonde positif, OSR acceptés par
    la puce, au moins 3 périodes par capture) ;
  - prendre la configuration avancée de l'ADC et le flux d'acquisition (tout
    ou rien) ;
  - refuser un balayage qui changerait l'OSR pendant que la lecture continue
    tourne (ses données seraient faussées) ;
  - lancer la mesure en tâche de fond.
- Mesure : pour chaque OSR demandé (ou l'OSR courant seul), l'écrire si
  besoin, laisser `settle_delay_s`, capturer DRDY sur assez de périodes,
  analyser (domaine), présenter le point.
- Fin : caractérisation (cohérence des `f_MOD` implicites), export, valeurs
  du catalogue ADC (`component_values`), restauration de l'OSR d'origine et
  des contrôles quoi qu'il arrive.

## Design

- Fenêtre de capture : `periods_per_capture` périodes attendues. La période
  attendue vient d'une estimation de `f_MOD` (4,096 MHz au départ, valeur
  mesurée le 2026-10-02), remplacée par la `f_MOD` implicite de chaque
  mesure. Elle ne sert qu'à choisir la base de temps : le résultat ne
  dépend que des fronts capturés.
- Propriétaire `"caractérisation ODR (DRDY)"` de la configuration `ads131a04`
  et du flux ; l'OSR est écrit par `IAdcOversamplingPort` sans persistance,
  puis restauré.
- Dépendances directes aux services d'acquisition et de configuration
  avancée pour leurs verrous (même précédent que la caractérisation du débit).
- ponytail: pas d'`acquisition-parameters.json` encore (voir le port
  d'export).
