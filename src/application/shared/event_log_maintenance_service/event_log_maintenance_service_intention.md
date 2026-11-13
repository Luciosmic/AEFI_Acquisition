# event_log_maintenance_service — Intention

## Rationale

`EventAuditLog` écrit un fichier JSONL par run et n'en supprime jamais : les
échantillons étant des faits métier enregistrés un par un, un run de lecture
continue pèse ~150 Mo. Sans ce service, le dossier grossit sans que personne le
voie, jusqu'au jour où quelqu'un le découvre en explorant le disque et supprime
des fichiers à la main — sans savoir lequel est en cours d'écriture ni ce qui
a encore de la valeur. Avec un fort turnover au labo, un nettoyage automatique
serait tout aussi opaque : un fichier qui disparaît « tout seul » devient une
énigme pour la personne suivante. Le service rend donc l'état visible et laisse
la suppression à l'utilisateur.

## Responsibility

- `get_summary()` (query) : taille totale, nombre de sessions, date de la plus
  ancienne, dépassement du seuil d'alerte (20 Go), et l'aperçu de ce qu'une
  suppression enlèverait (sessions de plus de 90 jours : nombre, taille, période).
- `delete_expired_sessions()` (command) : supprime les sessions de plus de
  90 jours, jamais la session en cours ; une session non supprimable (fichier
  ouvert par une autre instance) est signalée, pas fatale.

## Design

- Rien d'automatique : appelé uniquement depuis le panneau Logs, sur action
  de l'utilisateur, après confirmation.
- Seuils en constantes (`RETENTION`, `SIZE_WARNING_BYTES`) : le journal est un
  filet de sécurité très prudent, pas une archive ; on passera en config le
  jour où un poste a besoin d'autres valeurs. 20 Go : PC dédié à la manip,
  la marge disque est large.
- Âge d'une session = horodatage de démarrage porté par son nom (fourni par
  le port), jamais la date de modification du fichier.
- Pas de domain event : effacer le filet de sécurité n'est pas un fait métier.
  La suppression est tracée par un log INFO (sessions, période, octets libérés),
  visible dans le panneau Logs.
- Horloge injectée (`now`) pour tester la frontière des 90 jours.
- Port outbound : `ports/i_event_log_storage_port.py`.
