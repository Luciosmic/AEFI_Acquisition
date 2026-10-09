# sample — Intention

## Rationale

Sans type d'échantillon, `record_samples` recevrait des listes de floats ou de mesures quelconques, ce qui signifie que « N échantillons valides » ne veut rien dire dans le domaine.

## Responsibility

- Représenter un échantillon ADC unique, immuable, dont la validité est garantie à la construction.

## Design

- Enveloppe un `AefiVoltageMeasurement` (la forme que le pipeline produit déjà) ; la finitude des six tensions est déjà imposée par `AefiVoltageMeasurement` (un NaN ne peut pas être construit, donc pas être échantillon) ; la moyenne reste calculée par `MeasurementStatisticsService`.
