# ad9106_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour l'AD9106 : expose en réglage manuel la
fréquence DDS partagée et le gain/phase/offset des 4 canaux dans le panel Hardware Advanced
Config. C'est aussi l'**écrivain unique** pour ces registres — `MCULifecycleAdapter` délègue
ici au boot (via `nested_channels_to_flat_config()` + `apply_config()`) au lieu de dupliquer une
écriture registre séparée, ce qui évite que panel et hardware réel divergent silencieusement
(bug historique : le panel affichait une valeur, le hardware réel au boot en appliquait une
autre).

## Responsibility

- `get_parameter_specs()` : définir les specs (`frequency_hz`, `link_dds1_dds2`,
  `ch{1-4}_gain/phase/offset`) et les peupler avec l'état **résolu** (default+last, via
  `hardware_config_resolution.resolve_config()`) — pas le default seul, sinon l'affichage ment
  sur ce qui est réellement appliqué.
- `apply_config(config)` : écrire fréquence/gain/phase/offset sur le contrôleur AD9106,
  publier les events de sync (`ExcitationFrequencyChanged`, `DdsChannelConfigChanged` pour les
  canaux 1/2, `ExcitationDdsLinkChanged` si le lien change — chacun dédupliqué contre la
  dernière valeur publiée), puis persister dans `ad9106_last_config.json` en faisant un
  read-modify-write contre l'état résolu (jamais un dict reconstruit avec des `.get(key, 0)` —
  ça zérotait silencieusement tout canal absent du dict reçu, la cause du bug historique).
- Faire respecter le lien DDS1-DDS2 (`_enforce_dds1_dds2_link`) : si actif, un `apply_config`
  qui ne touche qu'un seul de `ch1_gain`/`ch2_gain` (ou les deux avec des valeurs différentes)
  aligne l'autre canal avant toute écriture — empêche la désync avec le panel Excitation
  (partagé via `ExcitationDdsLinkChanged`).
- `nested_channels_to_flat_config()` (staticmethod) : convertit la forme JSON imbriquée
  (`{"channels": {"1": {"gain":..}}}`) vers la forme plate attendue par `apply_config()` —
  c'est ce qui permet à `MCULifecycleAdapter` de réutiliser cet écrivain au boot.
- `reset_to_default()` : pendant de `save_config_as_default()` — relit le default **pur** (pas
  résolu, sinon on ne ferait que réappliquer l'état courant) via
  `nested_channels_to_flat_config()`, puis délègue à `apply_config()` — récupère donc
  gratuitement toute la logique d'écriture, d'enforcement (lien DDS1-DDS2, et toute autre
  contrainte ajoutée depuis à `apply_config()`) et de publication d'events.

## Design

- `hardware_id = "ad9106_dds"`.
- Implémente `IHardwareAdvancedConfigurator`.
- Dépend de `AD9106Controller` (partagé avec `AdapterExcitationConfigurationAD9106`) et
  `IDomainEventBus`.
- Note résiduelle : la protection anti-écrasement pour le lien repose sur le fait que
  `resolve_config()` peuple toujours les 4 canaux depuis le default — un futur appelant qui
  enverrait un dict plat partiel en dehors de ce chemin résolu pourrait réintroduire le bug
  historique localement.
