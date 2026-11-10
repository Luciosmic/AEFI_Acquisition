# mechanical_transmission_panel — Intention

## Rationale

Le facteur µm par incrément convertit chaque position du banc, et il se mesure sur le banc (lidar contre le compte d'impulsions). Sans écran pour le saisir, l'opérateur édite un fichier JSON à la main et relance l'application, sans rien qui lui dise ce qui est appliqué ni que la mesure d'hier est remplacée : une valeur d'essai peut rester en service sans que personne ne le voie.

## Responsibility

- Afficher la transmission en cours (valeur, micro-pas, moteur, driver, date) ou ce qui manque.
- Afficher l'avertissement de courant du driver quand il y en a un.
- Offrir le formulaire d'enregistrement : µm par incrément, micro-pas, courant réglé, courant crête ; le préremplir avec la transmission en cours pour corriger sans tout retaper.
- Émettre `save_requested(microsteps, driver_current_a, driver_peak_current_a, microns_per_pulse)`.
- Désactiver l'enregistrement pendant un scan (`set_scan_running`).

## Design

- Widget sans logique : il ne valide rien. Les invariants (courant crête ≥ courant réglé, valeurs > 0) sont refusés par le domaine, et le refus revient par `set_status_message`.
- Ne connaît que le modèle d'affichage `MechanicalTransmissionViewModel` et des primitives ; aucun import application ni domaine.
- Chaque enregistrement ajoute une entrée datée au registre : l'historique des valeurs essayées reste dans le fichier du banc.
