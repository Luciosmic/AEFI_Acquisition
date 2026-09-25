# adapter_excitation_configuration_ad9106 — Intention

## Rationale

Adaptateur Real implémentant `IExcitationPort` pour l'AD9106 DDS. Traduit les `ExcitationParameters` domain (mode, level_s1_s2, level_s3_s4, frequency) en commandes de registres AD9106 concrètes (canaux 1/2 uniquement — 3/4 sont la détection synchrone, non touchés ici).

## Responsibility

- Implémenter `IExcitationPort` : `apply_excitation()` (fréquence, gain, phase des canaux 1/2
  selon le mode), `set_gain()` (gain seul, pour le cycle mute/unmute des scans différentiels —
  ne publie pas d'event, c'est un toggle transitoire), `set_link_dds1_dds2()` (persiste et
  publie `ExcitationDdsLinkChanged`).
- Convertir les valeurs domain (%, mode) en valeurs de registres hardware (gain 0-5500, table
  de phases par mode dans `_map_excitation_mode_to_dds`).
- Publier `DdsChannelConfigChanged` (canaux 1/2) après chaque écriture gain/phase, pour que le
  panel Hardware Advanced Config reste synchronisé sans avoir à interroger le hardware.
- `set_link_dds1_dds2(linked)` : fait un read-modify-write de `link_dds1_dds2` dans
  `ad9106_last_config.json` (résolu via `resolve_config`, pas de registre hardware impliqué —
  même nature que MCU `n_avg`) et publie `ExcitationDdsLinkChanged` si la valeur change,
  dédupliqué via `_last_published_link`.

## Design

- Dépend de `AD9106Controller` (partagé avec `AD9106AdvancedConfigurator`, seconde
  implémentation de `apply_config()` sur le même hardware — écrivain distinct, volontaire :
  celui-ci traduit le domaine, `AD9106AdvancedConfigurator` expose le réglage bas niveau).
- Les formules de conversion (gain %, table de phases par mode) sont encapsulées ici.
- `apply_excitation()` diffe contre `AD9106Controller.get_memory_state()` (état partagé), jamais
  contre son propre dernier `ExcitationParameters` : l'autre écrivain réécrit les mêmes registres,
  et un cache local faisait sauter l'écriture de la phase DDS2 au changement de direction. À 0 %
  (OFF), la phase du mode choisi est quand même écrite — la phase *est* la direction.
- `ExcitationDdsLinkChanged` nommé ainsi (pas `DdsLinkChanged` générique) car une notion de
  lien différente est prévue pour DDS3/DDS4 (phase/fréquence, déphasage détection synchrone).
