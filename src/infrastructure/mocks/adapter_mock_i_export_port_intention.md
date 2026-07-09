# adapter_mock_i_export_port — Intention

## Rationale

Mock de `IScanExportPort` pour les tests de `ScanExportService` sans écriture de fichier.

## Responsibility

- Implémenter `IScanExportPort` en mémoire.
- Capturer les données exportées pour vérification dans les tests.

## Design

- **`infrastructure/mocks/`**.
- Spy attribute : `exported_data` pour assertions sur le contenu exporté.
