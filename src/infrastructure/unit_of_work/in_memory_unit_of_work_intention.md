# in_memory_unit_of_work — Intention

## Rationale

Sans implémentation de `IUnitOfWork`, la règle « un agrégat par transaction » reste un texte : les services continuent de publier pendant la mutation, ce qui signifie des événements émis pour des changements éventuellement abandonnés, ce qui force chaque consommateur à se défendre contre des faits invalidés.

## Responsibility

- Implémenter `IUnitOfWork` en mémoire (Real et fake de test : mono-processus, sans DB).
- Au commit, publier sur `IDomainEventBus` les événements des agrégats enregistrés, topic = nom de classe en minuscules (comme `_publish_events`).
- Ne rien publier sur rollback (exception ou commit absent). Logs LDD : commit, rollback, rien à publier.

## Design

- Le bus est injecté par constructeur ; les repositories (`aefi_points`, `scans`) sont instanciés avec `self` pour enregistrer les agrégats vus.
- Les événements sont collectés au commit, l'état de transaction est remis à zéro, puis la publication a lieu : réentrance sûre, un handler peut ouvrir une seconde UoW.
- Pas de restauration d'état des agrégats au rollback (en mémoire) : seule la publication est annulée.
