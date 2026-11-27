# Plan — publier les drivers avec leurs adaptateurs

## But

Chaque instrument du banc devient un paquet Python installable, dans son repo du dossier
`Desktop\THESE-LUIS-EXPERIMENTAL\Hardware - Drivers\`, poussé sur GitHub et tagué.
AEFI_Acquisition et les scripts de caractérisation l'installent au lieu de recopier le pilote.

## Décisions de l'humain (2026-11-27)

- Le paquet porte l'instrument seul : pilote, port en unités physiques, adaptateur réel,
  Fake, tests de contrat. Aucune dépendance à AEFI.
- Ce qui parle le langage d'AEFI (bus d'événements, scan, lifecycle, configurateurs) reste
  dans AEFI et s'appuie sur le paquet.
- AEFI dépend du paquet par une dépendance uv git, figée sur un tag.
- Un repo par instrument.
- Le port publié est le contrat commun : les modules AEFI du pilote, du port et des fakes
  réexportent le paquet. Un port AEFI différent du port de l'instrument garde un adaptateur
  de traduction dans AEFI.
- La copie Dropbox des drivers est abandonnée : tout se fait dans les clones du Desktop.
- Pousser au fur et à mesure.

## Avancement

- [x] Arcus Performax 4EX : paquet `arcus_performax_4ex` v0.1.0, caractérisation migrée,
  AEFI migré et fusionné dans `develop` (b97fa15f). Validé au banc le 2026-11-27.
- [ ] LIDAR VL53L0X sur ESP32 (repo `driver-lidar-vl53l0x-esp32`).
- [ ] LSM9DS1 (repo `driver-lsm9ds1`).
- [ ] Oscilloscope DSO-X 2014A (dossier non versionné ; le skill global l'importe en place).
- [ ] Narda EP-601 (dossier non versionné).
- [ ] AD9106, ADS131A04 et microcontrôleur : reporté, `mcu_serial_communicator.py` est un
  chemin à éviter de la session « Accélérer la boucle d'acquisition logicielle ».

## Règles de travail

- AEFI : worktree `AEFI_Acquisition_dev_drivers`, branche `feature/drivers-publies`,
  poussée sur GitHub après chaque instrument. Fusion dans `develop` seulement après l'essai
  au banc par l'humain (règle 10 : code présent n'est pas fonction validée).
- Tests : base mesurée avant chaque changement, puis comparaison. Pas de matériel réel
  sans l'humain.

## Prochaine action

LIDAR ESP32 : comparer le repo publié et la copie d'AEFI, puis passer le repo en paquet.
