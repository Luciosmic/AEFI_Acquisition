# adapter_mock_hardware_config_provider — Intention

## Rationale

Mock générique de provider de configuration hardware, utilisé dans les tests du `HardwareConfigurationService` pour valider le routing des configurations vers le bon périphérique.

## Responsibility

- Simuler un `IHardwareAdvancedConfigurator` avec un `hardware_id` fixé.
- Enregistrer les appels à `apply_config()` pour les assertions.
- `save_config_as_default()`/`reset_to_default()` : implémentations triviales, présentes
  uniquement pour rester conforme à l'ABC.

## Design

- **`infrastructure/mocks/`**.
- Paramétrable avec n'importe quel `hardware_id` pour simuler plusieurs périphériques dans le même test.
- **Non utilisé actuellement** : aucune classe du code ne l'instancie (vérifié par grep). Gardé
  conforme à l'ABC au cas où il serait réactivé plus tard.
