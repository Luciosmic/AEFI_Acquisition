# frequency_sweep — Intention

## Rationale

L'acquisition en fréquence enchaîne des balayages qu'on soustrait (objet − fond) et qu'on compare dans le temps (référence instrument d'un jour à l'autre). Ces opérations n'ont de sens que si chaque balayage est complet, acquis sur une grille connue, avec le même nombre d'échantillons à chaque fréquence, et si l'on sait ce qu'il caractérise et à quelle hauteur de table. Sans agrégat, ces garanties vivraient dans la boucle du service et un balayage à moitié acquis ressemblerait à un balayage complet.

## Responsibility

- Aggregate root d'un balayage en fréquence : identité `FrequencySweepId`, rôle (`FrequencySweepRole`), grille (`FrequencyGrid`), hauteur de la table (`TableHeight`), nombre N d'échantillons par fréquence (≥ 1).
- `record_frequency_point(f, samples)` : refuse une fréquence hors grille (`FrequencyNotInGridError`), déjà acquise (`FrequencyAlreadyAcquiredError`), ou un nombre d'échantillons différent de N (`FrequencyPointIncompleteError`), sans modifier l'état. Sinon calcule la mesure moyennée, empile `FrequencyPointAcquired` et la retourne.
- Complet quand toutes les fréquences de la grille sont acquises : empile alors `FrequencySweepCompleted`, une seule fois.
- `points` : les fréquences acquises et leur mesure, dans l'ordre de la grille.
- Expose `domain_events` (retourne puis vide la liste, convention `AefiPoint`).

## Design

- Un seul agrégat par balayage, qui contient ses points : un balayage dure quelques minutes et n'a de sens qu'entier. Le découpage « agrégat fin + points forts » du scan (ADR-004) répond à des milliers de points et à la pause en milieu de ligne, inutiles ici.
- Mesures brutes (I et Q en volts, repère du capteur, sans correction de champ primaire) : le fond joue ce rôle.
- Moyenne déléguée à `MeasurementStatisticsService` (même service qu'`AefiPoint`).
- Pas de repository : le balayage vit le temps de son acquisition, son export et ses événements en gardent la trace. Le profil de fond (tranche 4 du plan) dira s'il faut le relire.
- Domaine pur : aucun import infrastructure/application, aucun logger.
