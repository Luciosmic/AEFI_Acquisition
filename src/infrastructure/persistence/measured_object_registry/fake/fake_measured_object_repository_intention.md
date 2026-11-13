---
type: doublure-de-test::solidai-hexagonal
tldr: "Implémenter IMeasuredObjectRepository en mémoire."
code: ["[[src/infrastructure/persistence/measured_object_registry/fake/fake_measured_object_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/measured_object_registry/measured_object_registry_intention^^i-measured-object-repository]]"]
double_de: "[[src/infrastructure/persistence/measured_object_registry/real_measured_object_repository_intention]]"
---
# fake_measured_object_repository — Intention

## Rationale

Les tests du service et des presenters ne doivent pas écrire dans le vrai
`.aefi_acquisition/`. Un mock vérifierait des appels ; il faut au contraire
vérifier l'état (qui est enregistré) et pouvoir reproduire les échecs du
dépôt réel — sinon le service ne serait jamais testé face à un registre
illisible.

## Responsibility

- Implémenter `IMeasuredObjectRepository` en mémoire.
- Reproduire les modes d'échec du réel : registre illisible (`read_failure`,
  qui bloque aussi l'écriture, comme le réel) et non écrivable (`write_failure`).

## Design

- Aucune latence simulée : le dépôt réel est un petit fichier local lu à la
  demande, rien ne dépend de son temps de réponse.
- Testé contre le contrat : `_tests/fake_measured_object_repository_test.py`.
