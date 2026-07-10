# i_domain_event_bus — Intention

## Rationale

Découpler les producteurs d'événements (agrégats, services) des consommateurs (handlers, presenters) sans dépendance directe. L'interface domain garantit que ni le domain ni l'application ne connaissent `InMemoryEventBus` ou tout autre implémentation.

## Responsibility

- Déclarer `subscribe(event_type: str, handler: Callable)` : enregistrement d'un handler.
- Déclarer `publish(event_type: str, data: Any)` : diffusion à tous les abonnés.
- Déclarer `unsubscribe(event_type: str, handler: Callable)` : désabonnement.
- Déclarer `clear_subscribers(event_type: str = None)` : nettoyage pour les tests.

## Design

- **Placé dans `domain/events/`** : c'est une abstraction domain, pas applicative — le domain a le droit d'en dépendre.
- **`event_type` est une str (lowercase class name)** : convention `type(event).__name__.lower()` utilisée uniformément dans tous les publishers.
- Implémenté par `InMemoryEventBus` (infrastructure/events/).
