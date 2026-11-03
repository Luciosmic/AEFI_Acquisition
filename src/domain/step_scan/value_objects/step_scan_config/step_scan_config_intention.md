# step_scan_config — Intention

## Rationale

Value object immuable regroupant tous les paramètres d'un scan step-by-step. Rendre la configuration atomique et validée à la construction évite les états partiellement configurés dans `ScanApplicationService` et `StepScanExecutor`.

## Responsibility

- Encapsuler : zone de scan, nb de points X/Y, pattern, délai de stabilisation, averaging par position, incertitude de mesure.
- Valider les contraintes à la construction (`__post_init__`).
- Calculer `total_points()` et `estimated_duration_seconds()` comme dérivés purs.
- Fournir `validate() → ValidationResult` pour l'usage par le service applicatif.
- Porter le choix `fly_scan` (exploration rapide sur la même grille, cf. `fly_scan_line_projector`) et `points_per_line()` (nb de points le long de l'axe rapide). Refuser un fly-scan en mode différentiel ou avec moins de 2 points par ligne.

## Design

- **`@dataclass(frozen=True)`** : garantit l'immuabilité — la config ne change pas pendant l'exécution.
- La validation dans `__post_init__` est la première ligne de défense ; `validate()` retourne un `ValidationResult` pour l'usage applicatif non-exceptionnel.
- `estimated_duration_seconds()` est une estimation rough (100ms/sample) — ne compte pas le temps de mouvement.
- `fly_scan` est un booléen sur la config de grille plutôt qu'une config dédiée : le fly-scan explore la zone que le step-scan mesurera ensuite, avec la même grille — seule la façon de la parcourir change. `stabilization_delay_ms` et `averaging_per_position` sont alors ignorés (et l'estimation de durée ne vaut plus).
