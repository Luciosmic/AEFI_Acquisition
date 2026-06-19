# json_device_repository — Intention

## Rationale

Persistence JSON de la configuration du dispositif AEFI (géométrie, paramètres). JSON est choisi pour la lisibilité humaine et l'édition manuelle de la configuration matérielle, contrairement à HDF5 qui est opaque.

## Responsibility

- Charger et sauvegarder la configuration `AefiDevice` depuis/vers un fichier JSON dans `.aefi_acquisition/configs/`.
- Sérialiser/désérialiser les value objects domain (QuadSourceGeometry, etc.) en format JSON.

## Design

- Implémente un repository ou service de persistence de configuration côté infrastructure.
- La config device est rare à changer — JSON est adapté (pas de streaming, pas de performance critique).
