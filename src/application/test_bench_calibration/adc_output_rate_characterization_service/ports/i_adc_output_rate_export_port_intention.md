---
type: port::solidai-hexagonal
tldr: "Port sortant `i_adc_output_rate_export_port` : `export(result, captures)` : écrire un résumé par OSR, tous les intervalles entre fronts, et les formes d'onde brutes."
sens: sortant
code: "[[src/application/test_bench_calibration/adc_output_rate_characterization_service/ports/i_adc_output_rate_export_port.py]]"
---
# i_adc_output_rate_export_port — Intention

## Rationale

Une ODR affichée puis perdue à la fermeture de l'application ne sert pas de
référence ; et sans la forme d'onde brute, un autre critère de dépouillement
(seuil, tolérance des intervalles) ne pourrait pas être appliqué après coup.

## Responsibility

- `export(result, captures)` : écrire un résumé par OSR, tous les intervalles
  entre fronts, et les formes d'onde brutes ; rendre l'emplacement écrit.

## Design

- ABC pure, port sortant. Implémentations : `CsvAdcOutputRateExportPort`
  (dossier daté dans `AEFI_Acquisition_Exports`, noms de fichiers explicites),
  `FakeAdcOutputRateExportPort` (en mémoire).
- ponytail: pas encore d'`acquisition-parameters.json` — à brancher sur le
  même mécanisme que la caractérisation du débit une fois celui-ci relu et
  commité.
