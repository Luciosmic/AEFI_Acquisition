# aefi_point_acquired — Intention

## Rationale

Sans fait publié à l'acquisition d'un point, le handler du `Scan` doit relire l'état de l'agrégat point pour savoir où en est le scan, ce qui couple les deux agrégats et casse « un agrégat par transaction ».

## Responsibility

- Fait passé : un point a reçu exactement N échantillons valides ; porte identité, scan, position, mesure moyennée et nombre d'échantillons. L'unité de la mesure est inline (URI QUDT) pour que le fait soit rejouable sans convention externe.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent` ; `occurred_on` vient de la base.
- Émis par `AefiPoint.record_samples` uniquement. Topic : `"aefipointacquired"`.
- L'unité de la position n'est pas inlinée : `Position2D` ne la déclare pas, à trancher quand ce VO sera enrichi.
- Respecte le contrat `ProbeAcquisitionEvent` du `Scan` sans l'importer : `source` (constante `AEFI_POINT_SOURCE = "aefi_point"`) et `acquisition_id` (= `aefi_point_id`) sont des propriétés, aucun champ ajouté.
