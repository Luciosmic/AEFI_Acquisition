# i_drdy_capture_port — Intention

## Rationale

L'ODR de l'ADC ne se connaît sans hypothèse (fréquence d'horloge, diviseurs
réellement appliqués) que par la broche DRDY, observée à l'oscilloscope. Sans
port, le use case parlerait SCPI et VISA : il changerait à chaque changement
d'instrument, et ne serait testable qu'avec l'oscilloscope branché.

## Responsibility

- `capture_falling_edges(request)` : capturer la voie demandée sur au moins
  `window_s`, rendre les instants des fronts descendants, le pas
  d'échantillonnage, l'identité de l'instrument et la forme d'onde brute.

## Design

- ABC pure, port sortant. Implémentations : `AdapterDrdyCaptureDsox2014`
  (Agilent DSO-X 2014A en VISA), `FakeDrdyCapturePort` (fronts synthétiques
  à `f_MOD / OSR`, OSR lu sur le port d'OSR simulé).
- L'instrument est laissé dans l'état où il a été trouvé.
- Tout échec attendu (pas d'instrument, aucun front, erreur VISA) →
  `OperationResult.fail`.
