# adapter_mock_i_acquisition_port — Intention

## Rationale

Mock de `IAcquisitionPort` pour les tests de scan sans le hardware ADS131A04. Retourne des mesures de tension synthétiques configurables.

## Responsibility

- Implémenter `acquire_sample() → VoltageMeasurement` avec des données synthétiques.
- Permettre la configuration des valeurs retournées (constantes, bruit gaussien, pattern).

## Design

- **`infrastructure/mocks/`** avec préfixe `adapter_mock_`.
- Spy attributes : `sample_count` pour vérifier le nombre d'acquisitions.
