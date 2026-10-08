# source_geometry_preview_rejected — Intention

## Rationale

L'aperçu en direct est recalculé à chaque modification d'une mesure : les
états intermédiaires impossibles (sphères qui se chevauchent, triangle qui ne
ferme pas) sont un résultat attendu, pas une exception. Sans un type de
résultat nommé, le presenter devrait attraper l'erreur du domain, ce qui
couple l'interface aux règles métier.

## Responsibility

- Résultat d'échec unique de `preview_source_frame`, porteur de la raison
  lisible fournie par le domain.

## Design

- `@dataclass(frozen=True)` avec `reason: str`, renvoyé dans un
  `OperationResult.fail(...)`.
- Testé via `source_geometry_calibration_service_test.py`.
