# scan — Intention

## Rationale

Aujourd'hui `StepScan` contient ses points et se complète lui-même : il confond le processus physique avec son artefact de traçage, ce qui signifie qu'un agrégat gros et chargé de mesures porte la transaction de chaque point, ce qui force à tout verrouiller pour un seul point acquis. Le `Scan` est l'artefact qui dénote le processus : il référence par identité les acquisitions des agrégats forts et ne se complète que lorsque toutes les sources requises sont présentes. Il est agnostique de la sonde : sans cela, chaque capteur ajouté (AEFI point, AEFI ligne, Narda) modifierait l'agrégat.

## Responsibility

- Aggregate root fin : identité `ScanId`, sources attendues (mapping nom de source → `ExpectedSource(count, required)`), `total_points` (points de grille, pour le reporting de `ScanCompleted`), ensembles d'identifiants reçus par source.
- États PENDING (créé, observable) → STARTED (`start()`) → COMPLETED.
- `mark_acquired(source, acquisition_id)` : idempotent par (source, id) (retourne False si déjà reçu) ; refusé avant start (`ScanNotStartedError`), après complétion pour un id inconnu (`ScanAlreadyCompletedError`), et pour une source non déclarée (`ScanSourceNotDeclaredError`).
- COMPLETED seulement quand toutes les sources `required` ont reçu leur `count` (les sources facultatives sont enregistrées, sans conditionner la complétion) ; empile alors `ScanCompleted(total_points)`.
- Au moins une source requise, `total_points >= 1` (`ValueError`).
- Expose `domain_events` (retourne puis vide, requis par `IUnitOfWork.register`).

## Design

- Les noms de source sont des constantes des agrégats émetteurs (le `Scan` n'en connaît aucune) ; l'événement d'acquisition respecte `ProbeAcquisitionEvent`.
- Coexiste avec `StepScan` (non modifié ; pause/cancel/failed non migrés).
- Réutilise `ScanCompleted` existant (forme `scan_id`, `total_points` adaptée). `ScanStarted` existant exige une config de scan : non réutilisé ni recréé (même nom de topic, forme différente) ; PENDING→STARTED reste observable par `state`.
- Domaine pur : aucun import application/infrastructure, aucun logger.
