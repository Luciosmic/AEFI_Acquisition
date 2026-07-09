# acquisition_data_handler — Intention

## Rationale

Persister les données d'acquisition au fil des événements domain sans polluer `ScanApplicationService` avec la logique de persistence. Ce handler est un abonné de bus dédié à une seule responsabilité : écouter `ScanPointAcquired` et appeler le repository.

## Responsibility

- S'abonner (via injection dans le composition root) aux événements `ScanPointAcquired`.
- Extraire le `scan_id` et le `measurement` de l'événement.
- Déléguer la persistence à `IAcquisitionDataRepository`.

## Design

- **Handler applicatif** (pas un service) : reçoit un `DomainEvent` via `handle()`, filtre par type, délègue.
- **Dépendance unique** : `IAcquisitionDataRepository` — aucune dépendance sur le bus lui-même (l'abonnement est fait dans le composition root).
- **Resilience** : les exceptions sont catchées et loggées pour ne pas interrompre les autres abonnés du bus.
