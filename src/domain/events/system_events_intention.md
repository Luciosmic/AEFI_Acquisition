# system_events — Intention

## Rationale

Modéliser le cycle de vie global du système (démarrage, arrêt) comme des événements domain. Permettent à la UI et aux services de réagir aux transitions système sans couplage direct avec le service lifecycle.

## Responsibility

- `SystemReadyEvent` : le système est initialisé et prêt pour les opérations.
- `SystemStartupFailedEvent` : reason string — l'initialisation a échoué.
- `SystemShuttingDownEvent` : arrêt en cours — signal pour que les services actifs s'arrêtent proprement.
- `SystemShutdownCompleteEvent` : success + details — arrêt terminé.

## Design

- **`@dataclass`** héritant de `DomainEvent`.
- `SystemShuttingDownEvent` est publié AVANT les opérations d'arrêt : donne aux services l'opportunité de se nettoyer en réaction à l'événement.
