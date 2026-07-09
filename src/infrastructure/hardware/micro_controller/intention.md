# Micro-Contrôleur (MCU) — Communication Série

## Rationale
Ce module gère la communication série avec le micro-contrôleur embarqué qui pilote l'ADC ADS131A04 et le DDS AD9106. Un singleton partagé garantit qu'un seul port série est ouvert simultanément, évitant les conflits d'accès entre les sous-systèmes ADC et DDS.

## Responsibility
- `MCU_SerialCommunicator` : singleton thread-safe gérant la connexion série (pyserial) vers le MCU. Expose `connect`, `disconnect` et `send_command` (format `a<addr>*` puis `d<value>*`).
- `MCULifecycleAdapter` : implémenter `IHardwareInitializationPort`. Orchestre l'initialisation du MCU : connexion série, puis configuration des registres ADC et DDS depuis un dictionnaire JSON (ou configuration par défaut si aucun JSON n'est fourni).

## Design
- Le singleton `MCU_SerialCommunicator` utilise un `threading.Lock` pour sérialiser les accès au port série entre les threads ADC et DDS.
- La configuration depuis JSON est structurée en deux sections `"adc"` et `"dds"` ; chaque section mappe directement sur les adresses de registres hardware.
- La configuration par défaut (`_init_default_hardware_config`) reproduit le comportement legacy pour la rétrocompatibilité.
