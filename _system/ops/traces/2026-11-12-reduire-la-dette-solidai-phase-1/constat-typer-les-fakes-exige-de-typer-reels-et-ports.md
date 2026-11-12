---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai phase 1]]"
doc_type: constat
tldr: "Les lots de typage des Fakes (intention-non-typee sous-fake, 26 erreurs, et port-sortant-sans-fake fake-non-type, 20 erreurs) ne sont pas mécaniques sur ACQ : doublure-de-test exige implements vers un port typé et double_de vers un adaptateur typé, et ACQ n'en a aucun. Lots non appliqués."
---

# Typer les Fakes d'ACQ exige d'abord de typer les réels et les ports

**Verdict : bloqués, non appliqués.** Les deux familles de lots de typage des Fakes ne sont pas des gestes « frontmatter du Fake seul » sur ACQ.
Elles dépendent de lots de jugement hors phase 1.

## Ce qui bloque

1. Le type `doublure-de-test::solidai-hexagonal` hérite d'`adaptateur`. Il exige `implements` (au moins un `port`, lien `[[intention^^id]]` vers un enregistrement inline) et `double_de` (un `adaptateur`).
2. ACQ ne compte aucune instance `adaptateur` et aucun enregistrement `port` (`au_instances_of`, le 2026-11-12) : les intentions réelles et les intentions de service ne sont pas typées.
3. `au_validate` d'une intention de Fake typée sans `implements` rend l'erreur moteur `required-field-absent`. Typer les 26 Fakes ajouterait donc au moins 26 erreurs au graphe (référence : 2 erreurs).
4. La brique du geste, `creer-un-atome.sh` rôle `fake`, refuse elle aussi : « <réel>_intention.md ne déclare pas implements (F3) : le Fake n'a aucune promesse à tenir ».

## Ce que le tri annonce à tort

`trier-la-dette.sh` classe ces lots `mecanique` (rangs 2 et 3) d'après `table-des-gestes.tsv`, sans voir leur prérequis.
Sur ACQ, le prérequis est le typage `adaptateur` du réel et l'enregistrement `port` dans l'intention du service consommateur, deux lots `intention-non-typee (hors-fake)`, donc de jugement.

## Proposition

Ordre possible, sur décision de l'humain : pour chaque port sortant qui a un Fake, typer d'abord l'enregistrement `port` dans l'intention de son service et l'intention de son réel en `adaptateur` (avec `implements`), puis seulement le Fake en `doublure-de-test`.
Le tri gagnerait à classer ces lots « bloqués » tant que le réel ne déclare pas `implements`, comme la brique le fait déjà.
