# motion_timing_characterizer — Intention

## Rationale

Sans mesure sur le banc réel, les doubles de test moteur (`MockMotionPort`, `FakeArcusPerformax4EXController`) répondent en un délai fixe, quelle que soit la distance : un pas de 2,5 mm et une traversée de 600 mm coûtent pareil. Les tests applicatifs valident donc une boucle de scan qui ne voit jamais un déplacement long, ce qui signifie que tout ce qui dépend de la durée réelle d'un mouvement (timeout de 30 s du scan et de l'adaptateur, ETA, mode slow sur une grande distance) n'est jamais exercé — ce qui force à le découvrir sur le banc, pendant une acquisition. Inventer une vitesse dans le fake ne règle rien : sans valeur sourcée d'une mesure, le fake impose une qualité de service que le hardware ne promet pas.

## Responsibility

- Mesurer, sur le banc réel, la durée d'un déplacement en fonction de la distance, pour chaque mode de vitesse (`slow`, `medium`, `fast`).
- Ajuster le modèle **t = t0 + max(|dx|, |dy|) / v** par mode, à deux niveaux :
  - `controller` : commande driver → axes arrêtés **et** à la position cible (ce que `FakeArcusPerformax4EXController` doit reproduire) ;
  - `port` : `ArcusAdapter.move_to` → événement `MotionCompleted` (ce que voit la boucle de scan, ce que `MockMotionPort` doit reproduire).
- Produire un CSV brut (une ligne par déplacement) et un JSON de synthèse (v, t0, résidus, paramètres contrôleur relus, calibration) — source des constantes nommées des fakes.

## Design

- **Modèle linéaire** : les deux axes bougent en même temps (coût = max des deux), la rampe d'accélération est négligeable (constaté sur le banc) — pas de modèle trapèze. Les déplacements `diag` (dx = dy) à côté des `x` seuls vérifient le max() à peu de frais : leur résidu moyen doit rester ~0.
- **Conversion mm ↔ impulsions** : lue dans la transmission mécanique courante (`.aefi_acquisition/calibrations/`, amorcée par l'appli au premier démarrage), comme l'appli ; `--microns-per-pulse` la remplace (le `--dry-run` des tests l'utilise). L'adaptateur n'a plus de facteur à lui.
- **Plan** : allers-retours autour d'un centre (600, 600 par défaut), les deux sens mesurés ; ordre tiré au hasard à l'intérieur d'un mode, un seul changement de vitesse par mode ; distances 2,5 → 100 mm.
- **Fin de mouvement côté contrôleur** : `is_moving` peut rester False juste après la commande (c'est la raison des 0,25 s d'attente dans `ArcusAdapter`) — le mouvement est terminé quand les axes sont arrêtés ET à la position cible.
- **Niveau `controller`** mesuré avec l'adaptateur désactivé (pas de contention du thread monitor) ; niveau `port` avec l'adaptateur actif, tel que l'app l'utilise.
- **Sécurité** : confirmation opérateur avant tout mouvement, homing si nécessaire, app fermée (l'USB n'accepte qu'un client).
- `--dry-run` : même script sur `FakeArcusPerformax4EXController` — sert de test de bout en bout sans banc.
- Script outil (lancé à la main, hors suite pytest) ; seules les parties pures (`plan_moves`, `fit`) et le dry-run sont testés.
