# motion_conversion_handler — Intention

## Rationale

Sans ce handler, l'application doit choisir au démarrage entre deux mauvais comportements quand la transmission mécanique est incomplète : se fermer (l'opérateur ne peut plus rien saisir) ou démarrer avec une valeur devinée (le banc bouge de façon fausse). Il faut un troisième état, explicite : démarrer, refuser de bouger, dire ce qui manque, et repartir dès que c'est saisi.

## Responsibility

- `apply_current_transmission()` : appliquer la distance par impulsion de la transmission courante au port de mouvement, ou enregistrer ce qui manque. Ne lève jamais pour une conversion manquante.
- Publier `MotionConversionFoundMissing` (au changement du manque) et `MotionConversionBecameAvailable`.
- Se ré-évaluer quand la caractérisation, le montage ou la transmission changent, **uniquement** tant que la conversion n'est pas appliquée : aucun mouvement n'a pu avoir lieu avant, donc rien n'est réinterprété.
- Exposer l'état courant (`IMotionConversionStatusPort.get_status`).

## Design

- Process manager applicatif (comme `ScanClosureHandler`) : il appelle `IApiMechanicalTransmissionCalibrationService` et `IMotionPort`, jamais un autre service applicatif depuis un service.
- Aucune valeur par défaut : sans transmission calibrée, le port reste sans conversion et refuse (`_require_conversion`).
- `ponytail:` une conversion déjà appliquée n'est pas changée en session ; un changement de transmission demande un redémarrage.
