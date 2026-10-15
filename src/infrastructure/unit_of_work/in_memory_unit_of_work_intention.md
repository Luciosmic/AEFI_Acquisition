# in_memory_unit_of_work — Intention

## Rationale

Sans implémentation de `IUnitOfWork`, la règle « un agrégat par transaction » reste un texte : les services continuent de publier pendant la mutation, ce qui signifie des événements émis pour des changements éventuellement abandonnés, ce qui force chaque consommateur à se défendre contre des faits invalidés.

## Responsibility

- Implémenter `IUnitOfWork` en mémoire (Real et fake de test : mono-processus, sans DB).
- Au commit, publier sur `IDomainEventBus` les événements des agrégats enregistrés, topic = nom de classe en minuscules (comme `_publish_events`).
- Ne rien publier sur rollback (exception ou commit absent). Logs LDD : commit, rollback, rien à publier.

## Design

- Le bus est injecté par constructeur ; les repositories (`aefi_points`, `aefi_lines`, `narda_points`, `scans`) sont instanciés avec `self` pour enregistrer les agrégats vus.
- Les événements sont collectés au commit, l'état de transaction est remis à zéro, puis la publication a lieu : réentrance sûre, un handler peut ouvrir une seconde UoW.
- Livraison en file (seconde moitié du pattern Unit of Work + message bus) : le commit le plus externe d'un thread possède une file FIFO et la vide, chaque événement étant livré à tous ses abonnés (`"*"` compris) avant le suivant. Un commit imbriqué, fait par un handler pendant la livraison, ajoute ses événements en fin de file et retourne. Sans cela, `ScanCompleted` (émis par le commit imbriqué du handler de clôture) serait observé, par un abonné `"*"` ou inscrit après le handler, avant la dernière `AefiLineAcquired` / `AefiPointAcquired` qui le cause — et le journal d'événements exporté, déjà fermé, la perdrait.
- La file est par thread (`threading.local`) et partagée entre instances du même thread ; elle vit dans l'UoW et non dans le bus, que les threads matériels appellent directement et dont la sémantique reste inchangée. Elle est remise à zéro même si une livraison lève une exception, pour ne pas bloquer les commits suivants.
- Pas de restauration d'état des agrégats au rollback (en mémoire) : seule la publication est annulée.
