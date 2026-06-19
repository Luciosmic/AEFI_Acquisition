# measurement_result — Intention

## Rationale

Value object représentant le résultat d'une mesure à un point de scan, avec incertitude associée. Distinct de `VoltageMeasurement` (brut) : `MeasurementResult` intègre les métadonnées de qualité de mesure.

## Responsibility

- Stocker la valeur de mesure et son incertitude.
- Servir de type de sortie pour les services qui combinent mesure + validation qualité.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans les couches supérieures quand la qualité de mesure est pertinente.
