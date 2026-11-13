# synchronous_detection_service — Intention

## Rationale

ch1/ch2 (AD9106) portent l'excitation ; ch3/ch4 portent la référence de démodulation de la détection synchrone. Les 4 canaux partagent une horloge interne commune, donc le déphasage résiduel ch3-ch1 (Delta_Phi) ne vient que de l'électronique externe et est stable/calibrable en fonction de la fréquence. Ce service isole la dérivation des phases de sphères, l'enregistrement des points de calibration et l'application de la compensation, de la UI et du domain.

## Responsibility

- `get_sphere_phases()` : dérive les 4 phases de sphères S1-S4 depuis les registres ch1/ch2 via `SphereId.derive_phase`, calcule le Delta_Phi corrigé courant (lookup nearest-neighbor par fréquence) et rapporte l'état de l'enforcement de quadrature ch3/ch4 — tout est projeté dans `SpherePhasesDTO`, seul objet traversant vers l'interface.
- `save_calibration_point()` : lit ch1/ch3, calcule le delta signé (`PhaseAngle.difference_from`), enregistre un `SynchronousDetectionPhaseCalibrationPoint` dans le registre append-only via l'agrégat `Calibration` puis le repository. Garde-fou explicite : si aucune fréquence d'excitation active (`_current_frequency_hz <= 0`, avant tout event `ExcitationFrequencyChanged`), lève un `ValueError` au message clair plutôt que de laisser échapper le `ValueError` interne du VO — pour que le presenter (couche interface, hors scope) puisse l'attraper et afficher un message utilisateur.
- `is_compensation_enabled()` / `set_compensation_enabled(enabled)` : query/commande sur le flag domaine de compensation. Activer applique **immédiatement** la correction sur ch3 (décision produit confirmée) ; désactiver n'écrit aucun registre.
- `_on_frequency_changed` : s'abonne à `EXCITATION_FREQUENCY_CHANGED_TOPIC` (publié par `ExcitationConfigurationService`) pour mettre en cache la fréquence courante et réappliquer la correction si la compensation est active — jamais de polling.
- `_lookup_current_correction()` : nearest-neighbor par fréquence sur tous les points de toutes les entrées de la signature matérielle courante ; à égalité d'écart, l'entrée la plus récemment enregistrée gagne (tie-break confirmé).

## Design

- Dépendances reçues par constructeur : `ISynchronousDetectionHardwarePort`, `ISynchronousDetectionPhaseCalibrationRepository`, `HardwareSignature` (VO déjà résolu, pas de lecture fichier ici), `IDomainEventBus`.
- Reconstruit l'agrégat `Calibration` via `Calibration.reconstitute(...)` — jamais de construction positionnelle directe du dataclass pour la rehydration.
- Topics publiés : `SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC`, `SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC` (convention nom-de-classe-en-minuscules, identique aux topics du domain event correspondant). Topic souscrit : `EXCITATION_FREQUENCY_CHANGED_TOPIC`, importé directement du module `excitation_configuration_service` (pas dupliqué localement) pour éviter toute divergence de valeur.
- **Ordre de construction dans `main.py`** : ce service doit être instancié (donc abonné au bus) avant tout presenter de détection synchrone, même contrainte que `ExcitationConfigurationService`/`ExcitationPresenter`.
- Le registre append-only n'est jamais tenu en mémoire par l'agrégat — le repository fait autorité en lecture (`find_by_hardware_signature`), cohérent avec la doc du domain `Calibration`.
