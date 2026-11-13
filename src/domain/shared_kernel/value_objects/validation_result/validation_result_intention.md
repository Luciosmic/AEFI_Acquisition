---
type: value-object::solidai-ddd
tldr: "Stocker `is_valid: bool`, `errors: List[str]`, `warnings: List[str]`."
code: ["[[src/domain/shared_kernel/value_objects/validation_result/validation_result.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# validation_result — Intention

## Rationale

Value object encapsulant le résultat d'une validation domain (ex. `StepScanConfig.validate()`). Retourner un objet structuré plutôt qu'une exception permet à la couche applicative de collecter toutes les erreurs sans try/except imbriqués.

## Responsibility

- Stocker `is_valid: bool`, `errors: List[str]`, `warnings: List[str]`.
- Permettre l'accès à la liste complète des erreurs en une passe.

## Design

- **`@dataclass(frozen=True)`**.
- Pattern "collect-all-errors" : plus ergonomique que lever une exception à la première erreur.
