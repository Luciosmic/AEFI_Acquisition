---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 5 suite]]"
doc_type: constat
statut: to_validate
---

# Adaptateurs sous `persistence/` et `execution/` : un dossier par adaptateur, ou un dossier par thème

**Constat** : 21 erreurs `adaptateur-mal-place`. H16 veut `infrastructure/<adaptateur>/<adaptateur>.py`. `infrastructure/persistence/` tient 16 adaptateurs (dépôts réels, exports CSV et HDF5), `infrastructure/execution/` en tient 2, et `hardware/composite_hardware_initialization_port` est à côté de ses appareils. L'humain a tranché pour `hardware/<appareil>/`, pas pour ces deux dossiers.

Les 19 Fakes `fake-mal-place` qui en dépendent (`persistence/calibration/fake/`, `execution/fake/`) suivent la même décision : un Fake va près de son réel.

## Deux voies

1. **Un dossier par adaptateur** sous `infrastructure/` : `real_operator_repository/`, `csv_scan_export_port/`, etc. Une vingtaine de déplacements et d'imports à suivre, tests et intentions avec.
2. **Un dossier par thème, comme pour `hardware/`** : `persistence/<contexte>/` et `execution/` déclarés comme regroupements voulus. Demande un ajustement de H16 dans solidai-hexagonal (le dossier thème tient plusieurs adaptateurs).

Recommandation : la voie 2, pour la cohérence avec la décision sur `hardware/` et le coût.
