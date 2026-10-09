# scan_closure_failed — Intention

## Rationale

Sans événement d'échec, un handler qui n'arrive pas à rattacher un point acquis à son scan échoue en silence (le bus avale les exceptions), ce qui signifie un scan bloqué en STARTED sans trace, ce qui force l'opérateur à le découvrir par l'absence de complétion.

## Responsibility

- Rendre visible l'échec de rattachement d'un point à un scan : `scan_id`, `aefi_point_id`, `reason`.

## Design

- Pas de retry automatique ; la réconciliation par l'opérateur viendra plus tard.
- Émis par le handler applicatif (échec d'orchestration, pas un fait d'agrégat).
