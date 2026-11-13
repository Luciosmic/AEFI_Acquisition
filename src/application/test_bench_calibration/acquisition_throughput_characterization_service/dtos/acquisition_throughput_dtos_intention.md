---
type: atome::solidai-atome
tldr: "DTO `acquisition_throughput_dtos` : `AcquisitionThroughputRequestDTO` : grille de `n_avg` et échantillons par point (défauts : 1, 2, 4, 8, 16, 32, 64, 96, 127."
code: ["[[src/application/test_bench_calibration/acquisition_throughput_characterization_service/dtos/acquisition_throughput_dtos.py]]"]
cause_de_changement: orchestration
---
# acquisition_throughput_dtos — Intention

## Rationale

Le résultat de la caractérisation traverse trois frontières (presenter,
export CSV, formulaire du catalogue des composants). Sans DTO, les value
objects du domaine fuiraient dans l'interface, contre la règle « pas
d'import domain dans l'UI ».

## Responsibility

- `AcquisitionThroughputRequestDTO` : grille de `n_avg` et échantillons par
  point (défauts : 1, 2, 4, 8, 16, 32, 64, 96, 127 ; 50).
- `AcquisitionThroughputPointDTO` / `AcquisitionThroughputCharacterizationDTO` :
  miroir primitif des VO du domaine, plus le contexte de mesure (OSR,
  excitation, chemin d'export) et `component_values` (grandeurs du
  microcontrôleur, clés du catalogue).
- `AcquisitionThroughputSampleDTO` : un échantillon brut, pour l'export.

## Design

- `@dataclass(frozen=True)`, unités SI ; l'interface convertit (ms, µV).
