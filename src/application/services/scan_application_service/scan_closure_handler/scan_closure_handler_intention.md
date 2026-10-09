# scan_closure_handler — Intention

## Rationale

Sans handler, l'acquisition d'un point et la complétion du scan devraient partager une transaction, ce qui signifie deux agrégats modifiés ensemble, ce qui force un verrou large et casse la règle « un agrégat par transaction ». Sans gestion d'échec explicite, le bus avale l'exception du handler et le scan reste STARTED sans trace.

## Responsibility

- S'abonner (dans `__init__`) aux topics d'acquisition qu'on lui donne et, par événement `ProbeAcquisitionEvent`, ouvrir une UoW sur le `Scan`, appeler `mark_acquired(event.source, event.acquisition_id)`, `commit()`. Il est générique : ajouter un capteur = son agrégat + son topic ici (wiring dans `main.py`) + sa déclaration de source dans le `Scan`.
- Id déjà reçu : log « rien à faire », pas de commit.
- Scan introuvable ou toute exception : log d'erreur (`scan_id`, `source`, `acquisition_id`) + publication de `ScanClosureFailed`. Pas de retry automatique.
- La publication de `ScanClosureFailed` ne relance jamais d'exception.

## Design

- Le bus, l'UoW et la liste des topics sont injectés par constructeur (pas de registre dynamique). L'UoW (instance unique) est réentrante : celle de l'acquisition est fermée avant la publication, le handler peut donc ré-ouvrir `with uow:`.
- Capture ses propres erreurs car `InMemoryEventBus` avale les exceptions des handlers.
- Coexiste avec le service applicatif existant, qui n'est pas modifié ni câblé à ce handler.
