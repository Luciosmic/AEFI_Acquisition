---
type: constat::sh-agent-os
genere_par: "[[tache - preparer acq pour la vague 2]]"
doc_type: constat
---

# Comptes de solidai verify et de mypy avant la vague 2

**Exclure `archives/` retire 26 erreurs, toutes sous `archives/` et toutes du même code ; mypy compte 3 298 erreurs sur `src/`, dont 87 % d'annotations manquantes.**

## solidai verify

Le `.saignore` ignore 112 fichiers.
Les erreurs passent de 1 300 à 1 274 et les avertissements restent à 63.
Un seul code bouge : `solidai-test-hors-de-tests`, de 32 à 6.
Les 26 constats disparus sont tous sous `archives/`, et aucun constat n'apparaît.
Le brief en attendait 22 ; l'écart vient sans doute des renommages de la vague 1.

Les 6 `test-hors-de-tests` qui restent sont dans le code vivant : ils entrent dans la vague 2.

Journaux : `run-verify-avant-saignore.json`, `run-verify-apres-saignore.json`.

## mypy

Configuration posée par la garde (`disallow_untyped_defs`, `mypy_path = "src"`), lancée par `mypy src` à la racine.
Il ne plante plus depuis la correction de l'import `from src.interface…`.

- 3 298 erreurs dans 493 fichiers, sur 901 vérifiés
- `no-untyped-def` : 2 864
- `attr-defined` : 109
- `arg-type` : 87
- `union-attr` : 52
- `assignment` : 36
- `index` : 31
- `import-untyped` : 31
- `import-not-found` : 19
- `return-value` : 16
- `operator` : 13
- `var-annotated` : 12
- les 7 autres codes : 28 en tout

Les 58 `annotation-unchecked` sont des notes, hors de ce compte.

Journal : `run-mypy-src.log`.

## Tests

`pytest src` donne 1 707 réussis et 3 sautés, avant et après la correction de l'import.
Journaux : `run-pytest-reference.log`, `run-pytest-apres-import.log`.
