# acquisition_throughput_characterization_service — Intention

## Rationale

Le débit de la chaîne d'acquisition dépend du moyennage MCU `n_avg` de façon
non linéaire : au-delà d'un certain `n_avg`, monter le moyennage ne fait que
ralentir la cadence. La caractérisation qui situait ce coude a été faite à
la main en 2024 et perdue. Sans un use case qui pilote le balayage depuis
l'application, chaque nouvelle mesure demande de fermer l'application, un
script à part et un dépouillement manuel — et le résultat ne rejoint jamais
le catalogue des composants où il doit vivre (grandeur « Débit d'acquisition
optimal vs n_avg » du microcontrôleur).

## Responsibility

- `start_characterization(request)` : valider la grille (au moins 2 `n_avg`
  distincts dans les bornes du MCU, au moins 3 échantillons par point),
  réserver l'excitation, puis lancer le balayage en tâche de fond. Refus
  (grille invalide, excitation pilotée par un scan ou une calibration) :
  `present_throughput_characterization_failed`.
- Balayage, **excitation coupée** (`mute`) : pour chaque `n_avg`, l'appliquer,
  collecter `samples_per_point` échantillons acquis entièrement sous ce
  réglage (règle causale, `application/shared/settled_sample_collection`),
  caractériser le point (domaine), le présenter.
- Fin : ajustement et `n_avg` recommandé (domaine), export brut + résumé,
  pré-remplissage des grandeurs du microcontrôleur (`component_values`).
- Paramètres d'acquisition (activité PROV) : une fois l'excitation coupée,
  rassembler par ses ports tout ce qui influence la mesure — conditions
  matérielles (`IAcquisitionConditionsPort`), provenance du code
  (`ISoftwareProvenancePort`), latence USB du port du MCU
  (`IUsbLatencyTimerPort`), position du banc au début et à la fin — plus ce
  que le balayage fait lui-même (identifiant, début / fin, issue, requête,
  condition d'excitation et sa définition, contrôles tenus, `n_avg` et
  excitation de l'opérateur et leur restauration, origine du flux). Les
  remettre au port d'export en DTO sans format : au démarrage (`running`),
  puis à la fin (`completed` / `failed`, avec les fichiers écrits). Un
  balayage refusé (grille, contrôle pris) ne démarre aucune activité : rien
  n'est écrit.
- Restaurer quoi qu'il arrive : `n_avg` d'origine, excitation de
  l'opérateur, flux d'acquisition (arrêté s'il a été démarré ici),
  propriété de l'excitation.

## Design

- Périodes : écarts d'horodatage entre échantillons gardés successifs. La
  règle causale garantit qu'ils sont consécutifs dans le flux, donc chaque
  écart est un aller-retour complet.
- Propriétaire `"caractérisation débit MCU"` de tout ce dont dépend le
  balayage, pris tout ou rien (`take_all`) et rendu à la fin : l'excitation
  (panneau Excitation verrouillé), le flux d'acquisition (Start/Stop de
  Continuous Reading verrouillés — un Stop manuel avait bloqué un balayage
  le 2026-10-02) et la configuration avancée `mcu` / `ads131a04` (n_avg et
  OSR grisés dans Hardware Advanced Config ; identifiants fournis par le port
  de moyennage). Refusé pendant un scan ou une calibration automatique.
- ponytail: excitation coupée seulement. Les conditions X, Y, circulaire
  (bruit avec signal) viendront comme un paramètre de la requête ; le
  domaine n'en dépend pas.
- Dépendance directe à `ExcitationConfigurationService` (même précédent que
  le scan et la calibration capteur : pas d'événement « contrôle de
  l'excitation demandé »).
- Boutons de banc : `settle_delay_s` (après chaque changement, 0,5 s),
  `sample_timeout_s` (par point, 60 s).
- L'OSR courant est enregistré avec le résultat : la courbe en dépend. Le
  balayer se fait en changeant l'OSR (onglet ADC) puis en relançant.
- Le 2026-10-02, deux balayages n'ont pas pu être remis dans leur contexte
  (latence USB 16 ou 1 ms, flux démarré à la main, voies de référence,
  position, version) : d'où les paramètres d'acquisition. Le service ne
  connaît **aucun format** : le schéma `acquisition-parameters.json` 1.0
  (mise en page, unités UCUM, avertissements) vit dans l'infrastructure
  (`acquisition_parameters_v1_serializer`), sa cause de changement est le
  format de fichier, pas le use case.
- La définition de « coupée » (`EXCITATION_CUT`) est portée par le service :
  c'est lui qui applique la coupure, et elle n'est que le contrat de
  `ExcitationConfigurationService.mute()` (gains DDS1/DDS2 à 0, phases,
  modes, fréquence et DDS3/DDS4 inchangés). ponytail: un value object du
  domaine quand les conditions X, Y, circulaire deviendront un paramètre.
- Le dossier d'export est créé au démarrage (le document `running` y est
  écrit) ; s'il ne peut pas l'être, le balayage continue sans export et
  le résultat reste affiché.
