# i_bar_transmission_calibration_output_port — Intention

## Rationale

La mesure d'un axe dure plusieurs minutes (fly scan de butée à butée, puis deux
dichotomies à l'arrêt) et tourne hors du thread Qt. Sans port de sortie, le panneau
devrait interroger le service en boucle pour savoir où il en est, ou le service
devrait connaître Qt.

## Responsibility

- Annoncer la progression (étape en cours, encadrements), la mesure réussie
  (`AxisBarTransmissionDTO`) ou l'échec (erreur typée).

## Design

- Port sortant, implémenté par le presenter ; appelé depuis la tâche de fond,
  l'implémentation ne fait qu'émettre des signaux.
