---
type: port::solidai-hexagonal
tldr: "Port sortant LIDAR (distances horodatées à leur réception), contrat commun publié par le paquet lidar_vl53l0x_esp32 et réexporté ici."
sens: sortant
code: "[[src/application/inertial_probe/lidar_distance/ports/i_lidar_distance_port.py]]"
---
# i_lidar_distance_port — Intention

## Rationale

Le pilote vivait en deux copies, ici et dans le repo LIDAR-VL53L0C-ESP32, qui divergeaient.
Depuis le 2026-11-27, la source unique est le paquet `lidar_vl53l0x_esp32` (github.com/Luciosmic/driver-lidar-vl53l0x-esp32),
dont AEFI dépend par `pyproject.toml` (tag git).

## Responsibility

- Garder le chemin d'import AEFI de `lidar_vl53l0x_esp32.ports.i_lidar_distance_port` : réexporter ses noms, sans code
  propre.

## Design

- Toute correction se fait dans le repo LIDAR-VL53L0C-ESP32, puis AEFI monte le tag dans
  `pyproject.toml`.
- Documentation, tests et intention complète : à côté du module, dans le paquet.
