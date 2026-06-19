# excitation_parameters — Intention

## Rationale

Value object regroupant tous les paramètres de configuration du générateur d'excitation DDS (AD9106) : fréquence, amplitude, mode, phase. Bundler ces paramètres dans un type immuable évite les appels multi-arguments et garantit la cohérence de la configuration transmise à `IExcitationPort`.

## Responsibility

- Stocker fréquence (Hz), amplitude (V ou DAC value), mode d'excitation, phase.
- Valider les plages valides à la construction.

## Design

- **`@dataclass(frozen=True)`** avec validation dans `__post_init__`.
- Utilisé dans `ExcitationConfigurationService` et `IExcitationPort`.
