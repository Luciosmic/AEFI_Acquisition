# scan_closure_failed — Intention

## Rationale

Sans événement d'échec, un handler qui n'arrive pas à rattacher une acquisition à son scan échoue en silence (le bus avale les exceptions), ce qui signifie un scan bloqué en STARTED sans trace, ce qui force l'opérateur à le découvrir par l'absence de complétion.

## Responsibility

- Rendre visible l'échec de rattachement d'une acquisition à un scan : `scan_id`, `source`, `acquisition_id` (génériques : n'importe quelle sonde), `reason`.

## Design

- Pas de retry automatique ; la réconciliation par l'opérateur viendra plus tard.
- Émis par le handler applicatif (échec d'orchestration, pas un fait d'agrégat).
