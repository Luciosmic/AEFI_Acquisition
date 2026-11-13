# scan_acquisition_parameters_dtos — Intention

## Rationale

Le document de paramètres d'un scan ou d'une série temporelle était construit
dans `ScanExportService` lui-même, sous forme de `dict` déjà mis en page :
chaque évolution du format de fichier forçait à modifier un service
applicatif, et l'export des scans ne partageait rien avec celui du balayage de
débit — deux mises en page d'un même schéma, qui dérivaient. Il faut, comme
pour le balayage, que l'application ne transporte que des faits, et que
l'infrastructure les écrive.

## Responsibility

- Ce que **l'acquisition** a fait : `ScanActivityDTO` (identifiant, type
  `step_scan` / `time_series`, début / fin, issue, contrôle exclusif tenu,
  excitation réglée, procédure du scan `StepScanProcedureDTO`, sonde
  auxiliaire, positions du banc, latence USB, nombre d'enregistrements).
- `ScanAcquisitionParametersDTO` : l'activité, les conditions matérielles et la
  provenance du code (DTO partagés de `application/shared/acquisition_parameters/`),
  remis au port d'export.

## Design

- `@dataclass(frozen=True)`, primitives, unité dans le nom (`_mm`, `_ms`, `_v`,
  `_percent`) ; `None` = inconnu, la raison à côté (`*_unknown_reason`).
- Aucune clé JSON ni code d'unité : c'est
  `infrastructure/persistence/scan_acquisition_parameters_v1_serializer.py`
  qui écrit le document 1.0.
- `files` est rempli par le port au moment d'écrire le document final : c'est
  lui qui connaît les fichiers produits et peut en calculer l'empreinte.
