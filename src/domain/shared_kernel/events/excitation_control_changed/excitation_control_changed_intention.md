---
type: evenement-de-domaine::solidai-ddd
tldr: "Événement `excitation_control_changed` : Signaler que le propriétaire de l'excitation a changé : pris par un pilote (`controller` = son nom lisible, ex."
code: ["[[src/domain/shared_kernel/events/excitation_control_changed/excitation_control_changed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# excitation_control_changed — Intention

## Rationale

Le scan, la calibration automatique du capteur et le panneau Excitation
écrivent tous la même excitation. Sans propriétaire unique, une calibration
lancée pendant un scan change le mode (coupée, X, Y) au milieu des points :
le scan enregistre des mesures sous la mauvaise excitation, sans erreur,
avec des données plausibles. Le verrou seul ne suffit pas : s'il est
invisible, l'opérateur voit ses réglages refusés sans savoir pourquoi (état
caché). Cet événement rend visible qui pilote l'excitation.

## Responsibility

- Signaler que le propriétaire de l'excitation a changé : pris par un
  pilote (`controller` = son nom lisible, ex. « scan »), ou libéré
  (`controller` = `None`, l'excitation redevient réglable à la main).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `controller: Optional[str]` — nom affiché tel quel dans le panneau
  Excitation.
- Publié par `ExcitationConfigurationService.take_control()` /
  `release_control()`, uniquement sur changement effectif.
- Topic : `"excitationcontrolchanged"`.
