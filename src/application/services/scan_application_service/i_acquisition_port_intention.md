# i_acquisition_port — Intention

## Rationale

Définir le contrat outbound que `ScanApplicationService` utilise pour acquérir un échantillon de mesure. Ce port découple le service applicatif du chip ADC concret (ADS131A04) et rend les tests de scan possibles sans hardware.

## Responsibility

- Déclarer `acquire_sample() → VoltageMeasurement` (ou équivalent) comme méthode abstraite.
- Servir de frontière entre la couche Application et l'infrastructure d'acquisition.

## Design

- **Port outbound** (Application → Infrastructure) : placé dans le dossier du service consommateur (`scan_application_service/`).
- **ABC avec `@abstractmethod`** : contrat pur, zéro logique d'implémentation.
- Implémenté par `AdapterIAcquisitionPortADS131A04` (Real) et `AdapterMockIAcquisitionPort` (Fake/Mock).
