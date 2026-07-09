# i_hardware_initialization_port — Intention

## Rationale

Abstraire la séquence d'initialisation et de fermeture de tous les périphériques hardware (MCU, Arcus, AD9106, ADS131A04) derrière un port unique. Permet à `SystemStartupApplicationService` d'orchestrer le démarrage sans connaître les drivers concrets.

## Responsibility

- Déclarer `initialize_all() → Dict[str, Any]` : initialise tous les périphériques, retourne les ressources créées.
- Déclarer `verify_all() → bool` : vérifie optionnellement la connectivité de tous les périphériques.
- Déclarer `close_all()` : ferme toutes les connexions de façon gracieuse.

## Design

- **Port outbound** dans `system_lifecycle_service/`.
- Implémenté typiquement par un `CompositeHardwareInitializationPort` qui agrège les initialiseurs individuels (MCU, Arcus).
