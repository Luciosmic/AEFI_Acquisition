# i_acquisition_data_repository — Intention

## Rationale

Définir le contrat de persistence des `AcquisitionSample` dans le domain, suivant le pattern Repository DDD. Le domain déclare QUOI persister, l'infrastructure décide COMMENT (HDF5, CSV, in-memory).

## Responsibility

- `save(scan_id: str, data: List[AcquisitionSample])` : persister un batch d'échantillons pour un scan donné.
- `find_by_scan(scan_id: str) → List[AcquisitionSample]` : retrouver tous les échantillons d'un scan.

## Design

- **ABC placé dans `domain/repositories/`** : frontière domain/infrastructure pour la persistence.
- Implémenté par `HDF5AcquisitionRepository` (Real) dans `infrastructure/persistence/`.
- L'interface domain ne connaît pas HDF5 — le domain reste pur.
