# scan_export_service — Intention

## Rationale

Isoler la logique d'export des résultats de scan dans un service dédié pour préserver la cohésion de `ScanApplicationService`. L'export (HDF5, CSV) implique des opérations I/O qui ne doivent pas alourdir le service principal de scan.

## Responsibility

- Accepter les résultats d'un scan complété et les transmettre au port d'export configuré.
- Gérer les erreurs d'export sans affecter le cycle de vie du scan.

## Design

- **Dépendance sur `IScanExportPort`** : le format d'export est interchangeable via injection.
- Service séparé de `ScanApplicationService` pour respecter le Single Responsibility Principle.
