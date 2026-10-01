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
- **Durée de déplacement mesurée sur le banc** (2026-10-01, caractériseur
  `../characterization/`) : `move_to`/`move_by` sont non bloquants comme dans
  pylablib (la commande rend la main, l'axe roule) ; chaque axe met
  `t0 + |Δpas| / vitesse`, constantes `_MEASURED_TIMING_BY_HS` indexées par le
  HS des presets slow/medium/fast. Les deux axes commandés à la suite roulent
  donc ensemble (coût = axe le plus long), comme sur le banc. `is_moving` et
  `get_position` sont calculés depuis l'horloge (position interpolée
  linéairement, figée par `stop`).
- **Fidélité vérifiée** en repassant le caractériseur en `--dry-run` sur ce fake :
  niveau contrôleur identique au banc (v et t0 à ~0,01 près). Niveau port
  (avec le vrai `ArcusAdapter` au-dessus) : vitesse identique, mais t0
  **sous-estimé d'environ 0,19 s** — le banc paie une latence USB à chaque
  requête de l'adaptateur (polling `is_moving`, thread monitor, relecture de
  position) que ce fake ne simule pas, faute de mesure directe. Un test qui a
  besoin de la durée exacte vue par la boucle de scan utilise `MockMotionPort`
  (calé sur la mesure niveau port).
- Rampe d'accélération ignorée (modèle linéaire) : en fast (ACC = 500 ms), un
  déplacement de 2,5 mm est surestimé d'environ 0,1 s.
- Homing : toujours un court délai synchrone (`_simulate_move`), non caractérisé.
