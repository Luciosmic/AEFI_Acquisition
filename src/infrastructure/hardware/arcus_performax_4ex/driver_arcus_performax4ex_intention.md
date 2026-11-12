---
type: atome::solidai-atome
tldr: "Wrapper bas-niveau autour de la DLL Arcus Performax 4EX."
code: ["[[src/infrastructure/hardware/arcus_performax_4ex/adapter_arcus_speed_config.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_lifecycle_arcus_performax4ex.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_motion_port_arcus_performax4ex.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/arcus_advanced_configuration.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/composition_root_arcus.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/driver_arcus_performax4ex.py]]"]
cause_de_changement: outil
---
# driver_arcus_performax4ex — Intention

## Rationale

Wrapper bas-niveau autour de la DLL Arcus Performax 4EX. Isole les appels ctypes/DLL dans une seule classe pour que les adaptateurs au-dessus puissent utiliser une API Python propre sans manipuler directement les types C.

## Responsibility

- Charger la DLL depuis `DLL64/`.
- Exposer les commandes Arcus (move, stop, home, get_position, set_reference) comme méthodes Python.
- Gérer les codes retour de la DLL et lever des exceptions Python claires.

## Design

- **Couche driver pure** : pas de logique domain, pas de publication d'événements.
- Utilisé exclusivement par les adaptateurs motion et lifecycle Arcus.
