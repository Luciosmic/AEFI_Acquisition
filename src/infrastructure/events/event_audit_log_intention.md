# event_audit_log — Intention

## Rationale

Capteur d'audit : persiste chaque événement domain publié sur `IDomainEventBus` en JSONL append-only, pour qu'un LLM (ou un humain) puisse relire, plus tard, ce que le logiciel a réellement fait — et le comparer à ce qu'un `intention.md`/test dit qu'il devrait faire. Ce n'est pas de l'event sourcing : l'état n'est jamais reconstruit depuis ce fichier, `InMemoryEventBus` reste la seule source de vérité à l'exécution. Voir `_system/self/event_store.md` pour le schéma et le mode d'emploi côté lecture.

## Responsibility

- S'abonner au wildcard `"*"` du bus pour voir tous les événements sans être modifié à chaque nouveau type ajouté.
- Sérialiser chaque événement (type + tous ses champs) en une ligne JSON, avec `event_id`/`occurred_on` toujours présents via `DomainEvent`.
- Ne jamais faire échouer la publication d'un événement : une erreur de sérialisation est loggée et avalée, pas propagée.

## Design

- **Un fichier JSONL par run applicatif**, nommé avec l'horodatage UTC de démarrage — couvre tout le run (tous les scans, tous les événements système) dans un seul fichier ordonné.
- **`dataclasses.asdict()`** aplatit récursivement les value objects imbriqués (`FieldMeasurement`, `Position2D`, etc.) ; `default=` sur `json.dumps` convertit `UUID`/`datetime` en `str`, avec repli `str(x)` générique pour tout type non prévu.
- **Ouverture/fermeture du fichier à chaque écriture** : légèrement plus coûteux qu'un flux tenu ouvert, mais garantit qu'un crash pendant un scan ne perd pas les événements déjà écrits — pertinent pour du logiciel de pilotage matériel.
- **Pas de correlation_id propre** : la corrélation se fait via les champs `scan_id`/`acquisition_id` déjà portés par les événements concernés.
