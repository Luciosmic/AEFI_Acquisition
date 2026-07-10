# fake_electric_field_probe_adapter — Intention

## Rationale

Permettre de tester `ElectricFieldProbeService` et le mode
`HARDWARE_CONFIG["electric_field_probe"] = "mock"` sans port série réel.
Co-localisé avec `adapter_electric_field_probe_port.py` (le Real), pas dans un
dossier `mocks/` global — la sonde a un cycle de connexion (connect/disconnect
à la demande) suffisamment particulier pour justifier un double dédié.

## Responsibility

- Implémenter `IElectricFieldProbePort` en mémoire : `connect()` réussit
  instantanément (sauf si `simulate_connection_failure=True`, pour tester le
  chemin d'échec), `acquire_sample()` retourne des valeurs synthétiques.
- Exposer une identité de sonde factice tri-axiale plausible.

## Design

- Pas de threading, pas d'I/O — état interne simple (`_connected: bool`).
- `simulate_connection_failure` en constructeur : bascule de test explicite,
  pas de logique cachée.
