---
doc_type: rapport
tldr: "Vague 1 de la dette SolidAI d'ACQ : 3 lots mécaniques faits sur 22, 19 sautés, aucun annulé. solidai verify passe de 1 311 à 1 300 erreurs, tests identiques. Sur ACQ, la plupart des lots dits mécaniques ne le sont pas : il faut corriger le tri avant une vague 2."
---

# Bilan de la vague 1

1. **Erreurs** : 1 311 → 1 300 (−11), 63 avertissements inchangés. `fake-mal-place` 25 → 24, `test-mal-suffixe` 32 → 0, `test-hors-de-tests` 10 → 32.
2. **Lots** : 3 faits (Fake des conditions d'acquisition, 11 tests d'archives, 21 tests d'archives, de `external_modules/` et de `src/_tests/`). 19 sautés, avec un constat chacun. Aucun annulé.
3. **Mécaniques restants** : 21 lots, 445 erreurs, et aucun ne se fait par un geste sûr. Les 2 lots snake_case et un lot `intention-mal-nommee` passent par `arcus_performax_4EX`. Les autres demandent un choix ou changent le code.
4. **Prochaine vague recommandée** : corriger d'abord le tri et les vérifications (variante « cas d'usage sans DTO » de `dto-non-gele` à classer en jugement, `Enum`/`Protocol`/`ABC` à exempter de `valeur-mutable`, `boucle-tdd.sh` qui crie CASSE sur un renommage). Puis le renommage `arcus_performax_4EX` → `arcus_performax_4ex`, testé sur le banc Windows, qui retire jusqu'à 60 erreurs.
5. **Tests** : `pytest src` à 1 707 réussis, 3 sautés et 248 sous-tests après chaque lot, identique à la référence. Aucun test instable n'est apparu.

## Les lots faits

| Lot du tri | Code | Erreurs | Commits |
|---|---|---|---|
| 3 | `solidai-fake-mal-place` (réel en place) | 25 → 24 | `1727b18`, `1dcba1c`, `1df2b47`, `7093eb5` (gate), `73b7327` (imports) |
| 7 | `solidai-test-mal-suffixe` | 32 → 21 | `2627c9f` … `cc75fdc` (11 renommages, gate), `1536294` (imports) |
| 8 | `solidai-test-mal-suffixe` | 21 → 0 | `cb6ee43` … `05e0d6a` (21 renommages, gate), sans import à suivre |

Le gate commite chaque renommage seul.
Un lot compte donc un commit par fichier, plus un commit manuel pour les imports quand il y en a.

**`test-hors-de-tests` monte de 22** (10 → 32), sans code nouveau : les 22 tests d'archives renommés en `*_test.py` sont maintenant reconnus comme des tests, et ils ne sont pas dans un `_tests/`.
Cette dette existait déjà, mais elle était cachée par l'ancien nom.
Elle disparaît d'un coup si `archives/` sort du périmètre de `solidai verify`, une décision qui revient à l'humain.

`boucle-tdd.sh` rend CASSE sur les trois lots, à tort à chaque fois :
- lot 3 : il compte comme nouvelles les erreurs déjà présentes sur le fichier renommé, comme en phase 1 ;
- lots 7 et 8 : `archives/` n'a aucun test que pytest lance ;
- lot 8 : il signale une erreur de collecte de `external_modules/…/_tests/`, alors que `pytest --collect-only` y trouve 10 tests avant comme après le renommage.

## Les lots sautés

- 1, 2 et 5 renomment un chemin d'`arcus_performax_4EX` : `constat-lots-1-2-5-sautes-car-ils-renomment-arcus.md`
- 4 et 6 demandent de choisir une destination : `constat-lots-4-et-6-demandent-de-choisir-une-destination.md`
- 9 à 20 changent le code au-delà d'un renommage : `constat-lots-9-a-20-changent-le-code-au-dela-d-un-renommage.md`
- 21 et 22 sont des faux positifs (`Enum`, `Protocol`, `ABC`) : `constat-lots-21-22-valeur-mutable-sont-des-faux-positifs.md`

## Journaux

- Tri : `run-tri-avant.txt`, `run-tri-apres.txt`
- Tests : `run-pytest-reference.log`, `run-pytest-lot-3.log`, `run-pytest-lot-7.log`, `run-pytest-lot-8.log`
- Verify : `run-verify-<étape>.json` et leurs comptes par code, `run-verify-<étape>-comptes.json`
- Boucle TDD : `run-boucle-tdd-lot-<n>-avant.log`, `run-boucle-tdd-lot-<n>-apres.log`
