# measurement_statistics_service — Intention

## Rationale

Calculer la moyenne des mesures de tension (6 canaux : X/Y/Z × In-Phase/Quadrature) sur plusieurs échantillons par position. Ce calcul appartient au domain car il exprime la règle métier "averaging_per_position" du scan step-by-step.

## Responsibility

- `calculate_statistics(measurements: List[VoltageMeasurement]) → VoltageMeasurement` : retourner la mesure moyennée.
- Garantir un résultat même avec une seule mesure (averaging = 1).

## Design

- **Service stateless** avec méthode(s) statique(s).
- Retourne un `VoltageMeasurement` (pas de type statistique séparé) : le résultat est directement utilisable par `StepScanExecutor` pour créer un `ScanPointResult`.
- Calcul simple (moyenne arithmétique composante par composante) : extensible vers pondération ou médiane sans changer l'interface.
