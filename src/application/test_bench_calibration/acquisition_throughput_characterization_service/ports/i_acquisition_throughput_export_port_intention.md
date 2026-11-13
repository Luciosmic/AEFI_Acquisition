# i_acquisition_throughput_export_port — Intention

## Rationale

La caractérisation de 2024 a été perdue : elle vivait dans un tableur à
part. Sans export automatique des échantillons bruts à côté du résumé, une
caractérisation ne peut pas être refaite ni recomparée, et la couche
application écrirait elle-même des fichiers. Le 2026-10-02, deux balayages
exportés n'ont pas pu être remis dans leur contexte (latence USB, flux
démarré à la main, voies de référence, position, version) : sans les
paramètres d'acquisition écrits dans le même dossier que les données, ces
conditions n'existent que dans le journal d'événements. Et si le service
construisait lui-même le document, il changerait à chaque évolution du
schéma de fichier — une cause de changement qui n'est pas la sienne.

## Responsibility

- `open_export(oversampling_ratio, excitation_label)` : créer l'emplacement
  de l'export au démarrage du balayage ; le rendre.
- `export(location, result, samples)` : écrire le résumé (un point par
  `n_avg`, ajustement, contexte) et les échantillons bruts ; rendre les
  fichiers écrits (nom, format, taille, SHA-256).
- `write_acquisition_parameters(location, parameters)` : (ré)écrire les
  paramètres d'acquisition — au démarrage (activité `running`), puis à la
  fin (`completed` / `failed`). Un document resté `running` signale un
  balayage interrompu.

## Design

- ABC pure, port sortant. Implémentations : `CsvAcquisitionThroughputExportPort`
  (dossier daté dans `AEFI_Acquisition_Exports`, `acquisition-parameters.json`
  au schéma 1.0 via `acquisition_parameters_v1_serializer`),
  `FakeAcquisitionThroughputExportPort` (en mémoire).
- Le port reçoit des DTO sans format (`AcquisitionParametersDTO`) : le
  format du fichier (schéma, unités UCUM, mise en page) est un choix de
  l'adaptateur.
- L'empreinte des fichiers est calculée par l'adaptateur qui les écrit : il
  est le seul à connaître les octets.
- Échec d'écriture → `OperationResult.fail`, la caractérisation reste
  affichée.
