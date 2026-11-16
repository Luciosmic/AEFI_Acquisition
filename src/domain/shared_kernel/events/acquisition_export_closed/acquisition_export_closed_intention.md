---
type: evenement-de-domaine::solidai-ddd
tldr: "Signale qu'une acquisition a fermé son export, à la fin, à l'arrêt ou après un échec : plus rien n'y sera écrit."
code: ["[[src/domain/shared_kernel/events/acquisition_export_closed/acquisition_export_closed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# acquisition_export_closed — Intention

## Rationale

L'ouverture d'un export ne suffit pas : sans la fermeture, celui qui suit les exports ouverts croirait une acquisition toujours en cours après sa fin, et l'application refuserait de se fermer à tort.
La fermeture doit arriver quelle que soit l'issue, fin normale, arrêt par l'opérateur ou échec.

## Responsibility

- Dit qu'un export d'acquisition vient de se fermer, quelle que soit l'issue.
- Porte la sorte d'acquisition et son identifiant, les mêmes que l'`AcquisitionExportOpened` qu'il ferme.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, publié sous le sujet `acquisitionexportclosed`.
- Dans le noyau partagé, comme `AcquisitionExportOpened`.
