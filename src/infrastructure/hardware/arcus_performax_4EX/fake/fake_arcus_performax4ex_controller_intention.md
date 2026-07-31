# fake_arcus_performax4ex_controller — Intention

## Rationale

Contrairement au MCU (AD9106/ADS131), Arcus n'a pas de couche "communicator"
série séparée : `ArcusPerformax4EXController` appelle directement `pylablib`/
la DLL vendeur dans chacune de ses méthodes. Le seul point d'injection
possible pour un simulateur réaliste est donc le contrôleur lui-même, pas une
couche transport en dessous — ce Fake réimplémente sa surface publique avec un
état interne réaliste, plutôt que de faker un objet `pylablib` interne.

Motivation identique au Fake MCU : en mode "mock" aujourd'hui, `MockMotionPort`
court-circuite entièrement `ArcusAdapter` (pas de worker thread, pas de
conversion mm↔steps, pas de garde homing) — aucun code réel n'est exercé.

## Responsibility

- Implémenter la surface publique consommée par `ArcusAdapter`,
  `ArcusPerformaxLifecycleAdapter` et `ArcusPerformax4EXAdvancedConfigurator` :
  `connect`, `disconnect`, `is_connected`, `move_to`, `move_by`, `home`,
  `home_both`, `stop`, `wait_move`, `set_position_reference`, `get_position`,
  `set_axis_params`/`get_axis_params(_dict)`, `get_status`, `is_moving`.
- Garder le même comportement de garde que le réel : `move_to`/`move_by`
  lèvent `RuntimeError` si l'axe n'est pas homé ou si non connecté ;
  `is_moving()` renvoie `False` (pas d'exception) si non connecté.

## Design

- État interne : position par axe, flags homed/moving, paramètres LS/HS/ACC/DEC
  par axe (mêmes valeurs par défaut que `ArcusPerformax4EXController.DEFAULT_PARAMS`).
- Déplacement simulé par un court délai synchrone (`_simulate_move`) plutôt
  qu'une interpolation — suffisant pour exercer le worker thread et la boucle
  de monitoring réels de `ArcusAdapter`, pas besoin de plus pour ce chantier.
