# scan_type — Intention

## Rationale

Enum ou value object définissant le type de scan (ex. 1D, 2D, 3D, circular). Utile pour les exports et les métadonnées de fichiers HDF5 afin d'identifier le type de cartographie produite.

## Responsibility

- Définir les types de scan disponibles dans le système AEFI.

## Design

- **`enum.Enum`**.
- Stocké dans les métadonnées d'export HDF5 et utilisé pour le nommage des datasets.
