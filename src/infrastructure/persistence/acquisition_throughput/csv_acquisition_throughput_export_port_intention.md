# csv_acquisition_throughput_export_port — Intention

## Rationale

La caractérisation du débit de 2024 a été perdue faute d'avoir été rangée
avec ses données. Sans export systématique, chaque balayage ne vit que dans
l'UI et disparaît à la fermeture ; et sans les échantillons bruts, un autre
critère de dépouillement ne pourrait pas être appliqué après coup.

## Responsibility

- Écrire, dans un dossier daté `<YYYY-MM-DD_HHMMSS>_mcuThroughput_osr<OSR>_excitation-<cond>`
  sous `~/Desktop/AEFI_Acquisition_Exports` :
  - `summary.csv` : un point par `n_avg` (période, débits, σ par voie, bruit
    en 1 s), précédé du contexte (OSR, excitation, T₀, ODR, écart au modèle,
    `n_avg` recommandé) en lignes de commentaire `#` ;
  - `samples.csv` : chaque échantillon brut (`n_avg`, index, horodatage,
    6 voies).
- Rendre le chemin du dossier, ou un échec lisible.

## Design

- `csv` de la bibliothèque standard. Dossier de base injectable (tests).
- Les exceptions d'I/O sont traduites en `OperationResult.fail`.
