# in_memory_event_bus — Intention

## Rationale

Implémentation in-memory de `IDomainEventBus` — le seul bus d'événements utilisé dans le système (tests comme production). La simplicité in-memory suffit pour un processus mono-JVM synchrone ; si le système devient distribué, seule cette classe change.

## Responsibility

- Maintenir un dictionnaire `event_type → List[handler]`.
- Dispatcher synchronement les événements à tous les handlers abonnés.
- Logger les événements sans subscribers (warning) et les erreurs de handlers (error, sans propagation).

## Design

- **`defaultdict(list)`** : abonnement à un type inexistant est safe sans vérification.
- **Isolation des erreurs de handlers** : un handler défaillant ne bloque pas les autres — try/except par handler dans `publish()`.
- **`clear_subscribers()`** essentielle pour les tests : permet de réinitialiser le bus entre tests sans recréer d'instance.
