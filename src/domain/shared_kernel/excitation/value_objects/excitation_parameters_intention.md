# excitation_parameters — Intention

## Rationale

Value object regroupant tous les paramètres de configuration du générateur d'excitation DDS (AD9106) : fréquence, amplitude, mode, phase. Bundler ces paramètres dans un type immuable évite les appels multi-arguments et garantit la cohérence de la configuration transmise à `IExcitationPort`.

## Responsibility

- Stocker fréquence (Hz), mode d'excitation, et les deux niveaux DDS indépendants.
- Valider les plages valides à la construction.

## Design

- **`@dataclass(frozen=True)`**, validation déléguée à `ExcitationLevel.__post_init__`.
- `level_s1_s2` / `level_s3_s4` : deux gains matériels indépendants, jamais un
  seul "level" partagé (voir `adapter_excitation_configuration_ad9106.py`).
  Câblage réel confirmé à l'oscilloscope (2026-07-30) : le générateur DDS2
  alimente S1/S2, le générateur DDS1 alimente S3/S4 — contre-intuitif par
  rapport à la numérotation des channels, voir `SphereId.dds_channel` et la
  note "Correspondance Poupette Sortie DDS" (source de vérité historique).
- Utilisé dans `ExcitationConfigurationService` et `IExcitationPort`.
