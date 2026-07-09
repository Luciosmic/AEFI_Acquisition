# Mocks Infrastructure — Adaptateurs de Test

## Rationale
Ce dossier contient les adaptateurs mock (implémentations in-memory) de tous les ports applicatifs. Ils permettent de tester les services applicatifs et les presenters sans connecter le hardware réel, en mode synchrone ou asynchrone simulé.

## Responsibility
- `MockMotionPort` (`adapter_mock_i_motion_port.py`) : implémenter `IMotionPort` en mémoire. Enregistre l'historique des déplacements, simule la latence dans un thread daemon, et publie les événements `MotionStarted/Completed/Failed/PositionUpdated` sur le bus domaine si disponible.
- `MockAcquisitionPort` / `RandomNoiseAcquisitionPort` (`adapter_mock_i_acquisition_port.py`) : implémenter `IAcquisitionPort`. `MockAcquisitionPort` retourne des valeurs synthétiques déterministes (compteur × 0.1). `RandomNoiseAcquisitionPort` génère un bruit gaussien configurable pour simuler un signal réel.
- Les autres mocks du dossier couvrent les ports excitation, export, configuration hardware, initialisation hardware et exécuteur de scan.

## Design
- Tous les mocks suivent la convention de nommage `adapter_mock_<i_port_name>.py` pour une identification immédiate.
- Les mocks publient sur le bus domaine lorsqu'un `event_bus` est injecté, ce qui permet de tester les flux événementiels end-to-end sans hardware.
- `RandomNoiseAcquisitionPort` accepte un `seed` pour garantir la reproductibilité des tests.
