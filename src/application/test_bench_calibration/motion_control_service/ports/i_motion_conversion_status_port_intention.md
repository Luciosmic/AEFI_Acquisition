---
type: port::solidai-hexagonal
tldr: "Port sortant `i_motion_conversion_status_port` : Déclarer `get_status() → MotionConversionStatusDTO`."
sens: sortant
code: "[[src/application/test_bench_calibration/motion_control_service/ports/i_motion_conversion_status_port.py]]"
---
# i_motion_conversion_status_port — Intention

## Rationale

Sans ce port, `MotionControlService` refuse un mouvement sans pouvoir dire pourquoi, ou appelle le service de calibration de la transmission (un service applicatif n'en appelle pas un autre).

## Responsibility

- Déclarer `get_status() → MotionConversionStatusDTO`.

## Design

- Port de lecture, co-localisé avec le service qui le consomme.
- Implémenté par `MotionConversionHandler`, qui garde l'état courant.
