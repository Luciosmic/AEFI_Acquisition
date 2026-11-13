---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_adapter_i_acquistion_port_ads131a04` : Implémenter `acquire_sample() → AefiVoltageMeasurement` avec des données synthétiques."
code: ["[[src/infrastructure/hardware/ads131a04/adapter_i_acquistion_port_ads131a04/fake/fake_adapter_i_acquistion_port_ads131a04.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/ports/i_acquisition_port_intention]]"]
double_de: "[[src/infrastructure/hardware/ads131a04/adapter_i_acquistion_port_ads131a04/adapter_i_acquistion_port_ads131a04_intention]]"
---
# fake_adapter_i_acquistion_port_ads131a04 — Intention

## Rationale

Mock de `IAcquisitionPort` pour les tests de scan sans le hardware ADS131A04. Retourne des mesures de tension synthétiques configurables.

## Responsibility

- Implémenter `acquire_sample() → AefiVoltageMeasurement` avec des données synthétiques.
- Permettre la configuration des valeurs retournées (constantes, bruit gaussien, pattern).

## Design

- **`infrastructure/mocks/`** avec préfixe `adapter_mock_`.
- Spy attributes : `sample_count` pour vérifier le nombre d'acquisitions.
