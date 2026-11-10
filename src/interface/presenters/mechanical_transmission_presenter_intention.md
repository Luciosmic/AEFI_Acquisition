# mechanical_transmission_presenter — Intention

## Rationale

L'onglet « Transmission » ne doit ni appeler le service ni deviner l'état du banc. Sans présenteur, le widget importerait les DTO de l'application, et rien ne le préviendrait qu'un scan commence (une transmission enregistrée pendant un scan mêlerait deux échelles dans ses positions) ni qu'une entrée vient d'être ajoutée par un autre chemin.

## Responsibility

- Construire le modèle d'affichage de la transmission courante, ou de ce qui manque, à partir des DTO du service, et le publier (`transmission_changed`).
- Se rafraîchir à chaque `mechanicaltransmissioncalibrationentryadded`.
- Relayer l'enregistrement demandé par le panneau vers `record_calibration` ; renvoyer le succès ou le refus du domaine par `status_message`.
- Suivre `scanstarted` / `scancompleted` / `scanfailed` / `scancancelled` (`scan_running_changed`) et refuser l'enregistrement pendant un scan, même si le bouton était resté actif.

## Design

- Ne lit que les DTO et l'interface `IApi…` du service, jamais les types du domaine ; les événements sont écoutés par leur sujet (chaîne).
- L'application en direct du facteur au mouvement n'est pas faite ici : c'est `MotionConversionHandler`, qui écoute le même événement.
