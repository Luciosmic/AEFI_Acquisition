# measured_object_name_blank_error — Intention

## Rationale

Un objet mesuré enregistré sans nom (champ validé vide, ou que des espaces)
apparaîtrait comme une ligne blanche dans la liste et serait exporté comme
un objet sans description : la traçabilité promise serait vide sans que rien ne le
signale.

## Responsibility

- Nommer un seul refus métier : « un objet mesuré a un nom » (invariant I2 du
  registre `MeasuredObjectRegistry`).

## Design

- Sous-classe de `ValueError`, comme les autres erreurs domaine du projet.
- Levée par `MeasuredObjectRegistry.register` ; traduite par `MeasuredObjectService` en
  refus du use case (`MeasuredObjectNameBlank`).
- Testé via son émetteur : `measured_object_registry_test.py`.
