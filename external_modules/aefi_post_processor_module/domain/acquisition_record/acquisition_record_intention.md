---
type: racine-d-agregat::solidai-ddd
tldr: "Dire pour chaque acquisition de l'export si ses étapes calculées sont à jour : absentes, plus anciennes que le fichier du scan, ou recalcul demandé."
code: ["[[external_modules/aefi_post_processor_module/domain/acquisition_record/acquisition_record.py]]"]
cause_de_changement: regle-metier
repositories:
  - ^: i-acquisition-repository
    type: interface-de-repository::solidai-ddd
    tldr: "list_acquisitions(export_folder) : les acquisitions d'un dossier d'export avec la date de leur fichier de scan et de leur fichier d'étapes."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/domain/acquisition_record/repositories/i_acquisition_repository.py]]"
---
# acquisition_record — Intention

## Rationale

Un traitement qui échoue avant d'avoir rangé sa première étape laisse un fichier d'étapes vide, plus récent que le scan : sans règle pour ce cas, l'acquisition apparaît « traitée » au lancement suivant, alors qu'elle n'a aucune étape. Le lancement du post-traitement décidait seul, dans une boucle de `sync_scans`, quelles acquisitions recalculer : fichier d'étapes absent, plus ancien que le CSV, ou recalcul forcé. Cette règle n'avait pas de nom ni de test, et la fenêtre ne pouvait pas montrer l'état d'une acquisition sans lancer le calcul. Sans elle dans le domaine, chaque appelant la réécrirait avec ses propres dates.

## Responsibility

- Porter une acquisition de l'export : son nom (le dossier), son genre (`stepScan` ou `flyScan`), les chemins de son scan et de son fichier `.h5`, désignés par des chaînes, et les dates du scan et des étapes.
- Décider si ses étapes sont à recalculer, et pourquoi : `new`, `incomplete`, `forced` ou `source_newer`.
- Aucune méthode n'écrit dans l'export : l'agrégat est en lecture seule.

## Design

- Une `@dataclass` ; la règle est `recalculation_reason(forced)`, dans l'ordre : fichier d'étapes absent, fichier d'étapes sans l'étape `preprocessed` (`incomplete`, même plus récent que le scan et même forcé), recalcul forcé, scan aussi récent que les étapes. Le dépôt dit si le fichier contient `preprocessed` (`steps_hold_preprocessed`). Un traitement qui échoue après avoir rangé `preprocessed` laisse des étapes partielles que cette règle ne voit pas : elle ne garde que le cas du fichier vide.
- Le dépôt `IAcquisitionRepository` est un port sortant en lecture : le domaine ne connaît ni dossiers ni dates système.
- Le refus d'une convention de rotation non appliquée (écart 7 de l'avis) attend la tranche 2, qui apporte la convention.
