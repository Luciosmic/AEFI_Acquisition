---
tags: [#domain, #application]
fa: operator_traceability
source: _system/thoughts_interface/fa_operator_traceability.md
---

# Promise Model — Registre des opérateurs

## Agents

| Agent (Promise Theory) | DDD |
|---|---|
| `OperatorRegistry` | Aggregate Root |
| `OperatorService` | Application Service (expose les use cases) |
| `ScanExportService` | consommateur : copie (id, nom) de l'opérateur choisi dans les faits de l'acquisition |

## Promesses

**OperatorRegistry**

- `+expose register(name)` / `-accept register` de `OperatorService`
- `+emit OperatorRegistered(operator_id, name, registered_at)` — seulement
  quand un opérateur est **créé**
- Bodies :
  - B1 — un opérateur, une seule orthographe (égalité à la casse et aux espaces près)
  - B2 — un opérateur a un nom (non vide)
  - B3 — `operator_id` stable
- `-reject OperatorNameBlank` (assessment : B2 cassé)
- Orthographe déjà connue : la promesse tenue est « tu obtiens **l'**opérateur
  de ce nom » → rend l'existant, n'émet rien (idempotence)

**OperatorService** (superagent de la FA)

- `+expose register_operator(name)` → `OperatorDTO` | `OperatorNameBlank` | `OperatorRegistryUnavailable`
- `+expose list_operators()` → `[OperatorDTO]` | `OperatorRegistryUnavailable`
- publie `OperatorRegistered` sur le bus (presenters des deux panneaux :
  la liste se met à jour)

**ScanExportService**

- `-accept` l'opérateur choisi via `ExportConfigDTO` (id + nom)
- `+promise` : `provenance.operator = {id, name}` dans
  `acquisition-parameters.json` ; absent → `null` + avertissement

## Cooperation

« Tracer l'opérateur d'une acquisition » = interface (liste, « Nouvel
opérateur… ») → `OperatorService.register_operator` → `OperatorRegistry` →
`OperatorRegistered` → listes rafraîchies → opérateur choisi → export.

## Assessment (tests)

- B1 : « luis  saluden » après « Luis Saluden » rend le même `operator_id`, aucun événement
- B2 : nom vide → `OperatorNameBlank`
- B3 : `operator_id` relu identique après redémarrage (dépôt réel)
- Export : `provenance.operator.id` = id choisi
