---
type: doublure-de-test::solidai-hexagonal
tldr: "Implémenter IOperatorRepository en mémoire."
code: ["[[src/infrastructure/persistence/operator_registry/fake/fake_operator_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/operator_registry/operator_registry_intention^^i-operator-repository]]"]
double_de: "[[src/infrastructure/persistence/operator_registry/real_operator_repository_intention]]"
---
# fake_operator_repository — Intention

## Rationale

Les tests du service et des presenters ne doivent pas écrire dans le vrai
`.aefi_acquisition/`. Un mock vérifierait des appels ; il faut au contraire
vérifier l'état (qui est enregistré) et pouvoir reproduire les échecs du
dépôt réel — sinon le service ne serait jamais testé face à un registre
illisible.

## Responsibility

- Implémenter `IOperatorRepository` en mémoire.
- Reproduire les modes d'échec du réel : registre illisible (`read_failure`,
  qui bloque aussi l'écriture, comme le réel) et non écrivable (`write_failure`).

## Design

- Aucune latence simulée : le dépôt réel est un petit fichier local lu à la
  demande, rien ne dépend de son temps de réponse.
- Testé contre le contrat : `_tests/fake_operator_repository_test.py`.
