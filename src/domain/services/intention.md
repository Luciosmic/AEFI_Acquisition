# Services Domaine

## Rationale
Ce dossier contient les services domaine purs : logique métier complexe qui ne peut pas être attachée à un seul agrégat, sans effet de bord, sans I/O, déterministe et facilement testable.

## Responsibility
- `ScanTrajectoryFactory` : générer la séquence ordonnée de positions à visiter pour un scan donné. Supporte les patterns SERPENTINE (alternance de direction), RASTER (gauche→droite systématique) et COMB (par colonnes). Retourne un `ScanTrajectory` immuable.
- `MeasurementStatisticsService` : calculer la moyenne et l'écart-type (correction de Bessel, n-1) d'une liste de `VoltageMeasurement`. Retourne un `VoltageMeasurement` agrégé avec les champs `std_dev_*` renseignés.

## Design
- Les deux services exposent uniquement des méthodes statiques ou de classe : pas d'état interne, pas de dépendance infrastructure.
- `ScanTrajectoryFactory.create_trajectory` opère sur `StepScanConfig` (valeur objet domaine) et retourne `ScanTrajectory` (valeur objet domaine) — aucune fuite d'infrastructure.
- `MeasurementStatisticsService` utilise le calcul deux-passes (somme puis variance) pour minimiser les erreurs numériques.
