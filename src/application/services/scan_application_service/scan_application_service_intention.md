# scan_application_service — Intention

## Rationale

Orchestrer le cycle de vie d'un scan 2D step-by-step. Ce service est le point central qui coordonne la motion, l'acquisition et l'export tout en restant indépendant des implémentations hardware. Sans ce service, la logique d'orchestration serait soit dans la UI (violation de séparation des responsabilités) soit dans le domain (pollution par l'I/O).

## Responsibility

- Accepter un `Scan2DConfigDTO` (`execute_scan`, grille) ou un `LineScanConfigDTO` (`execute_line_scan`, ligne theta) et déclencher la séquence complète : validation → création de l'agrégat `StepScan` → génération de trajectoire (factory propre à chaque forme) → boucle de scan commune (`_start_scan`).
- Gérer le cycle de vie du scan : pause, resume, cancel via l'exécuteur.
- S'abonner aux événements domain publiés sur `IDomainEventBus` et les forwarder vers `IScanOutputPort` (Presenter).
- Exposer une query `get_status() → ScanStatusDTO` sans dépendance infrastructure.

## Design

- **Injection de dépendances** : `IMotionPort`, `IAcquisitionPort`, `IDomainEventBus`, `IScanExecutor`, `IScanOutputPort` sont tous injectés au constructeur.
- **Séparation Commands/Queries** : méthodes `execute_scan`, `pause_scan`, `resume_scan`, `cancel_scan` (commands) vs `get_status` (query).
- **Event forwarding** : s'abonne lui-même au bus dans `__init__` pour transposer les événements domain vers le port de sortie UI — évite le couplage direct Executor→Presenter.
- **Traduction DTO→Domain** : `_to_domain_config()` isole la conversion afin que le domain ne voie jamais les DTOs applicatifs.
