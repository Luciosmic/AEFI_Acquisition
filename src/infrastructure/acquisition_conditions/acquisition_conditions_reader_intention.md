# acquisition_conditions_reader — Intention

## Rationale

Les conditions d'un balayage de débit existent déjà dans le système, mais
dispersées : catalogue des composants et configurations résolues des puces
(rassemblés par `AcquisitionSnapshotReader` pour l'export des scans),
mémoire du contrôleur AD9106 (la seule source fidèle quand la détection
synchrone compense la phase sans persister), OSR en mémoire du contrôleur
ADS131A04, rotation active du capteur, compensation de phase, port série
ouvert, position des moteurs. Sans un adaptateur qui les rassemble, soit le
service de caractérisation dépendrait de chacune de ces sources, soit une
seconde collecte dupliquerait celle du scan et divergerait (le cas qui a
produit `resolve_config` : deux lectures différentes d'une même config).

## Responsibility

- Implémenter `IAcquisitionConditionsPort` :
  - composants montés et caractérisation : section `hardware_configuration`
    de `AcquisitionSnapshotReader.read()` (réutilisée, pas recalculée) ;
  - réglages ADC : section `hardware_settings.ads131a04` (default + last
    résolus), OSR remplacé par la mémoire du contrôleur (valeur appliquée) ;
  - réglages AD9106 : mémoire du contrôleur (registres écrits), drapeaux de
    politique (`link_dds1_dds2`, quadrature, lien de gain DDS3/DDS4) depuis
    `hardware_settings.ad9106` ;
  - détection synchrone : compensation active ou non ;
  - montage du capteur (identifiant, date) et rotation active, avec
    l'identifiant de l'entrée de calibration appliquée retrouvé dans le
    registre ;
  - liaison série : port et débit ouverts par le communicateur ;
  - backends matériels (réel / simulé), fournis par la racine de composition.
- `read_bench_position()` : position des moteurs, ou un échec lisible.

## Design

- Les services applicatifs (calibration capteur, détection synchrone) et
  les contrôleurs sont passés comme **requêtes liées** (`Callable`) par la
  racine de composition : l'adaptateur ne connaît pas leurs classes.
- Chaque famille de faits est lue séparément ; toute exception la rend
  inconnue (`None`) avec sa raison dans `unknown` — le balayage n'échoue
  jamais pour une condition illisible.
- Désaccord OSR mémoire / config résolue : la mémoire l'emporte (valeur
  appliquée), décision loguée.
- L'identifiant de la calibration appliquée n'est pas exposé par
  `ActiveSensorRotationDTO` : retrouvé par `recorded_at` + montage ; ambigu
  ou absent → `None` (avertissement dans le document).
