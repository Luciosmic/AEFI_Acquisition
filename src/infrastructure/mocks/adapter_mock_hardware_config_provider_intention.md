# adapter_mock_hardware_config_provider — Intention

## Rationale

Mock générique de provider de configuration hardware, utilisé dans les tests du `HardwareConfigurationService` pour valider le routing des configurations vers le bon périphérique.

## Responsibility

- Simuler un `IHardwareAdvancedConfigurator` avec un `hardware_id` fixé.
- Enregistrer les appels à `apply_config()` pour les assertions.

## Design

- **`infrastructure/mocks/`**.
- Paramétrable avec n'importe quel `hardware_id` pour simuler plusieurs périphériques dans le même test.
