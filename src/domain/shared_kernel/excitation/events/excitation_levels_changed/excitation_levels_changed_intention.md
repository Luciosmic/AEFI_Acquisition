# excitation_levels_changed — Intention

## Rationale

Miroir de `excitation_frequency_changed` pour les deux niveaux DDS indépendants
(S1-S2, S3-S4). Séparé de l'event fréquence car les consommateurs diffèrent :
la fréquence intéresse la sonde Narda EP-601 (démodulation), les niveaux
n'intéressent aujourd'hui que le snapshot d'export de scan.

## Responsibility

- Signaler qu'un appel à `ExcitationConfigurationService.set_excitation()` a
  réellement changé au moins un des deux niveaux (comparaison avec les
  anciennes valeurs avant écrasement) — pas publié si seuls le mode ou la
  fréquence changent.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `level_s1_s2_percent: float`, `level_s3_s4_percent: float` — nouveaux niveaux
  appliqués (0-100%).
- Topic de publication : `"excitationlevelschanged"`.
