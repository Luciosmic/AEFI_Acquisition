# Scan Application Service

## Rationale
Ce service orchestre le cas d'utilisation central du système : l'exécution d'un scan 2D pas-à-pas. Il coordonne le mouvement, l'acquisition et l'export tout en restant découplé des détails hardware grâce aux ports injectés.

## Responsibility
- Convertir le DTO de configuration en valeur objet domaine `StepScanConfig`.
- Créer et piloter l'agrégat `StepScan` (start, pause, resume, cancel, fail).
- Déléguer l'exécution pas-à-pas à `IScanExecutor` (infrastructure).
- S'abonner au bus d'événements pour transférer les événements domaine vers le port de sortie `IScanOutputPort` (presenter).
- Publier les événements domaine (`ScanStarted`, `ScanPointAcquired`, `ScanCompleted`, etc.).

## Design
- Ports injectés au constructeur : `IMotionPort`, `IAcquisitionPort`, `IDomainEventBus`, `IScanExecutor`, `IScanOutputPort` (optionnel).
- La logique de trajectoire est déléguée au service domaine `ScanTrajectoryFactory` (pur, sans effet de bord).
- L'exécution réelle point-par-point est déléguée à `IScanExecutor` pour permettre l'asynchronisme sans que ce service ne porte de thread.
- Les événements sont reroutés vers `IScanOutputPort` dans `_on_domain_event` via l'abonnement au bus.
