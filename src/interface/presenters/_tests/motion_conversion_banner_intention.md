# motion_conversion_banner_test — Intention

## Rationale

Sans ce test, l'état « banc non calibré » peut redevenir invisible : mouvements refusés sans raison affichée, ou bandeau jamais retiré après la saisie du « Pas par tour ».

## Responsibility

- Les presenters traduisent l'état et les événements de calibration en view model de bandeau.
- Les panneaux désactivent les commandes de déplacement et START, mais pas stop ni arrêt d'urgence, et se réactivent à l'événement de disponibilité.
