# lsm9ds1 — Adaptateur du capteur inertiel LSM9DS1 (via carte série)

## Rationale

Le LSM9DS1 (STMicroelectronics : accéléromètre, gyroscope, magnétomètre) n'est
pas relié au PC directement : il est lu par une carte microcontrôleur au
firmware inconnu (mais encore flashé) qui expose un port série USB et porte
aussi un lidar. Sans module dédié, le protocole ASCII de cette carte (établi
par sondage dans le dossier de travail `Hardware - Drivers/LSM9DS1` de la
thèse) se retrouverait dispersé entre le service applicatif et l'interface.

## Responsibility

- `lsm9ds1_stream_protocol.py` : protocole de flux pur (commandes, ordre des
  champs d'une ligne, découpage, lignes de transitoire), sans I/O.
- `lsm9ds1_conversion.py` : valeurs brutes (entiers 16 bits) vers unités
  physiques (g, °/s, µT, mm), sans I/O.
- `driver_lsm9ds1_stream.py` : liaison série en mode flux continu, lecture
  bloquante, horodatage à la réception.
- `adapter_inertial_sensor_stream_port.py` : implémente
  `IInertialSensorStreamPort` (driver + conversion).
- `lsm9ds1_config_loader.py` : lit `config_templates/lsm9ds1_config.json`
  (port COM, débit, capteurs, cadence), refuse un `schema_version` inconnu.
- `fake/` : double déterministe sans matériel.

## Design

- Conversion séparée du driver : les pleines échelles (gyroscope et
  magnétomètre non vérifiées) se corrigent en un seul endroit.
- Le lidar est sur la même carte et la même liaison série : c'est un fait
  d'**infrastructure**. Le lidar n'est pas un capteur inertiel ; il traverse
  ce module comme canal du même flux, dette visible (voir `ponytail:` dans le
  code et `_system/ops/ponytail-debt.md`).
- Source des faits de protocole : dossier de travail LSM9DS1 de la thèse,
  note `lsm9ds1_protocole-serie-observe-a-et-l.md` et journal du 2026-10-12.
