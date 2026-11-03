# operator_name_blank_error — Intention

## Rationale

Un opérateur enregistré sans nom (champ validé vide, ou que des espaces)
apparaîtrait comme une ligne blanche dans la liste et serait exporté comme
un agent anonyme : la traçabilité promise serait vide sans que rien ne le
signale.

## Responsibility

- Nommer un seul refus métier : « un opérateur a un nom » (invariant I2 de
  la FA `_system/thoughts_interface/fa_operator_traceability.md`).

## Design

- Sous-classe de `ValueError`, comme les autres erreurs domaine du projet.
- Levée par `OperatorRegistry.register` ; traduite par `OperatorService` en
  refus du use case (`OperatorNameBlank`).
- Testé via son émetteur : `operator_registry_test.py`.
