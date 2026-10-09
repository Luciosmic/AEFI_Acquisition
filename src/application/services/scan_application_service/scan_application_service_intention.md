# scan_application_service — Intention

## Rationale

Orchestrer le cycle de vie d'un scan 2D step-by-step. Ce service est le point central qui coordonne la motion, l'acquisition et l'export tout en restant indépendant des implémentations hardware. Sans ce service, la logique d'orchestration serait soit dans la UI (violation de séparation des responsabilités) soit dans le domain (pollution par l'I/O).

## Responsibility

- Accepter un `Scan2DConfigDTO` (`execute_scan`, grille) ou un `LineScanConfigDTO` (`execute_line_scan`, ligne theta) et déclencher la séquence complète : validation → création de l'agrégat `StepScan` (`FlyScan` en fly-scan) → génération de trajectoire (factory propre à chaque forme) → boucle de scan commune (`_start_scan`).
- Exécuter une grille en **fly-scan** quand `Scan2DConfigDTO.fly_scan` est vrai (`_execute_fly_scan_loop`) : exploration rapide avant un step-scan de mesure. Pour chaque ligne de l'axe rapide : aller au début de la ligne, déclencher le chronomètre, balayer jusqu'au bout d'une traite pendant que le flux ADC continue ; les positions rapportées par le contrôleur (`PositionUpdated`, ~150 ms) et les échantillons ADC passent **en direct** par `FlyScanLineProjector` (domaine), qui rend chaque point de grille dès que la trace l'a dépassé et qu'un échantillon postérieur est arrivé — jamais en rafale en fin de ligne. Même cycle de vie, mêmes événements, même export que le step-scan ; `FlyScan` garde ses points et son auto-complétion jusqu'à l'étape 8 (`AefiLine`).
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

### Coexistence `StepScan` / `Scan` fin (step-scan et line-scan, hors fly-scan)

- `IUnitOfWork` est injecté (obligatoire, par mot-clé) ; `main.py` instancie `InMemoryUnitOfWork` puis `ScanClosureHandler` **avant** ce service, pour que `ScanCompleted` sorte pendant la diffusion de `AefiPointAcquired`.
- `_start_scan` crée le `Scan` fin (même id que le `StepScan`) en deux UoW fermées avant la soumission de la boucle : `PENDING` observable (zéro événement) puis `STARTED`. Le fly-scan n'en crée pas et garde l'héritage.
- `StepScan` est une coque de cycle de vie sans points : statuts, pause/resume/cancel/fail, et émission de `ScanStarted`, `ScanPointAcquired`, `ScanFailed`, `ScanCancelled`, `ScanPaused`, `ScanResumed`. Chaque point est acquis dans un `AefiPoint` (une UoW par point) ; le handler clôt le `Scan` dans une transaction séparée.
- **Progression par compteurs locaux** : `_acquired_count` / `_expected_total` (entiers remis à zéro par scan dans `_start_scan`, écrits par la boucle, lus par l'UI/MCP) alimentent `get_status`, `present_scan_progress` et l'index de pause/resume. « Dernier point » = `_acquired_count == _expected_total`.
- **Émetteur unique de `ScanCompleted` par scan** : en step/line-scan c'est le `Scan` fin (via le handler) ; `StepScan` n'en émet plus. Le service s'abonne à `scancompleted` et appelle `StepScan.mark_completed()` pour le scan courant (avant le forward vers le presenter). En fly-scan, `FlyScan` émet le sien ; `mark_completed` est alors sans effet (loggé).
- **Pause en fin d'acquisition** : une fois `_acquired_count == _expected_total`, `pause_scan` est un no-op loggé (le scan reste `RUNNING` entre le dernier point et `ScanCompleted`).
- **Annulation en fin d'acquisition ou après la fin** : comme la pause, `cancel_scan` est un no-op loggé quand `_acquired_count >= _expected_total` (sinon le Scan fin publierait `ScanCompleted` après `ScanCancelled`) et quand le scan est déjà COMPLETED/FAILED/CANCELLED (l'arrêt système l'appelle sans condition : ne plus lever, sinon l'arrêt est classé en échec).
- Seuls la boucle et le démarrage touchent l'UoW (instance unique, non thread-safe) ; pause/resume/cancel/`get_status` (thread UI) n'y accèdent jamais.
- Ordre au dernier point : `ScanPointAcquired` hérité (avant le commit — fait publié avant validation transactionnelle, accepté pendant la coexistence, sinon l'export se ferme sur `ScanCompleted` et perd la dernière ligne), libération des flux, puis commit de l'`AefiPoint`.
- **`ScanClosureFailed`** : le handler est synchrone et le bus avale les exceptions ; ce service s'y abonne, fait échouer le `StepScan` (toujours `RUNNING` à ce moment, y compris au dernier point) et publie `ScanFailed` (l'export se ferme, l'UI affiche l'échec). La boucle s'arrête au point suivant ; les flux sont alors libérés après `ScanFailed` (écart assumé à la règle « flux libérés avant l'événement terminal »).
- **Scan « zombie »** : le `Scan` fin n'a pas de `CANCELLED`/`FAILED` ; après annulation ou échec il reste `STARTED`.
- **Journal par scan** : l'`AefiPointAcquired` du dernier point peut manquer, car l'export est déjà fermé quand il est publié.
- `AefiPoint` n'a pas encore d'index ni de baseline ; la baseline différentielle reste portée par `ScanPointAcquired`.
