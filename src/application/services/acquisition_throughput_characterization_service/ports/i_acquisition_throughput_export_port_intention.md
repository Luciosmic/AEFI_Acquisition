# i_acquisition_throughput_export_port — Intention

## Rationale

La caractérisation de 2024 a été perdue : elle vivait dans un tableur à
part. Sans export automatique des échantillons bruts à côté du résumé, une
caractérisation ne peut pas être refaite ni recomparée, et la couche
application écrirait elle-même des fichiers.

## Responsibility

- `export(result, samples)` : écrire le résumé (un point par `n_avg`, ajustement,
  contexte) et les échantillons bruts ; rendre l'emplacement écrit.

## Design

- ABC pure, port sortant. Implémentations : `CsvAcquisitionThroughputExportPort`
  (dossier daté dans `AEFI_Acquisition_Exports`),
  `FakeAcquisitionThroughputExportPort` (en mémoire).
- Échec d'écriture → `OperationResult.fail`, la caractérisation reste
  affichée.
