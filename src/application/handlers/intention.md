# Application Handlers

## Rationale
Les handlers applicatifs sont des abonnés aux événements domaine. Ils reçoivent des `DomainEvent` via le bus et déclenchent des effets de bord applicatifs (persistance, notification, audit) sans appartenir à un service métier.

## Responsibility
- `AcquisitionDataHandler` : écoute `ScanPointAcquired` et persiste le sample dans `IAcquisitionDataRepository`.

## Design
- Chaque handler reçoit ses dépendances par injection au constructeur.
- La méthode `handle(event: DomainEvent)` est l'unique point d'entrée ; le dispatch interne est fait par `isinstance`.
- Les handlers ne publient pas d'événements et n'appellent pas d'autres services.
