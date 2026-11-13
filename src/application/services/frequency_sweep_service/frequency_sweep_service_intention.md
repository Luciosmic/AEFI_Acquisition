# frequency_sweep_service — Intention

## Rationale

L'acquisition en fréquence est la base de la méthode lente et robuste : référence instrument (table basse), fond (table à la hauteur de travail), puis objet. Tant que le balayage se fait à la main (changer la fréquence dans le panneau Excitation, lire, noter), deux balayages ne sont jamais acquis de la même façon, et rien ne garde les conditions qui permettraient de réutiliser un fond. Plan : `_system/ops/traces/acquisition-en-frequence/plan - acquisition en frequence.md`.

## Responsibility

- `start_sweep(request)` : construire le balayage (rôle, grille logarithmique, hauteur de table, N), refuser sans rien démarrer si la demande ne permet pas un balayage comparable (rôle inconnu, hauteur non saisie, N < 3, grille invalide), si l'excitation est éteinte ou en mode personnalisé, ou si l'excitation ou le flux sont tenus par un scan ou une calibration (`present_frequency_sweep_failed`). Sinon réserver l'excitation et le flux, et balayer en tâche de fond.
- Balayage : pour chaque fréquence de la grille, appliquer le mode et les niveaux de l'opérateur à cette fréquence, attendre la stabilisation, collecter N échantillons acquis entièrement à cette fréquence (règle causale, `application/shared/settled_sample_collection`), les faire enregistrer par l'agrégat, publier ses événements, lire le décalage de phase de la référence de détection synchrone appliqué à cette fréquence, présenter le point.
- `stop_sweep()` : arrêter après la fréquence en cours ; le balayage finit `cancelled`, ce qui a été acquis est exporté.
- Fin : exporter la réponse par fréquence et les échantillons bruts (même partiels), écrire les paramètres d'acquisition (`completed`, `cancelled` ou `failed`), présenter le résultat.
- Restaurer quoi qu'il arrive : la fréquence de l'opérateur, le flux d'acquisition (arrêté s'il a été démarré ici), la propriété de l'excitation et du flux.

## Design

- Calque `AcquisitionThroughputCharacterizationService` : `take_all` des contrôles, activité PROV écrite au démarrage puis à la fin, ports de conditions, de provenance et de latence USB, export sans format (le schéma `acquisition-parameters.json` vit dans l'infrastructure).
- Propriétaire `"balayage en fréquence"` de l'excitation (panneau Excitation verrouillé) et du flux (Start/Stop de Continuous Reading verrouillés).
- L'excitation reste celle de l'opérateur : seule la fréquence change. Le mode personnalisé est refusé parce que `set_excitation` réécrit les phases du mode choisi.
- La compensation de phase de la détection synchrone se réapplique à chaque changement de fréquence (`SynchronousDetectionService` écoute `ExcitationFrequencyChanged`) en prenant le point de calibration le plus proche en fréquence ; le décalage effectivement écrit est gardé par fréquence. Le biais d'une calibration lointaine est le même dans le fond et dans l'objet, il s'annule dans la différence.
- Mesures brutes, repère du capteur, sans correction de champ primaire.
- Dépendance directe à `ExcitationConfigurationService` (même précédent que le scan et la caractérisation du débit).
- Boutons de banc : `settle_delay_s` (0,5 s après chaque changement de fréquence), `frequency_timeout_s` (60 s par fréquence).
- Pas de repository : un balayage vit le temps de son acquisition ; son export et ses événements en gardent la trace.
