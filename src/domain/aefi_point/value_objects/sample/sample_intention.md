---
type: value-object::solidai-ddd
tldr: "Représenter un échantillon ADC unique, immuable, dont la validité est garantie à la construction."
code: ["[[src/domain/aefi_point/value_objects/sample/sample.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/aefi_point/aefi_point_intention]]"
---
# sample — Intention

## Rationale

Sans type d'échantillon, `record_samples` recevrait des listes de floats ou de mesures quelconques, ce qui signifie que « N échantillons valides » ne veut rien dire dans le domaine.

## Responsibility

- Représenter un échantillon ADC unique, immuable, dont la validité est garantie à la construction.

## Design

- Enveloppe un `AefiVoltageMeasurement` (la forme que le pipeline produit déjà) ; la finitude des six tensions est déjà imposée par `AefiVoltageMeasurement` (un NaN ne peut pas être construit, donc pas être échantillon) ; la moyenne reste calculée par `MeasurementStatisticsService`.
