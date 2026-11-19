---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Lots de rangement sautés : ce qui demande un jugement, avec la raison

**Sautés, rien n'est modifié.** Chacun sort des gestes décrits dans les fiches.

| Lot | Raison | Ce qu'il faudrait |
| --- | --- | --- |
| 5 intentions de dossier sans module (`acquisition_parameters` 427 lignes, `inertial_probe`, `motion`, `test_bench`, `presenters`) | la fiche les fait fusionner ou supprimer : c'est du texte écrit par l'humain, à relire | l'humain choisit, par intention, entre fusion dans l'atome principal, type `bounded-context` ou suppression |
| `domain/detection_devices/inertial_probe/_tests/inertial_probe_events_test.py` | un seul test pour 3 événements : le ranger demande de le couper | accord pour couper le fichier en trois tests, un par événement |
| `src/tool/diagram_friendly_test.py` | classe de base utilitaire importée par des dizaines de tests, pas un test | la sortir de `tool/` vers un dossier d'outils de test, ou l'exempter |
| 3 erreurs de `ports/` (`lidar_stream_error`, `motion_conversion_unavailable_error`, `raw_increment_motion_error`) | l'essai a fait apparaître 6 erreurs de A14, voir `constat-sortir-une-erreur-de-ports-fait-apparaitre-infrastructure-importe-hors-des-ports.md` | changer l'outil de A14 d'abord |
| 16 adaptateurs sous `infrastructure/persistence/<x>/` | la règle H16 les ferait remonter chacun dans `infrastructure/<adaptateur>/` : la structure `persistence/` disparaît | décider si `persistence/` reste un regroupement (comme `hardware/`) |
| 2 adaptateurs sans test (`aefi_acquisition_executor`, `thread_pool_task_runner`) de `infrastructure/execution/` | les sortir ferait deux `trio-incomplet` de plus | écrire leur test d'abord |
| Presenters (10) | `presenter` demande `appelle:`, un lien vers un enregistrement de port : les services d'application ne sont pas typés | typer les services d'application et leurs ports d'abord |
| Chaînes port, réel, Fake des ports d'application (13 + 8) et des dépôts `aefi_line`, `aefi_point`, `narda_point`, `scan` | même raison pour les ports ; les 4 dépôts n'ont que leur double en mémoire, un choix de Fake | typer les services d'abord ; choisir si le dépôt en mémoire devient le Fake |
| 8 ports sans intention (`i_api_*`, `i_electric_field_probe_port`, `i_position_increments_port`, `i_post_processing_port`) | pas d'intention où lire Responsibility, Rationale, Design | écrire ces rubriques depuis le code, l'humain relit |

## Une erreur révélée par un lot fait

Le lot de déplacement 2 (`execution/`) a fait passer `src/infrastructure/execution` en `solidai-trio-incomplet` (+1) : ses tests ont suivi leurs adaptateurs, et les deux adaptateurs sans test (ligne ci-dessus) ont perdu le `_tests/` partagé.
Le solde du lot reste de −3 erreurs.
