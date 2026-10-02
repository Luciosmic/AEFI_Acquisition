# csv_adc_output_rate_export_port — Intention

## Rationale

La première mesure de l'ODR (2026-10-02) a dû être archivée à la main, ses
fichiers génériques (`waveform.csv`, `resultat.txt`) renommés pour être
lisibles dans le vault de thèse. Sans export intégré aux noms explicites,
chaque mesure de l'application referait ce travail, ou perdrait la forme
d'onde qui permet de refaire le dépouillement.

## Responsibility

- Écrire, dans `<YYYY-MM-DD_HHMMSS>_odr-adc-ads131a04-drdy-oscilloscope/` sous
  `~/Desktop/AEFI_Acquisition_Exports` :
  - `<stamp>_odr-drdy_resume-par-osr.csv` : en-tête `# clé,valeur` (instrument,
    f_MOD moyenne, écart relatif max, OSR restauré), puis une ligne par OSR ;
  - `<stamp>_odr-drdy_intervalles-fronts-descendants.csv` : chaque intervalle
    entre fronts, par OSR, avec le pas d'échantillonnage ;
  - `<stamp>_odr-drdy_formes-d-onde.npz` : formes d'onde brutes (t, v) par
    OSR, compressées (100 000 points par capture).
- Rendre le dossier écrit, ou un échec lisible.

## Design

- `csv` (bibliothèque standard), `numpy.savez_compressed` pour les formes
  d'onde. Dossier de base et horloge injectables (tests).
- Exceptions d'I/O → `OperationResult.fail`.
- ponytail: `acquisition-parameters.json` à ajouter (voir le port).
