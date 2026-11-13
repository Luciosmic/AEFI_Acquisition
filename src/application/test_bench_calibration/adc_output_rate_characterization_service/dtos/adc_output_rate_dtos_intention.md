# adc_output_rate_dtos — Intention

## Rationale

La mesure de l'ODR traverse l'oscilloscope (capture), l'export (fichiers) et
l'interface (tableau, catalogue ADC). Sans DTO, les value objects du domaine
fuiraient dans l'interface, et le port d'oscilloscope dépendrait de types
applicatifs non figés.

## Responsibility

- `AdcOutputRateRequestDTO` : voie de l'oscilloscope branchée sur DRDY,
  rapport de sonde, OSR à mesurer (vide : l'OSR courant seulement, rien n'est
  modifié), nombre de périodes par capture (50).
- `DrdyCaptureRequestDTO` / `DrdyCaptureDTO` : contrat du port oscilloscope —
  fenêtre demandée ; instants des fronts descendants, pas d'échantillonnage,
  identité de l'instrument, forme d'onde brute.
- `AdcOutputRatePointDTO` / `AdcOutputRateCharacterizationDTO` : miroir
  primitif des VO du domaine, plus l'OSR restauré, l'instrument, le chemin
  d'export et `component_values` (grandeurs du catalogue ADC).

## Design

- `@dataclass(frozen=True)`, unités SI ; l'interface convertit.
