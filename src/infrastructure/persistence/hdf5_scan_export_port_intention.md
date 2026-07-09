# hdf5_scan_export_port — Intention

## Rationale

Implémentation HDF5 de `IScanExportPort` pour l'export structuré des résultats de scan 2D complets. Contrairement à `HDF5AcquisitionRepository` (persistence incrémentale par sample), cet adaptateur exporte la cartographie 2D complète avec ses métadonnées de configuration.

## Responsibility

- Exporter les points de résultat scan (position + mesure) dans un fichier HDF5 avec les métadonnées de configuration (zone, pattern, datetime).
- Organiser les données pour la relecture dans `plot_h5_images.py` et les outils d'analyse post-processing.

## Design

- **Séparation scan export vs acquisition repository** : deux contrats différents — l'export est one-shot à la fin du scan, la persistence est incrémentale pendant le scan.
- Implémente `IScanExportPort` dans `scan_application_service/`.
