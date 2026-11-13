---
type: atome::solidai-atome
tldr: "Module `motion_conversion_handler` : `apply_current_transmission()` : appliquer la distance par impulsion de la transmission courante au port de mouvement (première fois ou changement), ou enregistrer ce qui manque."
code: ["[[src/application/test_bench_calibration/motion_control_service/motion_conversion_handler.py]]"]
cause_de_changement: orchestration
---
# motion_conversion_handler — Intention

## Rationale

Sans ce handler, l'application doit choisir au démarrage entre deux mauvais comportements quand la transmission mécanique est incomplète : se fermer (l'opérateur ne peut plus rien saisir) ou démarrer avec une valeur devinée (le banc bouge de façon fausse). Il faut un troisième état, explicite : démarrer, refuser de bouger, dire ce qui manque, et repartir dès que c'est saisi. Et une recalibration (transmission mesurée) doit s'appliquer sans redémarrage (décision du 2026-10-15) : sinon la valeur mesurée resterait inutilisée jusqu'au prochain lancement, sans que rien ne le signale.

## Responsibility

- `apply_current_transmission()` : appliquer la distance par impulsion de la transmission courante au port de mouvement (première fois ou changement), ou enregistrer ce qui manque. Ne lève jamais pour une conversion manquante.
- Publier `MotionConversionFoundMissing` (au changement du manque), `MotionConversionBecameAvailable` (première conversion) et `MotionConversionChanged` (conversion remplacée).
- Se ré-évaluer quand la caractérisation, le montage ou la transmission changent.
- Ne rien appliquer pendant un scan : ses positions mêleraient deux échelles. Ce cas est anormal (tout autre pilote des moteurs est refusé pendant un scan par `ExclusiveControl`, et le scan pendant qu'un autre les tient) : un warning, aucun report ; l'opérateur réenregistre après le scan.
- Exposer l'état courant (`IMotionConversionStatusPort.get_status`).

## Design

- Process manager applicatif (comme `ScanClosureHandler`) : il appelle `IApiMechanicalTransmissionCalibrationService` et `IMotionPort`, jamais un autre service applicatif depuis un service.
- Pourquoi l'application en direct est sûre hors scan : le compteur d'impulsions du contrôleur reste la vérité ; seule sa lecture en mm change d'échelle, ce qui est précisément l'effet voulu d'une calibration. Un déplacement en file est converti à son exécution, donc avec la nouvelle échelle.
- État « scan en cours » suivi par les événements `scanstarted` / `scancompleted` / `scanfailed` / `scancancelled`.
- Aucune valeur par défaut : sans transmission calibrée, le port reste sans conversion et refuse (`_require_conversion`).
- `ponytail:` une transmission qui devient incomplète après avoir été appliquée garde l'ancienne conversion (pas de retrait sur le port).
