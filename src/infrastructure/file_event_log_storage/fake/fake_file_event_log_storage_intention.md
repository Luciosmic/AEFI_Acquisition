# fake_event_log_storage — Intention

## Rationale

Sans Fake, tester la règle des 90 jours du service de maintenance exigerait
de créer de vrais fichiers datés sur disque, et le cas « fichier ouvert par
une autre instance » (échec de suppression sous Windows) serait impossible à
reproduire de façon portable.

## Responsibility

- Implémenter `IEventLogStoragePort` en mémoire.
- Reproduire les modes d'échec du Real : session en cours, session absente,
  session verrouillée (`locked=`), tous renvoyés en `OperationResult.fail`.

## Design

- Sessions passées au constructeur sous forme de `StoredEventLogSession`.
- Pas de latence simulée : la suppression d'un fichier local est quasi
  instantanée sur le Real aussi, et rien ne régule sur sa durée.
