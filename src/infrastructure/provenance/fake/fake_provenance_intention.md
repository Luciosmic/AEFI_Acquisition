---
type: doublure-de-test::solidai-hexagonal
tldr: "Le Fake de provenance : rend une provenance donnée, arbre propre ou git absent, pour que les tests ne dépendent pas de l'état du dépôt."
code: ["[[src/infrastructure/provenance/fake/fake_provenance.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/acquisition_parameters/i_software_provenance_port_intention]]"]
double_de: "[[src/infrastructure/provenance/git_software_provenance_reader_intention]]"
---
# fake_provenance — Intention

## Rationale

Le lecteur réel interroge git dans le dépôt : un test applicatif qui en
dépendrait changerait de résultat à chaque commit ou modification locale
(arbre propre ou non), et ne pourrait pas reproduire un git absent.

## Responsibility

- Rendre une provenance donnée : `CLEAN` (défaut) ou `GIT_UNAVAILABLE`
  (même mode d'échec que le réel : champs `None` + `unknown_reason`).

## Design

- Vérification d'état (`reads`).
- Réponse instantanée : aucune régulation ne dépend de la durée de git
  (le réel est borné à 5 s par commande).
