---
type: evenement-de-domaine::solidai-ddd
tldr: "Signale qu'une acquisition a ouvert son export : ses fichiers sont en cours d'écriture jusqu'à l'export fermé."
code: ["[[src/domain/shared_kernel/events/acquisition_export_opened/acquisition_export_opened.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# acquisition_export_opened — Intention

## Rationale

Une acquisition réelle dure des heures. Si l'application se ferme pendant qu'elle écrit son export, la mesure est perdue ou tronquée.
Plusieurs sortes d'acquisition exportent (scan, lecture continue avec export armé, balayage en fréquence, caractérisation du débit), chacune dans son propre service.
Sans un fait commun, celui qui doit savoir qu'un export est ouvert devrait interroger chacun de ces services, et un service applicatif n'en appelle pas un autre.

## Responsibility

- Dit qu'un export d'acquisition vient de s'ouvrir.
- Porte la sorte d'acquisition, son identifiant et l'objet mesuré (vide quand il n'y en a pas), pour nommer l'acquisition à l'opérateur.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, publié sous le sujet `acquisitionexportopened`.
- Dans le noyau partagé : plusieurs contextes le publient (scan, balayage en fréquence, banc d'essai).
- `acquisition_kind` est une chaîne libre (`step_scan`, `fly_scan`, `time_series`, `frequency_sweep`, `acquisition_throughput`) : chaque producteur nomme sa sorte, le lecteur ne fait que la montrer.
- Fermé par `AcquisitionExportClosed` de même sorte et même identifiant.
