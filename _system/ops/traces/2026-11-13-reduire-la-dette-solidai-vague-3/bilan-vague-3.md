---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: bilan
date: 2026-11-13
---

# Bilan de la vague 3 (suite : rangement, typage du domaine, déplacements)

**Atteint.** `solidai verify` passe de 1 174 à 1 039 erreurs (1 169 à 1 033 hors les 2 dossiers non suivis), mypy reste à 2 943, pytest à 1 709 réussis (0 échec, 3 sautés ; la référence de départ avait 1 échec de délai). 13 lots commités sur 20 permis, 1 lot annulé.

## Les lots

Verify « hors untracked », avant → après.

| Lot | Commit | Verify | Remarque |
| --- | --- | --- | --- |
| L1 erreurs de `ports/` vers `errors/` | annulé | 1 169 → 1 174 | +6 `infrastructure-importe-hors-des-ports`, voir le constat |
| L2 `domain_event` et `i_domain_event_bus` dans leur dossier, test de `DomainEvent` | `e585147` | 1 169 → 1 167 | avertissements 55 → 84 |
| L3 `sys.path` retiré d'un test du domaine | `572c749` | 1 167 → 1 166 | |
| L4 4 tests dans le `_tests/` de `scan_application_service` | `8180d09` | 1 166 → 1 162 | |
| L5 3 intentions de test dans leur docstring, 1 intention orpheline retirée | `7c7563e` | 1 162 → 1 154 | |
| F1 9 racines d'agrégat typées | `d17e8be` | 1 154 → 1 145 | |
| F2 18 événements typés | `45db0fe` | 1 145 → 1 127 | 8 retirés, voir le constat |
| F3 21 objets-valeurs typés | `967902b` | 1 127 → 1 106 | |
| F4 3 entités, 15 erreurs, 4 services de domaine typés | `8cec6c2` | 1 106 → 1 084 | |
| F5 chaînes port, réel, Fake de 2 dépôts | `1129075` | 1 084 → 1 078 | 5 dépôts de calibration retirés |
| D1 docstrings de 10 ports du domaine | `f307313` | 1 078 → 1 068 | |
| D2 docstrings de 24 ports d'application | `1464064` | 1 068 → 1 044 | |
| M1 `events/` : bus et stockage du journal, avec Fake | `6d9e8b7` | 1 044 → 1 040 | |
| M2 `execution/` : 3 adaptateurs et un Fake | `42ae1f6` | 1 040 → 1 037 | +1 `trio-incomplet` révélé |
| M3 4 dossiers d'adaptateur renommés d'après leur module | `700aecc` | 1 037 → 1 033 | |

Contrôles : un cycle complet (pytest, verify, mypy) par lot jusqu'à L5, puis, sur la consigne de la session, un verify et un pytest ciblé par lot, avec un cycle complet en fin de vague (`run-controle-fin-couches.log`).

## Erreurs restantes par famille (verify 1 039)

| Code | Départ | Fin |
| --- | --- | --- |
| `intention-non-typee` | 416 | 338 |
| `test-applicatif-importe-un-reel` | 110 | 110 |
| `trio-incomplet` | 97 | 98 |
| `dto-non-gele` | 74 | 74 |
| `service-depend-hors-de-ses-ports` | 64 | 64 |
| `adaptateur-construit-hors-composition` | 51 | 51 |
| `adaptateur-mal-place` | 57 | 47 |
| `methode-publique-hors-api` | 44 | 44 |
| `port-sortant-sans-fake` | 46 | 44 |
| `fake-mal-place` | 35 | 33 |
| `service-appelle-un-service` | 30 | 30 |
| `infrastructure-importe-hors-des-ports` | 28 | 28 |
| `service-instancie-ses-dependances` | 22 | 22 |
| `service-incomplet` | 15 | 15 |
| `port-sans-docstring` | 42 | 8 |
| `mock-dans-un-test-applicatif` | 7 | 7 |
| `fake-sans-test-de-contrat` | 6 | 6 |
| `intention-mal-nommee` | 9 | 5 |
| `domaine-importe-hors-stdlib` | 4 | 5 |
| `port-sortant-mal-place`, `port-mal-nomme` | 7 | 7 |
| `test-hors-de-tests` | 7 | 3 |
| `domaine-appelle-une-entree-sortie`, `evenement-mal-place` | 3 | 0 |

Détail par lot : `run-tri-fin.txt`. Le +1 de `domaine-importe-hors-stdlib` est le dossier non suivi `electric_field_scan_point_acquired`, qui importe l'ancien chemin de `DomainEvent` ; l'humain y suit l'import en le commitant.

## Écarts à connaître

- **Avertissements `co-changement-entre-couches` : 55 → 89.** Les lots qui suivent des imports dans plusieurs couches (L2 surtout, 139 fichiers) font monter ce compteur, et le commit unique est imposé. Ce ne sont pas des erreurs ; voir `constat-un-deplacement-suivi-de-ses-imports-fait-monter-le-co-changement.md`.
- **Un `verify` lancé juste après une écriture native lit parfois un instantané périmé du moteur** : relancer après une à deux minutes avant de conclure.
- **Docstrings des ports (D1, D2)** : copiées telles quelles de l'intention, donc en français, alors que le reste des docstrings est en anglais ; leur AST est identique hors docstrings (34 fichiers).
- **`tldr` des 70 intentions typées** : première phrase de leur section Responsibility, à relire.

## Constats produits

- `constat-sortir-une-erreur-de-ports-fait-apparaitre-infrastructure-importe-hors-des-ports.md`
- `constat-un-deplacement-suivi-de-ses-imports-fait-monter-le-co-changement.md`
- `constat-un-agregat-a-deux-niveaux-ou-sans-racine-bloque-le-typage-ddd.md`
- `constat-lots-de-rangement-sautes-par-jugement.md`
- `constat-doubles-de-mocks-a-discuter.md` (le lot mocks n'est pas fait)

## Ce qui reste à l'humain

1. `test_bench/calibration` et `detection_devices/**` : remonter en `domain/<agrégat>` ? Débloque environ 60 typages (37 pour la calibration), voir le constat.
2. Frontière A14 : accepter les erreurs que le port déclare, pour refaire le lot L1.
3. `persistence/` : un regroupement permis, ou 16 adaptateurs à remonter ?
4. Les 5 intentions de dossier, le test d'événements de la sonde inertielle, `diagram_friendly_test.py`.
5. Les deux doubles de `mocks/` à discuter.
