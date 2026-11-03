# motion_conversion_banner_model — Intention

## Rationale

Sans view model, le panneau de mouvement devrait importer le DTO d'état ou l'événement domain pour afficher « banc non calibré » — ou afficher un message générique qui n'indique ni la grandeur manquante ni où la saisir.

## Responsibility

- `visible`, `headline`, `detail` : le contenu du bandeau, en texte.
- `not_calibrated(...)` / `calibrated()` : fabriques depuis les primitives du DTO d'état.

## Design

- `@dataclass(frozen=True)`, aucune dépendance Qt, application ou domain.
- Consommé par `MotionPanelCompact` et `ScanControlPanel` via des signaux de presenter.
