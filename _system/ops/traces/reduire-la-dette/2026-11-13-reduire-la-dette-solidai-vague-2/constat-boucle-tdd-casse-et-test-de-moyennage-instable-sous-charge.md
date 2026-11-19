---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 2]]"
doc_type: constat
tldr: "Sur les lots de typage, boucle-tdd rend CASSE pour des raisons antérieures au lot, et un test de moyennage échoue au hasard quand pytest tourne en parallèle de mypy et de verify ; ni l'un ni l'autre ne vient des annotations."
---

# boucle-tdd rend CASSE et un test de moyennage est instable sous charge

**Aucun des deux signaux ne vient des annotations : le verdict de boucle-tdd ne bloque pas un lot de typage, et le test de moyennage se rejoue seul.**

## boucle-tdd

Sur les atomes du lot 2, au dernier commit et sans aucune modification, boucle-tdd rend déjà `CASSE`, pour `collecte` et `aucun-test` (`run-boucle-tdd-lot-2-avant.log`).
Lancé sur ses propres `_tests/`, pytest n'arrive pas à collecter deux fichiers de test que `pytest src` passe sans erreur.

Après l'annotation, le verdict ajoute des causes `verify:<code>`.
L'oracle de boucle-tdd compte comme nouvelle toute erreur de verify sur un fichier modifié, même quand elle existait avant.
Le verify complet, comparé constat par constat, ne montre aucun constat apparu ni disparu.

Le verdict est donc noté dans la trace pour chaque lot, sans décider du lot.
Le verify complet identique fait foi.

Pistes pour solidai-developpement :
- le verdict d'un lot qui n'ajoute que des annotations ne devrait pas compter comme nouvelle une erreur ancienne
- la collecte par atome diffère de celle de `pytest src`

## Test de moyennage

`scan_averaging_integration_test.py` échoue à chaque lot sur une variante différente (`COMB`, puis `RASTER`), avec un écart-type mesuré au-dessus de 1.0.
Son générateur de bruit est fixé (`random.Random(42)`), mais le résultat dépend de l'ordre d'exécution, que la charge change : pytest tourne en même temps que mypy et verify.
Aucun fichier d'un lot ne touche ce test.

Le test échoué se rejoue alors seul, une fois.
Vert, le lot compte comme identique à la référence (`run-pytest-lot-<n>-rejeu.log`).
