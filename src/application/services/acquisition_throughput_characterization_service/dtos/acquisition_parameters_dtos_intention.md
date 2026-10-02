# acquisition_parameters_dtos — Intention

## Rationale

Le 2026-10-02, deux balayages de débit n'ont pas pu être remis dans leur
contexte après coup : latence USB du COM10 (16 ms ou 1 ms ?), flux démarré à
la main ou non, voies de référence DDS3/DDS4, position du banc, version du
logiciel — il a fallu tout reconstituer depuis le journal d'événements. Sans
des DTO qui portent ces faits du service jusqu'au port d'export, soit le
service construirait lui-même le document (et changerait à chaque évolution
du format de fichier), soit chaque adaptateur de lecture (catalogue,
registres, registre Windows, git) connaîtrait le format du document.

## Responsibility

- Conditions lues dans le système (`IAcquisitionConditionsPort`) :
  composants montés (`MountedComponentDTO`), réglages ADC et AD9106,
  détection synchrone, montage du capteur et rotation appliquée, liaison
  série hôte ↔ MCU, backends matériels (réel / simulé), position du banc.
- Provenance du code (`SoftwareProvenanceDTO`).
- Fichiers produits (`ExportedFileDTO` : taille, SHA-256).
- Ce que le balayage a fait (`ThroughputActivityDTO`) : identifiant,
  début / fin, issue, requête, condition d'excitation appliquée
  (`ExcitationConditionDTO` : nom, libellé, définition), contrôles tenus,
  `n_avg` et excitation de l'opérateur et leur restauration, origine du
  flux, position du banc au début et à la fin, latence USB.
- `AcquisitionParametersDTO` : le tout, remis au port d'export.

## Design

- `@dataclass(frozen=True)`, primitives, valeurs physiques en SI ou dans
  l'unité du nom (`_mm`, `_ms`, `_percent`), codes registres bruts (`_code`).
- `None` = inconnu ; la raison est portée à côté (`unknown[...]`,
  `*_unknown_reason`) : jamais une omission silencieuse.
- Aucune connaissance d'un format : pas de clé JSON, pas de code d'unité,
  pas de mise en page. C'est l'infrastructure
  (`acquisition_parameters_v1_serializer`) qui les traduit en document 1.0.
