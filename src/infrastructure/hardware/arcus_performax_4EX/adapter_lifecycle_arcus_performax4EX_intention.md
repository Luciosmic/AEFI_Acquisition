# adapter_lifecycle_arcus_performax4EX — Intention

## Rationale

Adaptateur gérant le cycle de vie de la connexion au contrôleur Arcus (ouverture USB/DLL, vérification de connectivité, fermeture). Séparé de l'adaptateur motion pour respecter le Single Responsibility Principle.

## Responsibility

- Ouvrir et configurer la connexion au contrôleur Arcus via la DLL.
- Vérifier la connectivité (ping ou status register).
- Fermer proprement la connexion lors du shutdown.
- Contribuer à `IHardwareInitializationPort` (via `CompositeHardwareInitializationPort`).

## Design

- **Séparation lifecycle / motion** : l'adaptateur lifecycle est utilisé au démarrage/arrêt, l'adaptateur motion l'est en permanence pendant les scans.
