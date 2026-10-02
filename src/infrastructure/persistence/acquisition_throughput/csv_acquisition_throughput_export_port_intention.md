# csv_acquisition_throughput_export_port — Intention

## Rationale

La caractérisation du débit de 2024 a été perdue faute d'avoir été rangée
avec ses données. Sans export systématique, chaque balayage ne vit que dans
l'UI et disparaît à la fermeture ; et sans les échantillons bruts, un autre
critère de dépouillement ne pourrait pas être appliqué après coup. Le
2026-10-02, deux balayages exportés n'ont pas pu être remis dans leur
contexte faute de paramètres d'acquisition à côté des données ; et un
document écrit seulement à la fin disparaît avec un balayage qui plante.

## Responsibility

- `open_export` : créer, au démarrage, un dossier daté
  `<YYYY-MM-DD_HHMMSS>_mcuThroughput_osr<OSR>_excitation-<cond>` sous
  `~/Desktop/AEFI_Acquisition_Exports`.
- `export` : y écrire
  - `summary.csv` : un point par `n_avg` (période, débits, σ par voie, bruit
    en 1 s), précédé du contexte (OSR, excitation, T₀, ODR, écart au modèle,
    `n_avg` recommandé) en lignes de commentaire `#` ;
  - `samples.csv` : chaque échantillon brut (`n_avg`, index, horodatage ISO
    8601 avec décalage, 6 voies) ;
  et rendre pour chacun nom, format, taille et SHA-256.
- `write_acquisition_parameters` : (ré)écrire `acquisition-parameters.json`
  au schéma 1.0 (`acquisition_parameters_v1_serializer`).
- Rendre un échec lisible pour toute erreur d'écriture.

## Design

- `csv`, `json`, `hashlib` de la bibliothèque standard. Dossier de base et
  horloge injectables (tests).
- Les noms de colonnes viennent de `VALUE_CHANNELS` (DTO) : une seule
  source pour l'écriture et pour leur description dans le document.
- Le JSON est écrit dans un fichier temporaire puis renommé : jamais de
  document à moitié écrit.
- Les exceptions d'I/O sont traduites en `OperationResult.fail`.
