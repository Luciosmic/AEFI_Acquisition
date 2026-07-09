# Persistence — Export et Stockage des Données

## Rationale
Ce module gère la persistance des données de scan et d'acquisition sur disque. Il offre deux formats d'export pour le scan (HDF5 scientifique, CSV lisible) et un repository pour les échantillons d'acquisition continue, tous implémentant les ports définis par la couche application.

## Responsibility
- `HDF5ScanExportPort` (`hdf5_scan_export_port.py`) : implémenter `IScanExportPort`. Exporte les résultats de scan dans un fichier HDF5 structuré (positions shape (N,2), mesures shape (N,6), écarts-types shape (N,6), métadonnées en attributs racine). Supporte l'écriture incrémentale point par point.
- `CsvScanExportPort` (`csv_scan_export_port.py`) : implémenter `IScanExportPort`. Exporte les résultats de scan dans un fichier CSV lisible (une ligne par point de scan). Format de vérification rapide.
- `HDF5AcquisitionRepository` (`hdf5_acquisition_repository.py`) : implémenter `IAcquisitionDataRepository`. Persiste des listes de `AcquisitionSample` dans des datasets HDF5 redimensionnables (compound dtype : timestamp + 6 composantes flottantes).

## Design
- Le répertoire de sortie par défaut est `.aefi_acquisition/scans/raw_data/` (gitignored, données runtime).
- Les fichiers HDF5 utilisent des datasets redimensionnables (`maxshape=(None,)`) pour permettre l'écriture incrémentale sans connaître le nombre total de points à l'avance.
- `configure()` doit être appelé avant `write_point()` : ce contrat est documenté dans l'interface `IScanExportPort`.
