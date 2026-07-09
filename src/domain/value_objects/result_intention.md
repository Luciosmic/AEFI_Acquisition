# result — Intention

## Rationale

Value object générique Result[T, E] pour les retours de méthodes domain et applicatives qui peuvent réussir ou échouer sans lever d'exception. Complémentaire à `OperationResult` : `result` est la version domain/générique, `OperationResult` est la version orientée opérations hardware.

## Responsibility

- Encapsuler une valeur de succès `T` ou une valeur d'erreur `E`.
- Exposer `is_ok()`, `value`, `error` comme accesseurs.

## Design

- **Generic `[T, E]`**.
- Utilisé dans les contextes domain où une opération peut échouer par design (ex. validation, calcul avec données invalides).
