# electric_field_probe_service — Intention

## Rationale

Piloter une sonde de champ électrique générique (`electric_field_probe`,
aujourd'hui Narda EP-601) indépendamment du contexte `aefi_device`
(démodulation synchrone). Contrairement à Arcus/MCU, cette sonde ne fait pas
partie du démarrage matériel bloquant de l'application — elle est auto-off et
time-out fréquemment, donc la connexion est une commande explicite déclenchée
depuis l'UI, pas une étape du cycle de vie système.

## Responsibility

- Démarrer/arrêter/mettre à jour une acquisition continue en déléguant à
  `IElectricFieldProbeAcquisitionExecutor` (même pattern que
  `AefiAcquisitionService`).
- Piloter la connexion/déconnexion de la sonde via `IElectricFieldProbePort`,
  en absorbant toute exception matérielle (time-out, port série absent) :
  `connect_probe()` ne lève jamais, elle publie
  `ElectricFieldProbeConnectionChanged` avec le résultat.

## Design

- **Service intentionnellement minimal** : délègue à l'executor pour
  l'acquisition, au port pour la connexion — pas d'état propre autre que ces
  deux références et l'event bus.
- **Jamais de propagation d'exception hardware vers l'appelant** : la sonde
  étant peu fiable par nature (auto-off), chaque tentative de connexion se
  traduit par un événement, jamais par une exception à intercepter côté UI.
