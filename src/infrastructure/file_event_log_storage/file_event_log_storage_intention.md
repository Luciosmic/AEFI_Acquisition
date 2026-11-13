# file_event_log_storage — Intention

## Rationale

Le service de maintenance a besoin de connaître les sessions du journal
d'événements et d'en supprimer. Sans cet adaptateur, il devrait connaître le
dossier `logs/events/` et le format de nom des fichiers d'`EventAuditLog` ;
un fichier étranger déposé dans ce dossier, ou la session en cours, pourrait
alors être supprimé par erreur.

## Responsibility

- Lister les fichiers `events_<horodatage UTC>_<hex>.jsonl` du dossier : nom,
  date de démarrage (lue dans le nom), taille, et s'il s'agit de la session
  en cours (`live_session`, le fichier d'`EventAuditLog.path`).
- Supprimer une session sur demande. Refuser (en `OperationResult.fail`) :
  la session en cours, un nom qui n'est pas une session, un fichier absent ou
  verrouillé (Windows refuse de supprimer un fichier ouvert par une autre
  instance de l'application).

## Design

- Date tirée du nom (`SESSION_TIMESTAMP_FORMAT` partagé avec
  `event_audit_log.py`), jamais du `mtime`.
- Les fichiers qui ne suivent pas le format sont ignorés au listage et
  refusés à la suppression.
- Chaque suppression ou refus est loggé avec le nom de la session.
