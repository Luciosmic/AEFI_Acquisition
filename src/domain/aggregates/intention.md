# Aggregats Domaine

## Rationale
Ce dossier contient les racines d'agrégat du modèle domaine AEFI. Chaque agrégat représente un concept métier cohérent portant ses propres invariants et émettant des événements domaine lors de ses mutations.

## Responsibility
- `StepScan` : racine d'agrégat pour un scan pas-à-pas. Gère la collection de `ScanPointResult`, le cycle de vie (start/pause/resume/complete/fail/cancel) et émet les événements de cycle (`ScanStarted`, `ScanPointAcquired`, `ScanCompleted`, etc.).
- `AefiDevice` : racine d'agrégat représentant l'instrument AEFI physique. Encapsule la géométrie quadri-source (`QuadSourceGeometry`) et calcule les paires d'interaction source–capteur.
- `TestBench` : racine d'agrégat représentant le banc d'essai expérimental. Gère l'arrangement colonnes/sources/capteur et recalcule les paires d'interaction à la demande.

## Design
- `StepScan` hérite de `SpatialScan` (entité) et accumule les événements dans `_domain_events` ; les événements sont extraits et effacés à chaque accès pour garantir un flux unidirectionnel.
- `AefiDevice` est un dataclass `frozen=True` (immuable) car sa géométrie ne change pas en cours d'exécution.
- `TestBench` est mutable et expose `configure_geometry()` pour initialiser l'état depuis un service applicatif ou un test.
