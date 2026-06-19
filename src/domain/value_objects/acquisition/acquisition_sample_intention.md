# acquisition_sample — Intention

## Rationale

Value object étendant `VoltageMeasurement` avec un timestamp de capture. Utilisé pour la persistence temporelle dans `IAcquisitionDataRepository` (HDF5) où le temps d'acquisition est une métadonnée essentielle pour la reproductibilité expérimentale.

## Responsibility

- Stocker les 6 composantes de tension + `timestamp: datetime`.
- Servir de type de persistence dans `HDF5AcquisitionRepository`.

## Design

- **`@dataclass(frozen=True)`** avec `timestamp` comme champ supplémentaire vs `VoltageMeasurement`.
- Le timestamp est stocké comme POSIX float dans HDF5 pour l'efficacité, mais exposé comme `datetime` dans le domain.
