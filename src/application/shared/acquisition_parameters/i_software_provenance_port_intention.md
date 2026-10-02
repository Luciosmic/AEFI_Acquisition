# i_software_provenance_port — Intention

## Rationale

Le schéma `acquisition-parameters.json` n'exporte pas ce qui est figé dans le
code (mapping voies ADC → axes I/Q, conversion codes → volts) : il renvoie au
commit. Sans identification du code, ces faits sont perdus ; sans le drapeau
`dirty`, un export fait sur un arbre modifié passe pour reproductible alors
qu'il ne l'est pas. Le 2026-10-02, la version du logiciel a dû être
reconstituée à la main.

## Responsibility

- `read()` : nom, version, commit, branche, arbre modifié ou non.

## Design

- ABC pure, port sortant.
- Implémentations : `GitSoftwareProvenanceReader` (git + `pyproject.toml`),
  `FakeSoftwareProvenancePort` (tests).
- Jamais d'exception : git absent ou dépôt illisible → champs `None` et
  `unknown_reason`, que le document déclare en avertissement.
