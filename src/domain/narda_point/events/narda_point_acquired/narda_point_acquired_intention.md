# narda_point_acquired — Intention

## Rationale

Sans fait publié à l'acquisition d'un point de champ, le `Scan` ne peut pas savoir que ses mesures de champ électrique sont complètes : la sonde reste un flux parallèle hors agrégat, et le scan se déclarerait terminé avec l'AEFI seul.

## Responsibility

- Fait passé : un point de champ a reçu exactement N échantillons (et leur baseline en mode différentiel) ; porte identité, scan, `point_index` (clé de corrélation avec le point AEFI et l'affichage), position, mesure moyennée, baseline éventuelle, libellés d'axes et nombre d'échantillons. L'unité est inline (URI QUDT `V-PER-M`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`. Émis par `NardaPoint.record_samples` uniquement. Topic : `"nardapointacquired"`.
- Respecte le contrat `ProbeAcquisitionEvent` du `Scan` sans l'importer : `source` (constante `NARDA_POINT_SOURCE = "narda_point"`) et `acquisition_id` (= `narda_point_id`) sont des propriétés.
- Remplace l'ancien événement de champ publié hors agrégat ; l'export et le service applicatif (UI) s'abonnent à celui-ci.
