---
type: atome::solidai-atome
tldr: "Module `event_audit_log` : S'abonner au wildcard `\"*\"` du bus pour voir tous les événements sans être modifié à chaque nouveau type ajouté."
code: ["[[src/infrastructure/events/event_audit_log.py]]"]
cause_de_changement: outil
---
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
- **Une ligne = un événement complet, même en écriture concurrente** : le bus publie depuis plusieurs threads (boucle de scan, threads matériels ADC/moteur). La sérialisation JSON se fait hors verrou ; l'ouverture, l'écriture de la ligne entière et la fermeture se font sous un `threading.Lock` d'instance. Sans lui, le mode append sous Windows (aller en fin de fichier puis écrire, non atomique entre deux handles) fait écrire deux lignes au même offset : l'une écrase l'autre (constaté au banc le 2026-10-30 pendant un fly-scan). Limite : tous les publieurs attendent une ouverture de fichier par événement — piste si le débit en souffre : fichier tenu ouvert ou thread écrivain alimenté par une file.
- **Ne supprime jamais rien** : la taille du dossier et la suppression des vieilles sessions, sur action de l'utilisateur, relèvent de `event_log_maintenance_service` (via `file_event_log_storage`, qui lit le même format de nom — `SESSION_TIMESTAMP_FORMAT`). `path` expose le fichier de la session en cours pour qu'il ne soit jamais supprimé.
- **Pas de correlation_id propre** : la corrélation se fait via les champs `scan_id`/`acquisition_id` déjà portés par les événements concernés.
