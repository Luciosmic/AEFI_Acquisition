# aefi_line_acquired — Intention

## Rationale

Sans fait publié à l'acquisition d'une ligne, le handler du `Scan` doit relire l'agrégat ligne pour savoir où en est le scan, ce qui couple les deux agrégats et casse « un agrégat par transaction ».

## Responsibility

- Fait passé : une ligne a reçu tous ses points de grille ; porte identité, scan, rang de la ligne, points (position + mesure) et leur nombre. L'unité de la mesure est inline (URI QUDT), le fait est rejouable sans convention externe.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`. Topic : `"aefilineacquired"`.
- Émis par `AefiLine.record_points` uniquement.
- Respecte `ProbeAcquisitionEvent` sans l'importer : `source` (`AEFI_LINE_SOURCE = "aefi_line"`) et `acquisition_id` (= `aefi_line_id`) sont des propriétés.
