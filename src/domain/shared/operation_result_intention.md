# operation_result — Intention

## Rationale

Encapsuler le résultat d'une opération (succès/échec) sans lever d'exception vers la couche appelante. `OperationResult[T, E]` force les appelants (notamment la UI via `MotionControlService`) à traiter les deux cas de manière explicite.

## Responsibility

- Représenter soit un succès avec valeur `T` (`OperationResult.ok(value)`), soit un échec avec erreur `E` (`OperationResult.fail(error)`).
- Exposer `is_success`, `value`, `error` comme accesseurs typés.

## Design

- **Generic `[T, E]`** : réutilisable pour n'importe quel type de retour et d'erreur.
- Placé dans `domain/shared/` : utilitaire domain partagé entre services applicatifs et domain.
- Alternative aux exceptions pour les erreurs "attendues" (échec de mouvement, limite atteinte) vs les exceptions "inattendues" (bug).
