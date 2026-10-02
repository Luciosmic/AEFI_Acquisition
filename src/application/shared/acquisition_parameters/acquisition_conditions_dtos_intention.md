# acquisition_conditions_dtos — Intention

## Rationale

Les conditions matérielles d'une acquisition — composants montés, réglages de
l'ADC et de l'AD9106, détection synchrone, montage du capteur, liaison série,
backends réels ou simulés, version du code — sont les mêmes qu'il s'agisse
d'un scan, d'une série temporelle ou d'un balayage de caractérisation. Nées
dans le service de caractérisation du débit, elles y restaient enfermées :
l'export des scans aurait dû importer les DTO d'un autre service applicatif,
ou les redéfinir — deux définitions d'un même fait, qui divergent au premier
changement.

## Responsibility

- Porter, en primitives et sans aucun format, les faits communs à toute
  acquisition : `MountedComponentDTO`, `AdcSettingsDTO`,
  `SignalGenerationSettingsDTO` (+ `DdsChannelSettingsDTO`),
  `SynchronousDetectionStateDTO`, `SensorDeploymentDTO`, `HostLinkDTO`,
  `AcquisitionConditionsDTO` (le tout), `BenchPositionDTO`,
  `SoftwareProvenanceDTO`, `ExportedFileDTO`.
- Les ports qui les lisent vivent à côté : `IAcquisitionConditionsPort`,
  `ISoftwareProvenancePort`.

## Design

- `@dataclass(frozen=True)`, primitives ; valeurs physiques en SI ou dans
  l'unité du nom (`_mm`, `_hz`, `_percent`), codes registres bruts (`_code`).
- `None` = inconnu, la raison à côté (`unknown[...]`, `unknown_reason`) :
  jamais une omission silencieuse.
- Aucune connaissance du format `acquisition-parameters.json` : c'est
  l'infrastructure (sérialiseur 1.0) qui traduit en document.
- Ce que fait **une** acquisition (procédure, issue, colonnes) reste dans le
  service qui la mène (ex. `ThroughputActivityDTO`).
