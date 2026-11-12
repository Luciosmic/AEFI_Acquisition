# frequency_sweep_presenter — Intention

## Rationale

Le panneau de balayage ne doit connaître ni le service ni les DTOs de mesure : il affiche des amplitudes et des phases, et rend des champs saisis. Le présentateur traduit dans les deux sens et reçoit les résultats de la tâche de fond.

## Responsibility

- `refresh_state()` : pré-remplir le panneau avec la demande par défaut et les rôles (source unique : `FrequencySweepRequestDTO`, `ROLE_LABELS`).
- `on_start_requested(paramètres)` / `on_stop_requested()` : transmettre au service.
- Port de sortie : étape en cours, point mesuré (converti en `FrequencyPointViewModel` : amplitude √(I²+Q²) et phase atan2(Q, I) par axe), fin (statut, nombre de fréquences, dossier d'export), échec.

## Design

- Calque `AcquisitionThroughputCharacterizationPresenter` : signaux Qt seulement, sûrs entre threads.
- Amplitude et phase sont une projection d'affichage des moyennes I/Q : l'export garde I et Q, rien n'est perdu.
