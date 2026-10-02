# scan_application_service — Intention

## Rationale

Orchestrer le cycle de vie d'un scan 2D step-by-step. Ce service est le point central qui coordonne la motion, l'acquisition et l'export tout en restant indépendant des implémentations hardware. Sans ce service, la logique d'orchestration serait soit dans la UI (violation de séparation des responsabilités) soit dans le domain (pollution par l'I/O).

## Responsibility

- Accepter un `Scan2DConfigDTO` (`execute_scan`, grille) ou un `LineScanConfigDTO` (`execute_line_scan`, ligne theta) et déclencher la séquence complète : validation → création de l'agrégat `StepScan` → génération de trajectoire (factory propre à chaque forme) → boucle de scan commune (`_start_scan`).
- Exécuter une grille en **fly-scan** quand `Scan2DConfigDTO.fly_scan` est vrai (`_execute_fly_scan_loop`) : exploration rapide avant un step-scan de mesure. Pour chaque ligne de l'axe rapide : aller au début de la ligne, déclencher le chronomètre, balayer jusqu'au bout d'une traite pendant que le flux ADC continue ; les positions rapportées par le contrôleur (`PositionUpdated`, ~150 ms) et les échantillons ADC passent **en direct** par `FlyScanLineProjector` (domaine), qui rend chaque point de grille dès que la trace l'a dépassé et qu'un échantillon postérieur est arrivé — jamais en rafale en fin de ligne. Même agrégat, mêmes événements, même export que le step-scan.
- Gérer le cycle de vie du scan : pause, resume, cancel via l'exécuteur.
- S'abonner aux événements domain publiés sur `IDomainEventBus` et les forwarder vers `IScanOutputPort` (Presenter).
- Exposer une query `get_status() → ScanStatusDTO` sans dépendance infrastructure.

## Design

- **Injection de dépendances** : `IMotionPort`, `IAcquisitionPort`, `IDomainEventBus`, `IScanExecutor`, `IScanOutputPort` sont tous injectés au constructeur.
- **Séparation Commands/Queries** : méthodes `execute_scan`, `pause_scan`, `resume_scan`, `cancel_scan` (commands) vs `get_status` (query).
- **Event forwarding** : s'abonne lui-même au bus dans `__init__` pour transposer les événements domain vers le port de sortie UI — évite le couplage direct Executor→Presenter.
- **Traduction DTO→Domain** : `_to_domain_config()` isole la conversion afin que le domain ne voie jamais les DTOs applicatifs.
- **Fly-scan sans synchronisation** : aucune corrélation moteur/ADC, seulement un chronomètre côté service (début de ligne = appel `move_to`, fin = retour de `wait_for_motion`) et l'hypothèse de vitesse constante. Deux approximations assumées, acceptables pour une exploration :
  - synchronisation logicielle : positions et échantillons horodatés à leur réception côté Python ; latence USB de lecture de position et de l'ADC non compensées (quelques mm en fast) — acceptable pour une exploration ;
  - une position tous les ~150 ms : trace linéaire entre deux positions (rampe approchée par morceaux) ;
  - la position finale lue sur le port ferme la trace en fin de ligne.
- Un modèle « vitesse constante + demi-rampe » a été essayé avant : sur le banc en fast il courait devant le moteur (3,31 s prévues pour 3,80 s réelles, ~30 mm d'erreur en bout de ligne). La vitesse de consigne (`get_cruise_speed_mm_s`) ne sert plus qu'au délai max de la ligne.
- La fin de mouvement est interrogée par attentes courtes (`FLY_MOTION_POLL_S`) pendant que les échantillons sont projetés ; délai max d'une ligne = 2 × durée prévue + 10 s. Par ligne : nombre d'échantillons, de positions, de points émis en direct et en fin de ligne, durée.
- En fly-scan : une ligne commencée va au bout (le moteur n'est pas arrêté) ; l'annulation arrête aussitôt le traitement ; une pause en cours de ligne garde les points dépassés et les ajoute à la reprise, la ligne suivante attend la reprise ; sondes auxiliaires (Narda) ignorées ; mode différentiel refusé par la config.
