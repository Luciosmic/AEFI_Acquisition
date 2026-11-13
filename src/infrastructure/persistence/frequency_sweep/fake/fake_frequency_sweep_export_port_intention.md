---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_frequency_sweep_export_port` : Garder en mémoire chaque ouverture, export et écriture des paramètres."
code: ["[[src/infrastructure/persistence/frequency_sweep/fake/fake_frequency_sweep_export_port.py]]"]
cause_de_changement: outil
implements: ["[[src/application/frequency_sweep/frequency_sweep_service/ports/i_frequency_sweep_export_port_intention]]"]
double_de: "[[src/infrastructure/persistence/frequency_sweep/csv_frequency_sweep_export_port_intention]]"
---
# fake_frequency_sweep_export_port — Intention

## Rationale

Les tests du service doivent vérifier ce qui est exporté (points, échantillons bruts, paramètres à chaque statut) et son comportement quand le disque refuse, sans écrire de fichier.

## Responsibility

- Garder en mémoire chaque ouverture, export et écriture des paramètres.
- `fail=True` : reproduire un dossier qui ne peut être ni créé ni écrit, comme le port réel (échec rendu, jamais levé).

## Design

- Calque `FakeAcquisitionThroughputExportPort`. Pas de qualité de service à simuler : l'export n'est pas une opération qui régule le balayage.
