# source_geometry_inconsistent_error — Intention

## Rationale

Sans ce type, le chevauchement de sphères (entité) et l'impossibilité de
placer les sphères dans le plan (solveur) remontent comme des `ValueError`
anonymes. L'application ne peut alors pas distinguer « l'opérateur a saisi une
mesure impossible » d'un bug de programmation, et l'erreur visible dans l'UI
dépend de messages d'exception attrapés au hasard.

## Responsibility

- Nommer une seule condition métier : les mesures au pied à coulisse ne
  décrivent aucune géométrie physiquement possible des 4 sphères.

## Design

- Sous-classe de `ValueError` (rétrocompatible avec les appelants existants).
- Le message nomme la grandeur fautive (`D_S1_S2`, triangle `S1-S2-S3`…) pour
  que l'opérateur sache quelle mesure reprendre.
- Testé via ses émetteurs : `source_geometry_calibration_entry_test.py` et
  `source_frame_solver_test.py`.
