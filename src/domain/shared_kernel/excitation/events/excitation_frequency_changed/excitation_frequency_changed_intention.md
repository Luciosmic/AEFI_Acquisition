# excitation_frequency_changed — Intention

## Rationale

D'autres canaux (sonde Narda EP-601, calibration fréquentielle) doivent réagir
à un changement de fréquence d'excitation sans que `ExcitationConfigurationService`
ait à connaître leur existence. Placé dans `shared_kernel` (pas dans un
aggregate `excitation/` dédié) car il n'y a pas d'aggregate root côté
excitation aujourd'hui — seulement un value object `ExcitationParameters`.

## Responsibility

- Signaler qu'un appel à `ExcitationConfigurationService.set_excitation()` a
  réellement changé la fréquence (comparaison avec l'ancienne valeur avant
  écrasement) — pas publié si seuls le mode ou le niveau changent.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `frequency_hz: float` — nouvelle fréquence appliquée à l'excitation.
- Topic de publication : `"excitationfrequencychanged"`.
