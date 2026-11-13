# in_memory_event_bus — Intention

## Rationale

Implémentation in-memory de `IDomainEventBus` — le seul bus d'événements utilisé dans le système (tests comme production). La simplicité in-memory suffit pour un processus mono-JVM synchrone ; si le système devient distribué, seule cette classe change.

## Responsibility

- Maintenir un dictionnaire `event_type → List[handler]`.
- Dispatcher synchronement les événements à tous les handlers abonnés au type publié, ainsi qu'aux handlers abonnés au type spécial `"*"`.
- Logger les événements sans subscribers (warning) et les erreurs de handlers (error, sans propagation).

## Design

- **`defaultdict(list)`** : abonnement à un type inexistant est safe sans vérification.
- **Isolation des erreurs de handlers** : un handler défaillant ne bloque pas les autres — try/except par handler, factorisé dans `_dispatch()` et réutilisé pour le dispatch normal et le dispatch wildcard.
- **`clear_subscribers()`** essentielle pour les tests : permet de réinitialiser le bus entre tests sans recréer d'instance.
- **Wildcard `"*"`** : convention (pas un vrai type d'événement) pour un subscriber catch-all — voir `event_audit_log.py`, qui s'abonne à `"*"` pour persister tous les événements sans avoir à être modifié à chaque nouveau type d'événement.
