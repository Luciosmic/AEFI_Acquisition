# Bus d'Événements In-Memory

## Rationale
Ce module fournit l'implémentation concrète du bus d'événements domaine utilisé en production et dans les tests. Il est la colonne vertébrale de communication découplée entre les couches domaine, application et interface.

## Responsibility
- Implémenter `IDomainEventBus` avec un dictionnaire d'abonnés en mémoire (`defaultdict(list)`).
- Permettre l'abonnement (`subscribe`), la désabonnement (`unsubscribe`) et la publication (`publish`) d'événements identifiés par un topic string (nom de classe en minuscules).
- Isoler les erreurs de handlers : une exception dans un handler est loggée mais ne bloque pas la livraison aux autres subscribers.
- Permettre la réinitialisation complète ou partielle des abonnés (`clear_subscribers`) pour les besoins de test.

## Design
- Implémentation synchrone : `publish` appelle les handlers dans le thread de l'émetteur, sans queue ni thread dédié.
- Les handlers sont stockés dans une liste par topic, ce qui autorise plusieurs subscribers sur le même événement.
- Un warning est émis si un événement est publié sans subscriber (aide au diagnostic pendant le développement).
