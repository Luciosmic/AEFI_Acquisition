# acquisition_parameters_v1_serializer (balayage en fréquence) — Intention

## Rationale

Un fond ou une référence instrument ne se réutilise que si un lecteur, sans le logiciel, retrouve son rôle, sa grille, la hauteur de la table et tout ce qui influençait la mesure. Le contrat du schéma est `application/scan/scan_export_service/acquisition_parameters/acquisition_parameters_intention.md`.

## Responsibility

- Écrire le document `acquisition-parameters.json` (schéma 1.3) d'un balayage en fréquence : provenance (activité `frequency_sweep`, opérateur), absence d'objet par construction, procédure (`procedure.frequency_sweep` : rôle, grille, N, délais, hauteur de table, nombre de fréquences acquises), composants, chaîne de mesure, colonnes des fichiers.
- Signaler : balayage incomplet (ni référence ni fond utilisable), fréquence de l'opérateur non rétablie, plus les avertissements communs.

## Design

- N'ajoute que ce que le balayage fait ; les sections communes viennent de `acquisition_parameters_v1.py` (calque du sérialiseur de la caractérisation du débit).
- La fréquence de l'AD9106 est balayée : `components.signal_generation_chip.settings.frequency` et `measurement_chain.excitation.state.frequency` renvoient à la grille (`derived_from`) au lieu de recopier la fréquence lue au démarrage, qui est celle de l'opérateur.
- La hauteur de la table porte `source: "operator"` : le logiciel ne la mesure pas.
- `feature_of_interest.present: false` : référence et fond se font sans objet.
