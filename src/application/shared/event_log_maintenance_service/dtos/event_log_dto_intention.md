# event_log_dto — Intention

## Rationale

Sans DTO, le panneau Logs recevrait les `StoredEventLogSession` du port et
referait lui-même le calcul « quelles sessions ont plus de 90 jours » pour sa
confirmation — la règle de rétention vivrait alors à deux endroits.

## Responsibility

- `EventLogSummaryDTO` : l'état affiché (taille, sessions, plus ancienne,
  alerte) + l'aperçu exact de ce que la suppression enlèverait, pour la
  boîte de confirmation.
- `EventLogPurgeResultDTO` : ce qui a été supprimé, et ce qui ne l'a pas été.

## Design

- `@dataclass(frozen=True)`, tailles en octets et dates UTC : le formatage
  (Mo/Go, date locale) reste dans la vue.
