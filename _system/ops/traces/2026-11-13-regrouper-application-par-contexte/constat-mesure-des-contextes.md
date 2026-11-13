---
type: constat::sh-agent-os
genere_par: "[[tache - regrouper application par contexte]]"
doc_type: constat
date: 2026-11-13
---

# Mesure des contextes de `application/` après le regroupement

**Le noyau `shared` est stable (I = 0, aucun import vers un contexte) ; `test_bench` et `scan` sont instables (I proche de 0,9) ; `detection_devices` et les deux registres sont les contextes les plus séparés.**

Source : `solidai graphe --format json` après les déplacements (`run-graphe-apres.json`), lu par `mesurer_les_contextes.py` (test à la main : `cas_a_la_main_de_la_mesure_des_contextes.py`, vert). Sortie brute : `run-mesure-apres.md`.
Un arc est un couple (module source, module cible) du graphe d'imports de production, sans les tests.
I = sortants / (entrants + sortants) (Martin, *Agile Software Development*, ch. 20).
`I_app` ne compte que les arcs entre dossiers de `application/` ; `I_tout` ajoute les arcs vers `domain/` (sortants) et ceux de `interface/`, `infrastructure/` et `main.py` (entrants).
« services » est ce qui reste de `application/services/` : `aefi_acquisition_service`, l'ambigu du constat d'affectation.

| Contexte | Dossiers | Sortants vers contextes | Sortants vers shared | Entrants depuis contextes | Entrants depuis shared | I_app | Vers domaine | Depuis interface, infra, main | I_tout |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| detection_devices | 4 | test_bench 1 | 0 | scan 3 | 0 | 0.25 | 22 | 38 | 0.36 |
| frequency_sweep | 1 | services 2 | 10 | 0 | 0 | 1.00 | 9 | 12 | 0.64 |
| measured_object_registry | 1 | 0 | 0 | 0 | 0 | n/a | 7 | 5 | 0.58 |
| operator_registry | 1 | 0 | 0 | 0 | 0 | n/a | 7 | 5 | 0.58 |
| scan | 2 | detection_devices 3, services 2, test_bench 2 | 12 | services 2 | 0 | 0.90 | 73 | 35 | 0.71 |
| services | 1 | scan 2 | 1 | frequency_sweep 2, scan 2, test_bench 5 | 0 | 0.25 | 5 | 8 | 0.32 |
| shared | 9 | 0 | 0 | frequency_sweep 10, scan 12, services 1, test_bench 19 | 0 | 0.00 | 32 | 57 | 0.24 |
| test_bench | 10 | services 5 | 19 | detection_devices 1, scan 2 | 0 | 0.89 | 62 | 67 | 0.55 |

## Lecture

1. `shared` : 9 dossiers (les 4 services rangés ici et 5 du noyau d'origine), 0 arc sortant vers un contexte, 42 arcs entrants (`test_bench` 19, `scan` 12, `frequency_sweep` 10, `services` 1). C'est la forme attendue d'un noyau partagé (Evans, DDD ch. 14).
2. `test_bench` (10 dossiers) et `scan` (2) : I_app 0,89 et 0,90. Ils dépendent de `shared` (19 et 12 arcs) et de `aefi_acquisition_service` (5 et 2). `test_bench` n'est importé que par `scan` (2) et `detection_devices` (1), ce que prévoit l'intention du domaine (`test_bench` n'importe que le noyau, les autres l'importent).
3. `detection_devices` : I_app 0,25, un seul arc sortant (vers `test_bench`, par `aefi_signal_processing_service` qui appelle `transformation_service`), 3 arcs entrants depuis `scan`. Avec le domaine, c'est le contexte au couplage applicatif le plus faible parmi ceux qui ont des arcs.
4. `measured_object_registry` et `operator_registry` : aucun arc vers un autre dossier de `application/` ni depuis un autre (I_app indéfini) ; seulement le domaine (7 chacun) et l'interface (5 chacun). Le plus séparés de l'application.
5. `frequency_sweep` : I_app 1,00 (10 arcs vers `shared`, 2 vers `aefi_acquisition_service`), aucun importeur applicatif.
6. `aefi_acquisition_service` (« services ») : importé par `test_bench` (5), `scan` (2) et `frequency_sweep` (2), et il importe `scan` (2) et `shared` (1). Avec les 2 arcs de `scan` vers lui, les deux dossiers s'importent l'un l'autre (pas de cycle entre modules : R11 n'en trouve aucun). C'est l'ambiguïté du constat d'affectation, devenue un arc mesurable : remonter `i_acquisition_port` dans `shared/` le supprimerait (action de l'humain).

## À discuter (non tranché ici)

- Les contextes sans arc applicatif (`measured_object_registry`, `operator_registry`) et `detection_devices` sont les premiers candidats à devenir un module séparé avec une carte de contextes ; la mesure n'en décide pas, elle ne dit que le couplage.
- `I_tout` mêle des couches : un contexte importé surtout par l'interface (les registres) paraît stable même sans aucun usage applicatif.
