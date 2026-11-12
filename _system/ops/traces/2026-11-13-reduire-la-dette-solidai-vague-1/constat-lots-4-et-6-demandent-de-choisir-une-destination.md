---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 1]]"
doc_type: constat
tldr: "Les lots 4 et 6, classés mécaniques, ne le sont pas sur ACQ : leur geste suppose une destination évidente, et 4 intentions sur 5 du lot 4 et la plupart des tests du lot 6 n'en ont pas."
---

# Lots 4 et 6 sautés : la destination du geste est à choisir

**Sautés, sans aucun changement.** Le geste n'est pas mécanique sur ces atomes.

## Lot 4, `solidai-intention-mal-nommee` (5 erreurs)

Le geste « renommer l'intention en `<module>_intention.md` » suppose un module Python dans le dossier.
Quatre dossiers n'en ont aucun : leur intention décrit le dossier lui-même.

| Intention | Contenu du dossier |
|---|---|
| `application/services/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md` | l'intention seule |
| `domain/detection_devices/inertial_probe/inertial_probe_intention.md` | `_tests/`, `events/` |
| `domain/shared_kernel/motion/motion_intention.md` | `events/` |
| `domain/test_bench/test_bench_intention.md` | `calibration/`, `physical_bench_limits/` |

Il faut choisir pour chacune : un type de contexte (`bounded-context`, qui n'a ni code ni test), une fusion dans l'intention d'un module voisin, ou une suppression.
Seule `motion_control_service/_tests/uncalibrated_bench_intention.md` a un module (`uncalibrated_bench_test.py`) et se renomme mécaniquement.

## Lot 6, `solidai-test-hors-de-tests` (10 erreurs)

Le geste « déplacer le test dans le `_tests/` de l'atome qu'il teste » suppose de savoir quel atome il teste.

- `application/_tests/scan_hybrid_architecture_test.py` teste plusieurs services : aucun atome unique.
- `domain/detection_devices/inertial_probe/_tests/inertial_probe_events_test.py` teste trois événements, chacun dans son dossier.
- `archives/tests_e2e/integration/` n'a pas d'atome : déplacer, ou exclure `archives/` de la vérification.
- `scan_application_service/_tests/scan_averaging_integration_tests/` et `…/scan_export_with_post_processing_integration_tests/` : remonter les tests d'un niveau mélange leurs images de résultat avec les autres tests.
- `src/tool/diagram_friendly_test.py` : le seul déplacement sans question.
