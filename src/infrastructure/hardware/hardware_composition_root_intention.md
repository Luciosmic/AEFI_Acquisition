# hardware_composition_root — Intention

## Rationale

Point de composition des trois sous-systèmes hardware (motion, MCU, sonde de champ électrique) à partir du dict `hardware_config` (mock/real par sous-système). Sans ce module, cette sélection réel/mock — et le wrapping `ExcitationAwareAcquisitionPort` qui en dépend — vivait directement dans `main.py`, mélangée avec l'assemblage des services applicatifs et le wiring UI.

## Responsibility

- Choisir, par sous-système, entre l'adaptateur réel et son équivalent simulé (`ArcusCompositionRoot`/`MCUCompositionRoot` avec transport faké, `NardaEP601ProbeAdapter`/`FakeElectricFieldProbeAdapter`).
- Envelopper le port d'acquisition avec `ExcitationAwareAcquisitionPort` quand le MCU tourne en mode mock (simulation du couplage excitation/acquisition).
- Exposer les ports prêts à l'injection (`motion_port`, `acquisition_port`, `excitation_port`, `continuous_executor`, `probe_port`), la liste `lifecycle_adapters`, et les sous-composition-roots (`arcus_root`, `mcu_root`) pour l'accès à `.config`/`.configurators`/`.ad9106_*` en aval.

## Design

- **Composition root de second niveau** : compose `ArcusCompositionRoot` + `MCUCompositionRoot` + l'adaptateur Narda, symétrique à ces deux-là mais un niveau au-dessus.
- Utilisé depuis le composition root global de l'application (`main.py`).
- La sonde Narda n'est délibérément pas ajoutée à `lifecycle_adapters` : auto-off et sujette à des timeouts fréquents, sa connexion reste une action manuelle depuis le panneau, jamais une étape de démarrage bloquante.
