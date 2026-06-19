# measurement_uncertainty — Intention

## Rationale

Value object définissant le critère de qualité de mesure acceptable pour un scan step-by-step (`max_uncertainty_volts`). Intégrer l'incertitude dans la configuration de scan (via `StepScanConfig`) rend les critères de qualité explicites et vérifiables par le domain.

## Responsibility

- Stocker `max_uncertainty_volts: float` : seuil maximal d'incertitude acceptable par position.
- Fournir la méthode `is_acceptable(measured_uncertainty: float) → bool`.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans `StepScanConfig` et potentiellement dans `MeasurementStatisticsService` pour valider la qualité des mesures moyennées.
