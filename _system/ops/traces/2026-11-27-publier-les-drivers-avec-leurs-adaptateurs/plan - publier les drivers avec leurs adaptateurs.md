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
- [x] LIDAR VL53L0X sur ESP32 : paquet `lidar_vl53l0x_esp32` v0.1.0 (repo
  `driver-lidar-vl53l0x-esp32`), banc II migré (FakeClock désormais propre au banc II),
  AEFI sur `feature/drivers-publies` (eb3d6a35, poussée). 516 tests verts, comme avant.
  Reste : essai au banc (canal LIDAR de la sonde inertielle, stabilisation de colonne d'un
  scan), puis fusion dans `develop`.
- [ ] LSM9DS1 — **décision de l'humain.** L'API a divergé, pas seulement les chemins : AEFI a
  renommé les voies (`"acc"` → `"accelerometer"`…) et les constantes (`ACC_FS_G` →
  `ACCELEROMETER_FULL_SCALE_G`, règle 9), retiré `lidar_raw_to_mm`, et rendu port et débit
  obligatoires dans le pilote de flux. Le repo LSM9DS1 a ses propres consommateurs sur les
  anciens noms (services d'analyse IMU, interface terminal, scripts, pont du banc II).
  Question : adopter les noms d'AEFI et migrer ces consommateurs ?
- [ ] Oscilloscope DSO-X 2014A — **décision de l'humain.** AEFI n'a pas de copie du pilote :
  son adaptateur de capture DRDY parle pyvisa directement. Le pilote partagé n'est versionné
  nulle part (ni Desktop ni Dropbox) et le skill global l'importe à plat par `sys.path`.
  Question : créer un repo GitHub `driver-oscilloscope-dsox2014`, en gardant le module racine
  pour le skill ?
- [ ] Narda EP-601 — **décision de l'humain.** Le pilote d'AEFI est un sur-ensemble de celui du
  dossier (journalisation, estimation de la pile) : c'est lui à publier ; l'adaptateur et le
  fake d'AEFI restent (port `IElectricFieldProbePort`). Le repo git de Narda est la copie
  Dropbox, écrite par le Mac, sans remote ; le Desktop n'en a qu'une copie non versionnée.
  Question : pousser ce repo sur GitHub depuis le Mac, puis le cloner ici ?
- [ ] AD9106, ADS131A04 et microcontrôleur : reporté, `mcu_serial_communicator.py` est un
  chemin à éviter de la session « Accélérer la boucle d'acquisition logicielle ». Le dossier
  `AD9106_ADS131A04` n'est pas versionné non plus.
- Hors périmètre : Kapteos et impédancemètre ADS941, sans adaptateur dans AEFI.

## Notes

- Le worktree `AEFI_Acquisition_dev_drivers` a reçu une copie de `.aefi_acquisition/configs/`
  de `AEFI_Acquisition_dev` pour l'essai au banc ; ses `calibrations/` ont été semées par
  l'application (transmission 20,62 µm/impulsion, comme `AEFI_Acquisition_dev`).
- Outil de génération des modules de renvoi : écrit à la volée dans `%TEMP%`, non versionné ;
  la forme d'un module de renvoi est visible dans
  `src/infrastructure/hardware/arcus_performax_4ex/driver_arcus_performax4ex.py`.

## Règles de travail

- AEFI : worktree `AEFI_Acquisition_dev_drivers`, branche `feature/drivers-publies`,
  poussée sur GitHub après chaque instrument. Fusion dans `develop` seulement après l'essai
  au banc par l'humain (règle 10 : code présent n'est pas fonction validée).
- Tests : base mesurée avant chaque changement, puis comparaison. Pas de matériel réel
  sans l'humain.

## Prochaine action

Humain : essai au banc du LIDAR depuis `AEFI_Acquisition_dev_drivers`, puis trancher les trois
questions LSM9DS1, DSO-X 2014A et Narda ci-dessus.
