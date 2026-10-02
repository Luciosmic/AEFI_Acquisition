---
tags: [#domain, #application, #infra]
fa: operator_traceability
atomicity: mono-atomique (N = 1)
status: implémentée (2026-10-02)
---

# FA — Tracer l'opérateur d'une acquisition

## Sources

- **S_user (2026-10-02)** : « Pour l'opérateur, il vaudrait mieux un menu
  déroulant avec Nouvel Opérateur qui ouvre un champ de saisie. Cela va
  permettre qu'un opérateur ne rentre pas 2 fois son nom avec potentiellement
  une coquille. » — puis « il faut faire une chaîne complète avec export dans
  .aefi_acquisition/ » — puis « c'est une fonctionnalité atomique ».
- **S_retroing** : `acquisition-parameters.json` 1.0 a un champ
  `provenance.operator.name`, alimenté depuis commit `a38db85` par un champ
  texte libre (deux saisies = deux orthographes possibles) ; schéma de
  référence : `src/application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`.
- **S_doc** : W3C PROV-O — l'opérateur est un `prov:Agent` (`prov:Person`)
  associé à l'activité d'acquisition (`prov:wasAssociatedWith`) ; un agent est
  identifié, pas seulement nommé.

## Intention

L'opérateur d'un scan ou d'une série temporelle est choisi dans une liste ;
un nouvel opérateur est enregistré une seule fois ; chaque acquisition exporte
**qui** l'a menée, par un identifiant stable et son nom.

**Succès observable**

1. Au lancement d'un scan ou d'une série temporelle, l'opérateur choisit son
   nom dans une liste déroulante (panneaux Scan et Continuous Reading).
2. « Nouvel opérateur… » ouvre une saisie ; le nom apparaît ensuite dans la
   liste des deux panneaux, et à chaque redémarrage (registre persisté dans
   `.aefi_acquisition/`).
3. Saisir un nom déjà enregistré à la casse ou aux espaces près
   (« luis  saluden » face à « Luis Saluden ») **ne crée pas** de second
   opérateur : l'opérateur existant est sélectionné, et l'interface le dit.
4. `acquisition-parameters.json` contient `provenance.operator = {id, name}` ;
   aucun opérateur choisi → `null` + avertissement (inchangé).

## Event storming

| Type | Nom | Couche |
|---|---|---|
| Command | `RegisterOperator(name)` | #domain (exposée par l'application) |
| Domain event | `OperatorRegistered(operator_id, name, registered_at)` | #domain |
| Query | `ListOperators()` | #application |
| Choix (pas une commande domaine) | l'opérateur sélectionné pour l'acquisition, porté par la configuration d'export (`ExportConfigDTO`) | #application |
| Export | `provenance.operator {id, name}` | #infra |

Le choix de l'opérateur pour une acquisition n'est pas un fait métier du
registre : c'est un paramètre de l'acquisition, au même titre que l'objet
mesuré. Il ne modifie aucun aggregate.

## Aggregate et invariants

**Aggregate Root : `OperatorRegistry`** (registre des opérateurs) — entité
`Operator` (identité `operator_id`, `name`, `registered_at`).

| Invariant | Règle |
|---|---|
| I1 — une seule orthographe | jamais deux opérateurs dont les noms sont égaux à la casse et aux espaces près |
| I2 — un opérateur a un nom | jamais de nom vide (après suppression des espaces) |
| I3 — identité stable | `operator_id` ne change jamais ; c'est lui qui est exporté (le nom est dénormalisé à côté, pour que le document reste lisible et autonome) |

**Ordre N = 1** : un seul Aggregate Root. Les acquisitions ne sont pas un
aggregate qui « possède » l'opérateur ; elles en reçoivent une copie
(id + nom) au démarrage.

## Refusals (Domain errors)

| Invariant | Refus | Nommé par la promesse refusée |
|---|---|---|
| I2 | `OperatorNameBlank` | « un opérateur a un nom » |
| I1 | — | pas un refus : enregistrer une orthographe déjà connue **rend l'opérateur existant** (idempotence, aucun événement, un log « déjà enregistré ») — c'est le but de l'intention |

> Décision (S_user, 2026-10-02) : I1 = **rendre l'existant**, l'interface
> affiche « déjà enregistré : <nom> ». Pas de refus `OperatorAlreadyRegistered`.

## Cohérence de contexte

Un seul bounded context : *AEFI Acquisition*. Vocabulaire : **opérateur** =
la personne qui mène une acquisition (PROV Agent). Pas de conflit avec
« controller » (propriétaire exclusif d'une ressource : excitation, flux) —
un opérateur n'est pas un controller.

## Atomicité (irréductibilité)

- Sans le registre, la liste ne peut pas empêcher la seconde orthographe :
  sélection et enregistrement sont inséparables pour l'intention (I1).
- Sans l'export, l'opérateur choisi n'a aucun effet observable : la
  traçabilité est le succès attendu.
- Le registre seul (sans liste) ou la liste seule (sans registre persisté)
  laisseraient un état incohérent (doublons, ou opérateurs perdus au
  redémarrage). → **mono-atomique** : une FA, un aggregate, pas
  d'orchestration multi-aggregates.

## Union d'erreurs des Use Cases

| Use case | Union | Origine |
|---|---|---|
| `register_operator(name)` | `OperatorNameBlank` \| `OperatorRegistryUnavailable` | domain (I2) ; infrastructure traduite au boundary (registre illisible / non écrivable) |
| `list_operators()` | `OperatorRegistryUnavailable` | infrastructure traduite |

Aucune erreur d'infrastructure brute (`OSError`, `JSONDecodeError`) ne sort
du service.

## Projection

- Promise Model : `_system/promise_model/operator_registry.md`.
- code_interface (DDD) :
  - `src/domain/operator_registry/` — `operator_registry.py` (aggregate root),
    `entities/operator/`, `events/operator_registered/`,
    `errors/operator_name_blank_error.py`, `repositories/i_operator_repository.py`
  - `src/application/services/operator_service/` — `i_api_operator_service.py`,
    `operator_service.py`, `operator_service_errors.py`, `dtos/operator_dto.py`
  - `src/infrastructure/persistence/operator_registry/` — `real_operator_repository.py`
    (`.aefi_acquisition/operators/operators.json`), `fake/fake_operator_repository.py`
  - `src/interface/` — `OperatorPresenter`, widget `OperatorSelector`
    (liste + « Nouvel opérateur… »), dans les panneaux Scan et Continuous Reading
  - export : `ExportConfigDTO` → `ScanActivityDTO` → `provenance.operator {id, name}`

## Hors périmètre (noté)

- Corriger ou retirer un opérateur mal orthographié (coquille non détectable
  par I1, ex. « Saluen ») : pas demandé — à ajouter si le cas se présente.
- Opérateur du balayage de débit : même widget possible plus tard ; son
  document signale aujourd'hui l'opérateur manquant.
