# Plan — Portage Linux des pilotes matériels

**État :** WSL 2 et Ubuntu 24.04 installés le 2026-11-16 sur le PC du labo, dans le compte Windows `manip` ; `usbipd-win` 5.3.0 installé côté Windows. Rien n'est encore installé dans Ubuntu, aucun appareil n'est confié à Linux, aucun pilote n'est porté.
**Prochaine action :** installer dans Ubuntu `uv` et les outils USB (`usbutils`, `libusb-1.0-0`), puis confier à Linux un premier convertisseur série FTDI par `usbipd bind` et `usbipd attach --wsl`, et vérifier qu'il apparaît en `/dev/ttyUSB*`.

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
