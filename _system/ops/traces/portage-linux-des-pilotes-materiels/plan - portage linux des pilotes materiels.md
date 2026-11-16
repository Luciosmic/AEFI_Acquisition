# Plan — Portage Linux des pilotes matériels

**État :** étape 1 faite le 2026-11-16 ; le convertisseur FTDI de COM5 (bus 6-1) est confié à Linux et vu en `/dev/ttyUSB0`, nom stable `/dev/serial/by-id/usb-FTDI_LC234X_FT421G4I-if00-port0`. Aucun pilote n'est encore testé depuis Linux.
**Prochaine action :** créer l'environnement Python de l'application dans Ubuntu, hors du repo (`UV_PROJECT_ENVIRONMENT=~/.venvs/AEFI_Acquisition_dev uv sync`), puis faire lire la centrale inertielle LSM9DS1 sur `/dev/ttyUSB0` par son pilote.

## Fait

- 2026-11-16 : dans Ubuntu, `uv` 0.13.8 (dans `~/.local/bin`), `usbutils`, `libusb-1.0-0` ; utilisateur `manip` ajouté aux groupes `dialout` et `plugdev`.
- 2026-11-16 : `usbipd bind --busid 6-1` (compte `admin`), puis `usbipd attach --wsl --busid 6-1`. Après un débranchement ou un redémarrage, relancer seulement `usbipd attach --wsl --busid 6-1` depuis Windows.

## Pourquoi

L'application tourne déjà sous Linux, mais la communication avec le matériel n'y a jamais été testée. Une partie des pilotes dépend de bibliothèques Windows. L'humain veut migrer l'application sous Linux avec la suite de tests complète, pilotes matériels compris. WSL sert de banc Linux sur le PC du labo, sans changer de machine.

## Ce qui est en place

- WSL 3.0.5, noyau 6.18.58.1, distribution `Ubuntu-24.04` en version 2, utilisateur Linux `manip`, systemd actif, Python 3.12.3.
- Le repo se voit depuis Ubuntu en `/mnt/c/Users/manip/AEFI_Acquisition_dev`.
- `usbipd-win` 5.3.0, installé depuis l'installateur signé du projet sur GitHub (winget a échoué avec une erreur de source).
- Une première copie d'Ubuntu est installée sous le compte Windows `admin`, par la fenêtre élevée. Elle ne sert pas et peut être retirée par `wsl --unregister Ubuntu-24.04` depuis ce compte.

## Le matériel vu par `usbipd list`

Tout le banc est branché en USB.

| Bus | VID:PID | Appareil | Pilote du repo |
|---|---|---|---|
| 1-5 | 1589:a101 | Performax USB | `arcus_performax_4ex` |
| 1-10 | 0957:1798 | USB Test and Measurement Device (IVI) | `oscilloscope_dsox2014` |
| 6-1 | 0403:6015 | USB Serial Converter (COM5) | `lsm9ds1` d'après sa config |
| 6-4 | 0403:6001 | USB Serial Converter (COM10) | à identifier |

La config de la sonde de champ électrique vise COM8, absent au moment du relevé. Les ports de l'ADS131A04, du microcontrôleur et du LIDAR ESP32 restent à relever.

## Ce qui dépend de Windows

- **Platine Arcus Performax 4EX :** le pilote charge par ctypes `PerformaxCom.dll` et `SiUSBXp.dll` (`src/infrastructure/hardware/arcus_performax_4ex/DLL64/`). C'est le point dur du portage. La platine se présente comme un appareil USB simple (1589:a101), ce qui ouvre la piste d'un accès direct par libusb depuis Linux.
- **Oscilloscope DSO-X 2014A :** `pyvisa.ResourceManager()` sans argument, donc la bibliothèque VISA installée sous Windows. Sous Linux, la piste est `pyvisa-py` avec `pyusb` pour l'USB de mesure.
- **Pilotes série** (`esp32_serial_lidar`, `narda_ep600`, `micro_controller`, `lsm9ds1`, tests de l'ADS131A04) : `pyserial`, portable. Sous Linux, il faut remplacer les noms `COMn` des configs par des chemins `/dev/ttyUSB*` ou `/dev/serial/by-id/*`.

## Étapes

1. Outils dans Ubuntu : `uv`, `usbutils`, `libusb-1.0-0`, droits d'accès USB (groupe `dialout`, règles udev).
2. Un premier appareil série FTDI confié à Linux, vu en `/dev/ttyUSB*`, et ses tests matériels lancés depuis Ubuntu.
3. Les noms de ports dans les configs : choisir comment une config désigne un port sous les deux systèmes.
4. L'oscilloscope par `pyvisa-py`.
5. La platine Arcus sans les bibliothèques Windows.
6. La suite de tests complète, matériel compris, lancée depuis Ubuntu.

## Contraintes

- Un appareil confié à WSL disparaît pour Windows tant qu'il y reste attaché : l'application Windows ne peut pas l'utiliser en même temps.
- `usbipd bind` demande les droits administrateur, une fois par appareil, donc le compte Windows `admin`. `usbipd attach` n'en demande plus ensuite.
- Ne jamais lancer les tests dans `C:\Users\manip\AEFI_Acquisition`, la copie de travail des vrais runs.
- Le repo contient déjà le `.venv/` Windows : sous Ubuntu, `uv` doit utiliser `~/.venvs/AEFI_Acquisition_dev` par `UV_PROJECT_ENVIRONMENT`, sinon il écraserait l'environnement Windows.
- Le repo contient déjà le `.venv/` Windows : sous Ubuntu, `uv` doit utiliser `~/.venvs/AEFI_Acquisition_dev` par `UV_PROJECT_ENVIRONMENT`, sinon il écraserait l'environnement Windows.
