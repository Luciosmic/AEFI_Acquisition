# sensor_response_degenerate_error — Intention

## Rationale

Sans ce type, des réponses capteur nulles ou presque colinéaires (excitation
coupée, capteur débranché, bruit seul) produiraient quand même des angles —
n'importe lesquels — ou une exception numérique anonyme. L'application ne
pourrait pas dire à l'opérateur « la mesure ne permet pas de déterminer le
montage », seulement planter ou proposer un P absurde.

## Responsibility

- Nommer une seule condition métier : les réponses du capteur aux
  excitations X et Y ne déterminent pas les angles de montage.

## Design

- Sous-classe de `ValueError`, comme `SourceGeometryInconsistentError`.
- Le message donne la grandeur fautive (réponse nulle, angle entre réponses).
- Testé via son émetteur : `sensor_mounting_solver_test.py`.
