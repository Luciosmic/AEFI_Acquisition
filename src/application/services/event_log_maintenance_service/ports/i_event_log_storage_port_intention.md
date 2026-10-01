# i_event_log_storage_port — Intention

## Rationale

Sans ce port, le service de maintenance lirait le dossier `logs/events/`
lui-même : la règle des 90 jours deviendrait intestable sans fichiers réels
et datés, et le format de nommage des sessions (propriété d'`EventAuditLog`)
fuirait dans la couche application.

## Responsibility

- `list_sessions()` : chaque session du journal, avec sa date de démarrage,
  sa taille, et si c'est la session en cours d'écriture.
- `delete_session(name)` : supprime une session ; échec attendu (fichier
  ouvert ailleurs, déjà absent, session en cours) renvoyé en
  `OperationResult`, jamais levé.

## Design

- Port outbound, consommé par `EventLogMaintenanceService`.
- Real : `infrastructure/events/file_event_log_storage.py` ; Fake :
  `infrastructure/events/fake/fake_event_log_storage.py`.
- `started_at` vient du nom de fichier (UTC), pas du `mtime`.
