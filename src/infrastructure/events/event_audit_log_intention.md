---
type: atome::solidai-atome
tldr: "Module `event_audit_log` : S'abonner au wildcard `\"*\"` du bus pour voir tous les événements sans être modifié à chaque nouveau type ajouté."
code: ["[[src/infrastructure/events/event_audit_log.py]]"]
cause_de_changement: outil
---
# event_audit_log — Intention

## Rationale

Capteur d'audit : persiste chaque événement domain publié sur `IDomainEventBus` en JSONL append-only, pour qu'un LLM (ou un humain) puisse relire, plus tard, ce que le logiciel a réellement fait — et le comparer à ce qu'un `intention.md`/test dit qu'il devrait faire. Ce n'est pas de l'event sourcing : l'état n'est jamais reconstruit depuis ce fichier, `InMemoryEventBus` reste la seule source de vérité à l'exécution. Voir `_system/self/event_store.md` pour le schéma et le mode d'emploi côté lecture.

Le bus publie depuis le fil d'acquisition : tout ce que l'audit coûte à la publication ralentit chaque point de mesure. Le 2026-11-27, une ouverture de fichier par événement coûtait 0,55 ms, et un point publie trois événements : 1,7 ms par point, soit près de la moitié de l'écart de débit mesuré entre l'application et un script nu.

## Responsibility

- S'abonner au wildcard `"*"` du bus pour voir tous les événements sans être modifié à chaque nouveau type ajouté.
- Sérialiser chaque événement (type + tous ses champs) en une ligne JSON, avec `event_id`/`occurred_on` toujours présents via `DomainEvent`.
- Ne jamais faire attendre le disque au publieur : `record()` ne fait que mettre l'événement en file.
- Ne jamais faire échouer la publication d'un événement : une erreur de sérialisation ou d'écriture est loggée et avalée, pas propagée.

## Design

- **Un fichier JSONL par run applicatif**, nommé avec l'horodatage UTC de démarrage — couvre tout le run (tous les scans, tous les événements système) dans un seul fichier ordonné.
- **Un fil écrivain unique, fichier tenu ouvert** : `record()` dépose l'événement dans une `queue.Queue` (quelques µs). Le fil écrivain vide la file par lots, sérialise, écrit les lignes et fait un `flush()` par lot. Un seul écrivain : une ligne = un événement complet, même quand plusieurs fils publient (sans cela, le mode append sous Windows faisait écrire deux lignes au même offset, constaté au banc le 2026-10-30 pendant un fly-scan).
- **Ce qu'un arrêt brutal peut perdre** : les événements encore dans la file, au plus un lot (le `flush()` par lot les remet au système). L'ancienne conception, ouverture et fermeture à chaque écriture, ne perdait rien mais bloquait chaque publieur sur le disque.
- **`flush()`** attend que tout ce qui a été enregistré soit écrit (tests, lecture du fichier en cours). **`close()`** écrit la file puis arrête le fil ; il est enregistré par `atexit`, et `record()` ignore ce qui arrive après.
- **`dataclasses.asdict()`** aplatit récursivement les value objects imbriqués (`FieldMeasurement`, `Position2D`, etc.) ; `default=` sur `json.dumps` convertit `UUID`/`datetime` en `str`, avec repli `str(x)` générique pour tout type non prévu. Les événements sont gelés : les sérialiser plus tard, dans le fil écrivain, donne la même ligne.
- **Ne supprime jamais rien** : la taille du dossier et la suppression des vieilles sessions, sur action de l'utilisateur, relèvent de `event_log_maintenance_service` (via `file_event_log_storage`, qui lit le même format de nom — `SESSION_TIMESTAMP_FORMAT`). `path` expose le fichier de la session en cours pour qu'il ne soit jamais supprimé.
- **Pas de correlation_id propre** : la corrélation se fait via les champs `scan_id`/`acquisition_id` déjà portés par les événements concernés.
