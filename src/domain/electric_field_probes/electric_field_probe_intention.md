# electric_field_probe — Intention

## Rationale

Modéliser "une sonde de champ électrique" comme un concept propre, distinct du
contexte `aefi_device` (chaîne AD9106+ADS131A04 à démodulation synchrone).
Une sonde de champ électrique se définit par son identité matérielle
(marque/modèle/numéro de série) et le nombre d'axes qu'elle mesure — elle
parle en V/m, jamais en tension ADC ni en composantes in-phase/quadrature.

## Responsibility

- Porter l'identité de la sonde utilisée (`brand`, `model`, `serial_number`).
- Déclarer le nombre et le nom des axes mesurés (`axis_labels`), pour
  supporter des sondes mono/bi/tri-axiales sans hypothèse figée sur 3 canaux.
- Garantir l'invariant "une mesure a autant de composantes que la sonde a
  d'axes" via `record_measurement`, seul point d'entrée pour produire un
  `FieldMeasurement`.

## Design

- `@dataclass(frozen=True)` — identité de sonde immuable une fois connue
  (obtenue à la connexion, cf. adaptateur infrastructure).
- Aggregate root minimal : pas de sous-entités, pas de machine à états — la
  complexité de cycle de vie (connecté/déconnecté, acquisition en cours) est
  portée par l'application/infrastructure, pas par ce value-like aggregate.
