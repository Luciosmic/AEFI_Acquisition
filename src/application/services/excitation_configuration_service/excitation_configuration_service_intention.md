# excitation_configuration_service — Intention

## Rationale

Isoler la configuration du générateur d'excitation DDS (AD9106) de la UI et du domain. La couche applicative traduit les intentions utilisateur (paramètres d'excitation) vers le port outbound `IExcitationPort` sans connaître les détails du protocole SPI/série.

## Responsibility

- `set_excitation(mode, level_s1_s2, level_s3_s4, frequency)` : appliquer via `IExcitationPort`
  et publier `ExcitationFrequencyChanged` si la fréquence a changé. Pas d'event de niveau ici :
  l'écrivain DDS du port publie `DdsChannelConfigChanged` par canal, sur lequel tous les panels
  se synchronisent (l'ancien `ExcitationLevelsChanged`, doublon sans abonné, a été supprimé
  2026-09-25).
- `mute()`/`unmute()` : couper puis restaurer le gain pour la fenêtre baseline d'un scan
  différentiel — ne touche pas `_current_params` ni ne publie d'event (toggle transitoire, pas
  un changement de config utilisateur).
- `is_linked()`/`set_link(linked)` : query/commande pour le lien de gain DDS1/DDS2 partagé
  avec le panel Hardware Advanced Config — `set_link` délègue à `IExcitationPort` (écrivain
  unique pour la persistance), qui publie `ExcitationDdsLinkChanged`.
- Rester synchronisé quand le panel Hardware Advanced Config change directement la fréquence
  ou le gain/phase des canaux 1/2 (`_on_frequency_changed`, `_on_dds_channel_config_changed`,
  `_on_link_changed`, abonnés sur le bus d'events au lieu de poller) — recalcule mode/niveau
  depuis la paire de phases (DDS1, DDS2), retombe sur `ExcitationMode.CUSTOM` si la paire ne
  correspond à aucun mode connu.
- `take_control(controller)` / `release_control(controller)` / `get_controller()` :
  propriétaire unique de l'excitation (emprunt exclusif, à la `&mut` de Rust mais vérifié
  à l'exécution). Le scan la prend pour toute sa durée (différentiel ou non : l'excitation
  est une condition de mesure de chaque point), la calibration automatique du capteur pour
  sa séquence coupée/X/Y. Tant qu'elle est tenue, `set_excitation` (sans le bon
  `controller`) et `set_link` sont refusés par `OperationResult.fail` — sans ça, une
  calibration lancée pendant un scan change l'excitation au milieu des points, sans erreur
  et avec des données plausibles. Publie `ExcitationControlChanged` à chaque prise/libération
  pour que le panel Excitation affiche qui pilote et se verrouille (pas d'état caché).
  Les lectures (`get_current_parameters`) restent libres. ponytail: l'onglet Hardware
  Advanced Config écrit les registres DDS sans passer par ce service — non couvert.

## Design

- **Dépendance unique `IExcitationPort`** : le service ne connaît que le contrat, pas l'implémentation AD9106.
- **Pattern service applicatif thin** : délègue la logique hardware au port, ne contient pas de calculs DDS.
- L'ordre de construction dans `main.py` importe : ce service doit s'abonner au bus d'events
  avant `ExcitationPresenter`, pour que ce dernier lise un `_current_params`/`is_linked()`
  déjà à jour quand son propre handler s'exécute.
