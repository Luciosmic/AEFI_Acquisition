---
type: evenement-de-domaine::solidai-ddd
tldr: "Signaler que le pilote de la configuration avancée d'un matériel (`hardware_id`) a changé : pris (`controller`) ou libéré (`None`)."
code: ["[[src/domain/shared_kernel/events/hardware_configuration_control_changed/hardware_configuration_control_changed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# hardware_configuration_control_changed — Intention

## Rationale

La caractérisation du débit balaye le moyennage MCU `n_avg` et enregistre
l'OSR de l'ADC avec son résultat. Un changement de `n_avg` ou d'OSR depuis
le panneau Hardware Advanced Config pendant le balayage fausse la mesure
sans erreur. Le verrou bloque ces modifications ; cet événement montre dans
le panneau pourquoi les champs sont grisés.

## Responsibility

- Signaler que le pilote de la configuration avancée d'un matériel
  (`hardware_id`) a changé : pris (`controller`) ou libéré (`None`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Un verrou par `hardware_id` : verrouiller le MCU ne bloque pas les moteurs.
- Publié par `HardwareConfigurationService.take_control()` /
  `release_control()`. Topic : `"hardwareconfigurationcontrolchanged"`.
- Testé via `hardware_configuration_service`.
