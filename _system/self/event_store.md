# Event audit log — capteur pour audit réel vs attendu

Journal append-only de tous les événements domain réellement publiés à l'exécution. Sert de "boîte noire" : un LLM (ou un humain) qui veut vérifier si le logiciel a fait ce qu'un `intention.md`/test dit qu'il devrait faire lit ce fichier plutôt que de faire confiance au code seul.

Ce n'est **pas** de l'event sourcing : l'état de l'application n'est jamais reconstruit depuis ce fichier. C'est un enregistrement passif, en plus du fonctionnement normal du bus (`InMemoryEventBus`, toujours fire-and-forget en mémoire).

## Où

`.aefi_acquisition/logs/events/events_<horodatage UTC de démarrage>_<suffixe>.jsonl` — un fichier par run applicatif (du démarrage à l'arrêt), tous scans et événements système confondus, dans l'ordre où ils ont été publiés. Gitignored (comme le reste de `.aefi_acquisition/`).

## Schéma

Une ligne JSON par événement :

```json
{"event_type": "ScanPointAcquired", "event_id": "...", "occurred_on": "2026-07-31T14:22:03.512+00:00", "scan_id": "...", "point_index": 12, "...": "..."}
```

- `event_type` : nom de la classe Python de l'événement (`domain/**/events/`).
- `event_id`, `occurred_on` (UTC ISO8601) : toujours présents, hérités de `DomainEvent`.
- Le reste des champs = le payload propre à l'événement (value objects imbriqués aplatis par `dataclasses.asdict`).

## Comment auditer une session avec ce fichier

1. Identifier le `scan_id`/`acquisition_id` concerné (ou le fichier du bon run, par horodatage).
2. `grep` ce fichier pour cet ID → reconstitue la séquence complète d'un scan (`ScanStarted` → N × `ScanPointAcquired`/`ElectricFieldScanPointAcquired` → `ScanCompleted`/`ScanFailed`/`ScanCancelled`).
3. Comparer aux invariants attendus décrits dans le `intention.md` du service concerné (ex. `scan_application_service_intention.md`) : nombre de points, ordre des états, valeurs plausibles des mesures, cohérence config demandée (`ScanStarted`) vs mesures obtenues.
4. Pour les événements système/moteur/excitation (pas de `scan_id`), la corrélation se fait par proximité temporelle (`occurred_on`) et position dans le fichier.

## Limites connues (scope volontairement réduit)

- Capture les événements **domain** uniquement — pas les commandes/actions utilisateur qui les ont déclenchés. Un écart entre "ce que l'utilisateur a demandé dans l'UI" et "ce que le domain a fait" n'est donc visible qu'indirectement, via le contenu des événements (ex. `ScanStarted` porte la config demandée).
- Pas de `correlation_id` séparé : on s'appuie sur les `scan_id`/`acquisition_id` déjà portés par les événements. Insuffisant si plusieurs scans tournent un jour en parallèle.
- Pas d'outil de requête : fichier JSONL brut, à lire avec `grep`/lecture directe. Si le besoin de requêtes croisées entre fichiers/sessions apparaît, envisager de charger les JSONL dans sqlite/duckdb à la demande.

## Implémentation

- `src/domain/shared_kernel/events/domain_event.py` — base `event_id` (UUID4) + `occurred_on` (UTC).
- `src/infrastructure/events/in_memory_event_bus.py` — fan-out vers les subscribers `"*"` en plus du type publié.
- `src/infrastructure/events/event_audit_log.py` — le subscriber `"*"` qui écrit le JSONL (`EventAuditLog.record`).
- `src/main.py` — instancié et abonné juste après la création de `InMemoryEventBus`.
