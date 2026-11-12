# uncalibrated_transmission_test — Intention

## Rationale

Sans ce test, l'absence de conversion mm/impulsion (transmission mécanique non calibrée) peut de nouveau fermer l'application au démarrage ou saturer les logs de tracebacks — et l'opérateur n'a alors aucun écran où saisir la grandeur manquante.

## Responsibility

- Adaptateur sans conversion : erreur typée pour les commandes en mm, arrêt et préréglages de vitesse (impulsions) toujours disponibles, boucle de surveillance silencieuse (un seul avertissement).
- Cycle de vie : `verify_all()` vrai si le contrôleur répond (position brute en impulsions), échec conservé s'il ne répond pas.
