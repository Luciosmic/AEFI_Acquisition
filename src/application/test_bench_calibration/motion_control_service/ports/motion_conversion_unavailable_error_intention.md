# motion_conversion_unavailable_error — Intention

## Rationale

Sans erreur nommée, un adaptateur de mouvement qui n'a pas de conversion mm/impulsion lève une `RuntimeError` anonyme : la couche application ne peut pas la distinguer d'une panne matérielle, la traite comme un échec technique, et l'application se ferme au démarrage au lieu d'inviter l'opérateur à calibrer. La conversion est une promesse du port (« je ne bouge pas tant que la transmission n'est pas appliquée ») : son refus doit avoir un nom.

## Responsibility

- Nommer le refus d'un port de mouvement dont la distance par impulsion n'a pas été appliquée (`set_microns_per_pulse` jamais appelé).
- Rester une `RuntimeError` : le code existant qui capture `RuntimeError` continue de fonctionner.

## Design

- Déclarée à côté du port qui la lève (`IMotionPort`), levée par les adaptateurs réels, jamais par le domain.
- Pas de valeur par défaut silencieuse : cette erreur est la barrière, pas un cas à contourner.
